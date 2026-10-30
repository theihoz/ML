"""CSV profile preview only; no snapshot writes, model loading or training."""

import csv
import hashlib
import io

from .roles import ROLE_PATTERNS
from .snapshots import csv_bytes

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000


def parse_csv(content, delimiter=","):
    if not isinstance(content, bytes) or not content:
        raise ValueError("CSV trống hoặc không phải nội dung byte.")
    if len(content) > MAX_BYTES:
        raise ValueError("CSV vượt giới hạn 5 MiB; không có dòng nào được cắt hoặc xử lý một phần.")
    if delimiter not in {",", ";", "\t"}:
        raise ValueError("Dấu phân cách phải là dấu phẩy, chấm phẩy hoặc tab.")
    try:
        reader = csv.reader(
            io.StringIO(content.decode("utf-8-sig")), delimiter=delimiter, strict=True
        )
        columns = next(reader)
        if (
            not columns
            or any(not name.strip() for name in columns)
            or len(set(columns)) != len(columns)
        ):
            raise ValueError("Tên cột CSV phải có nội dung và không được trùng.")
        rows, previous_line = [], reader.line_num
        for values in reader:
            if len(rows) >= MAX_ROWS:
                raise ValueError("CSV vượt 10.000 dòng; không tự cắt dữ liệu.")
            rows.append((previous_line + 1, values))
            previous_line = reader.line_num
    except (UnicodeError, csv.Error, StopIteration) as error:
        raise ValueError("Không đọc được CSV UTF-8 hợp lệ; chưa tạo kết quả một phần.") from error
    return columns, rows


def preview_profiles(service, content, mapping, delimiter=","):
    columns, records = parse_csv(content, delimiter)
    if not all(mapping.get(key) in columns for key in ("role", "experience")):
        raise ValueError("Cần ghép cột vai trò và kinh nghiệm trước khi preview.")
    if any(column is not None and column not in columns for column in mapping.values()):
        raise ValueError("Mapping chứa tên cột không có trong CSV.")
    rows = []
    for index, (line, values) in enumerate(records, 1):
        raw = dict(zip(columns, values))

        def field(key):
            return raw.get(mapping.get(key), "")

        profile = normalize_profile(service, {key: field(key) for key in mapping})
        errors = list(profile["errors"])
        if len(values) != len(columns):
            errors.append(f"Sai số cột: cần {len(columns)}, nhận {len(values)}.")
        row = {
            **profile,
            "row_id": index,
            "csv_line": line,
            "status": "invalid" if errors else "valid",
            "errors": errors,
            "raw": raw,
            "raw_values": values,
        }
        rows.append(row)
    fields = list(rows[0]) if rows else ["row_id", "status", "errors", "raw"]
    valid = sum(row["status"] == "valid" for row in rows)
    return {
        "columns": columns,
        "row_count": len(rows),
        "valid_count": valid,
        "error_count": len(rows) - valid,
        "rows": rows,
        "csv": csv_bytes(rows, fields),
        "input_sha256": hashlib.sha256(content).hexdigest(),
    }


def normalize_profile(service, profile):
    """One normalization path for a single profile and mapped file rows."""
    if not isinstance(profile, dict):
        return {
            "status": "invalid",
            "errors": ["Hồ sơ phải là một object gồm các trường nhập."],
            "warnings": [],
            "raw": profile,
        }
    raw = dict(profile)
    input_errors = []
    profile = dict(profile)
    for field in ("role", "skills", "location", "work_mode"):
        value = profile.get(field)
        if value is None:
            profile[field] = ""
        elif not isinstance(value, str):
            input_errors.append(f"Trường {field} phải là chuỗi hoặc để trống.")
            profile[field] = ""
    role_raw = profile.get("role", "")
    role = next(
        (name for name in ROLE_PATTERNS if name.casefold() == role_raw.strip().casefold()), None
    )
    role = role or service.classify_role(role_raw)["role"]
    experience = service.normalize_experience(profile.get("experience"))
    locations = service.normalize_locations(profile.get("location"))
    skills = service.extract_skills(profile.get("skills", ""))
    errors, warnings = input_errors, []
    work_mode = profile.get("work_mode", "").strip()
    if work_mode:
        mode = service.normalize_locations(work_mode)
        if mode["work_modes"] and not mode["locations"] and not mode["location_unresolved"]:
            locations["work_modes"] = list(
                dict.fromkeys(locations["work_modes"] + mode["work_modes"])
            )
        else:
            errors.append("Hình thức làm việc chưa khớp nhãn Remote; có thể để trống khi chưa rõ.")
    if role is None:
        errors.append("Vai trò chưa khớp rõ một trong bảy nhóm nghề.")
    if experience["experience_status"] != "ok":
        errors.append("Kinh nghiệm thiếu hoặc không hợp lệ; không tự gán 0 năm.")
    if locations["location_status"] != "normalized":
        warnings.append(locations["location_reason"])
    if not skills["skills"]:
        warnings.append("Chưa trích được kỹ năng trong danh mục; giữ nguyên chuỗi nhập để rà soát.")
    return {
        "status": "invalid" if errors else "valid",
        "role": role,
        **experience,
        **locations,
        "skills": skills["skills"],
        "skill_evidence": [
            {**entry, "field": "skills_input"} for entry in skills["skill_evidence"]
        ],
        "errors": errors,
        "warnings": warnings,
        "raw": raw,
    }
