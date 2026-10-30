"""Read approved postings and expose shared, source-aware business methods."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

from .locations import location_report, normalize_locations
from .roles import classify_role
from .skills import extract_languages


class MarketError(ValueError):
    """An input problem safe to show in CLI and dashboard."""


@dataclass(frozen=True)
class Source:
    source_id: str
    revision: int
    license: str
    filename: str
    publisher: str
    platform: str
    metadata_url: str
    dataset_url: str
    archive_sha256: str
    raw_sha256: str
    expected_rows: int
    columns: tuple[str, ...]
    id_column: str | None
    url_column: str
    has_job_description: bool
    salary_period_confirmed: bool
    attribution: str
    time_fields: dict[str, str]
    imported_on: str


@dataclass(frozen=True)
class RawRecord:
    source_id: str
    job_id: str | None
    job_url: str
    raw: dict[str, str]


@dataclass(frozen=True)
class RawPreview:
    source: Source
    row_count: int
    columns: tuple[str, ...]
    raw_sha256: str
    records: tuple[RawRecord, ...]


class MarketService:
    """Public application seam; adapters only render its results."""

    def xlsx_sheets(self, content, filename="profiles.xlsx"):
        from .xlsx_profiles import inspect_xlsx

        try:
            return inspect_xlsx(content, filename=filename)
        except ValueError as error:
            raise MarketError(str(error)) from error

    def xlsx_profile_columns(self, content, sheet, filename="profiles.xlsx"):
        from .xlsx_profiles import inspect_xlsx

        try:
            if sheet is None:
                raise ValueError("Cần chọn sheet tường minh trước khi preview.")
            result = inspect_xlsx(content, sheet, filename)
            return {"columns": result["columns"], "row_count": len(result["records"])}
        except ValueError as error:
            raise MarketError(str(error)) from error

    def preview_xlsx_profiles(self, content, mapping, sheet, filename="profiles.xlsx"):
        from .xlsx_profiles import preview_xlsx

        try:
            return preview_xlsx(self, content, mapping, sheet, filename)
        except ValueError as error:
            raise MarketError(str(error)) from error

    def profile_columns(self, content, delimiter=","):
        from .profiles import parse_csv

        try:
            columns, rows = parse_csv(content, delimiter)
            return {"columns": columns, "row_count": len(rows)}
        except ValueError as error:
            raise MarketError(str(error)) from error

    def preview_profiles(self, content, mapping, delimiter=","):
        from .profiles import preview_profiles

        try:
            return preview_profiles(self, content, mapping, delimiter)
        except ValueError as error:
            raise MarketError(str(error)) from error

    def time_coverage(self, rows):
        from .time_coverage import time_coverage

        return time_coverage(rows, self.sources())

    def skill_demand(
        self, rows, role=None, locations=None, work_mode=None, source_ids=None, limit=15
    ):
        from .analysis import skill_demand

        if not isinstance(limit, int) or not 1 <= limit <= 50:
            raise MarketError("Top kỹ năng phải nằm trong 1–50.")
        return skill_demand(rows, role, locations, work_mode, source_ids, limit)

    def prepare_records(self, records):
        from .preparation import prepare_records

        return prepare_records(self, records)

    def prepare(self, source_ids=None, *, review_dir=None):
        sources = self.sources()
        selected = list(source_ids) if source_ids is not None else [s.source_id for s in sources]
        if not selected or len(set(selected)) != len(selected):
            raise MarketError("Chọn ít nhất một nguồn, không lặp source ID.")
        records = []
        for source_id in selected:
            records.extend(self.preview(source_id, limit=None).records)
        result = self.prepare_records(records)
        from dataclasses import asdict

        result["sources"] = [asdict(s) for s in sources if s.source_id in selected]
        from .reviewed_labels import apply_reviewed_labels

        try:
            return apply_reviewed_labels(
                self,
                result,
                review_dir or self.raw_dir.parent / "labels/2026-10-29",
                required=review_dir is not None,
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise MarketError(f"Không nhập được ledger nhãn đã duyệt: {error}") from error

    def snapshot(self, source_ids=None, output_dir=None, *, review_dir=None):
        from .snapshots import snapshot

        try:
            return snapshot(self.prepare(source_ids, review_dir=review_dir), output_dir)
        except OSError as error:
            raise MarketError(f"Không xuất được snapshot: {error}") from error

    # T03: phân loại vai trò, dùng chung cho các adapter.
    def classify_role(self, title: str, description: str = "", requirements: str = "") -> dict:
        """Return role, role_status, role_evidence (field/text), and role_reason."""
        return classify_role(title, description, requirements)

    def __init__(self, raw_dir: Path | None = None):
        package_dir = Path(__file__).resolve().parent
        bundled_raw = package_dir / "datasets/raw"
        self.raw_dir = (
            raw_dir
            if raw_dir is not None
            else (bundled_raw if bundled_raw.is_dir() else package_dir.parents[1] / "datasets/raw")
        )

    # T07: ngôn ngữ có bằng chứng, dùng chung cho CLI và Streamlit.
    def extract_skills(self, title: str, description: str = "", requirements: str = "") -> dict:
        """Return skills, skill_evidence ({skill, field, text}) and skills_reason."""
        return extract_languages(title, description, requirements)

    # T10: experience normalization; independent of other normalization methods.
    def normalize_experience(self, raw) -> dict:
        """Return year bounds, kind, status and reason; see T10 ticket notes."""
        from .experience import normalize_experience

        return normalize_experience(raw)

    def experience_report(
        self, source_id: str, status: str | None = None, kind: str | None = None
    ) -> dict:
        """Raw/clean rows and matching CSV from one approved source; T10 notes define keys."""
        preview = self.preview(source_id, limit=None)
        rows = []
        for record in preview.records:
            raw = record.raw.get("experience", record.raw.get("exp"))
            row = {
                "source_id": record.source_id,
                "job_id": record.job_id,
                "job_url": record.job_url,
                "experience_raw": raw,
                **self.normalize_experience(raw),
            }
            if status is not None and row["experience_status"] != status:
                continue
            if kind is not None and row["experience_kind"] != kind:
                continue
            rows.append(row)
        output = io.StringIO()
        columns = [
            "source_id",
            "job_id",
            "job_url",
            "experience_raw",
            "experience_min",
            "experience_max",
            "experience_kind",
            "experience_status",
            "experience_reason",
        ]
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return {
            "rows": rows,
            "total_count": preview.row_count,
            "filtered_count": len(rows),
            "csv": output.getvalue(),
        }

    # T05: location aliases; shared by CLI callers and the location page.
    def normalize_locations(self, raw: str | None) -> dict:
        """Normalize whole labels; see docs/tdd/T05.md for the dictionary contract."""
        return normalize_locations(raw)

    def select_locations(self, rows, locations=None, work_mode=None):
        from .postings import select_locations

        return select_locations(rows, locations, work_mode)

    def location_report(
        self,
        source_id: str,
        *,
        location: str | None = None,
        status: str | None = None,
        locations=None,
        work_mode=None,
    ) -> dict:
        """Raw–clean table, exact canonical/status filters, and matching CSV (T05)."""
        preview = self.preview(source_id, limit=None)
        canonical_rows = self.prepare_records(preview.records)["rows"]
        return location_report(source_id, canonical_rows, location, status, locations, work_mode)

    def sources(self) -> tuple[Source, ...]:
        catalog = json.loads(Path(__file__).with_name("sources.json").read_text())
        return tuple(Source(**{**item, "columns": tuple(item["columns"])}) for item in catalog)

    # T02: tải revision cố định, dùng chung cho CLI và trang tải nguồn.
    def download_source(
        self,
        source_id: str,
        *,
        cache_dir: Path | None = None,
        timeout: float = 60,
        check_only: bool = False,
    ) -> dict:
        """Return download status, source provenance, hashes, paths and UTC timestamps."""
        from .downloader import download_source

        source = next((item for item in self.sources() if item.source_id == source_id), None)
        if source is None:
            raise MarketError(f"Nguồn không được duyệt: {source_id}")
        return download_source(
            source,
            self.raw_dir,
            cache_dir or self.raw_dir.parent / "archives",
            timeout=timeout,
            check_only=check_only,
        )

    def preview(self, source_id: str, limit: int | None = 5) -> RawPreview:
        """Verify the whole source; limit=None returns every unmodified record."""
        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise MarketError("limit phải là số nguyên không âm hoặc None (tất cả).")
        source = next((source for source in self.sources() if source.source_id == source_id), None)
        if source is None:
            raise MarketError(f"Nguồn không được duyệt: {source_id}")
        try:
            raw = (self.raw_dir / source.filename).read_bytes()
        except OSError as error:
            raise MarketError(f"Không đọc được raw {source.filename}: {error.strerror}") from error
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
            if tuple(reader.fieldnames or ()) != source.columns:
                raise MarketError(f"Schema {source_id}: cần các cột {', '.join(source.columns)}")
            rows = list(reader)
        except (UnicodeError, csv.Error) as error:
            raise MarketError(f"CSV không hợp lệ cho {source_id}: {error}") from error
        if len(rows) != source.expected_rows:
            raise MarketError(f"Số dòng {source_id}: cần {source.expected_rows}, nhận {len(rows)}.")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != source.raw_sha256:
            raise MarketError(f"SHA-256 không khớp cho {source_id}; raw đã thay đổi.")
        return RawPreview(
            source,
            len(rows),
            tuple(reader.fieldnames),
            digest,
            tuple(
                RawRecord(source_id, row.get(source.id_column), row[source.url_column], row)
                for row in rows[:limit]
            ),
        )

    # Salary normalization (T09): only the explicit salary field supplies evidence.
    def normalize_salary(self, raw: str | None) -> dict:
        """Return source amounts, units, classification and optional VND/month target."""
        from .salary import normalize_salary

        return normalize_salary(raw)

    def salary_report(self, source_id: str | None = None) -> dict:
        """Normalize every verified raw row; counts describe rows, not unique IT jobs."""
        from collections import Counter

        source_ids = (
            [source.source_id for source in self.sources()] if source_id is None else [source_id]
        )
        rows = []
        for selected in source_ids:
            for number, record in enumerate(self.preview(selected, limit=None).records, start=1):
                raw = record.raw.get("salary", "")
                rows.append(
                    {
                        "source_id": record.source_id,
                        "source_row": number,
                        "job_id": record.job_id,
                        "job_url": record.job_url,
                        "raw_salary": raw,
                        **self.normalize_salary(raw),
                    }
                )
        return {
            "rows": rows,
            "row_count": len(rows),
            "target_n": sum(row["salary_target_vnd_month"] is not None for row in rows),
            "source_counts": dict(Counter(row["source_id"] for row in rows)),
            "reason_counts": dict(Counter(row["salary_reason"] for row in rows)),
            "status_counts": dict(Counter(row["salary_status"] for row in rows)),
        }

    def salary_exports(self, report: dict) -> dict[str, str]:
        """Return raw/normalized/status/review CSV strings from a salary_report result."""
        from .salary import salary_exports

        return salary_exports(report)
