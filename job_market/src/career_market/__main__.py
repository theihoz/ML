"""Local raw preview CLI, sharing the dashboard's business interface."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import MarketError, MarketService
from .company_cli import company_arguments, run_company_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Xem nguồn tin tuyển dụng gốc đã duyệt.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sources", help="Danh mục nguồn và xuất xứ")
    commands.add_parser("training-readiness", help="Kiểm nhãn và policy đã khóa, không fit")
    commands.add_parser("train", help="Fit ngoại tuyến hai model trên cohort đã duyệt")
    commands.add_parser("training-report", help="Nạp lại artifact và kiểm dự đoán, không fit")
    company_arguments(commands.add_parser("companies", help="Đối chiếu công ty và nhóm tin"))
    split = commands.add_parser("split-preview", help="Xem trước ba tập theo nhóm công ty")
    split.add_argument("--basis", choices=["unknown", "gross", "net"], required=True)
    split.add_argument("--scope", required=True)
    split.add_argument(
        "--output", type=Path, help="Lưu báo cáo preview JSON, không phải manifest train"
    )
    prepare = commands.add_parser("prepare", help="Chuẩn hóa và xuất snapshot EDA có manifest")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument(
        "--review-dir", type=Path, help="Ledger đã duyệt có manifest/hash đối chiếu"
    )
    preview = commands.add_parser("preview", help="Kiểm tra và xem raw dạng JSON")
    preview.add_argument("source_id")
    preview.add_argument("--limit", type=int, default=5)
    skills = commands.add_parser("skills", help="Trích ngôn ngữ có bằng chứng (T07)")
    skills.add_argument("--title", required=True)
    skills.add_argument("--description", default="")
    skills.add_argument("--requirements", default="")
    download = commands.add_parser("download", help="Tải revision cố định hoặc kiểm tra cache")
    download.add_argument("source_id")
    download.add_argument("--raw-dir", type=Path)
    download.add_argument("--cache-dir", type=Path)
    download.add_argument(
        "--check-only", action="store_true", help="Chỉ kiểm tra, không tải hoặc ghi"
    )
    predict = commands.add_parser("predict", help="Kiểm tra hồ sơ và trạng thái model")
    for field in ("role", "experience", "skills", "location", "work-mode"):
        predict.add_argument(f"--{field}", default="")
    args = parser.parse_args()
    try:
        service = MarketService(raw_dir=args.raw_dir if args.command == "download" else None)
        if args.command == "sources":
            result = [asdict(source) for source in service.sources()]
        elif args.command == "training-readiness":
            result = service.training_readiness()
        elif args.command == "train":
            result = service.train_models()
        elif args.command == "training-report":
            result = service.audit_training_run()
        elif args.command == "companies":
            result = run_company_report(service, args)
        elif args.command == "split-preview":
            result = service.preview_split(
                service.prepare()["rows"], basis=args.basis, scope=args.scope
            )
            if args.output:
                try:
                    args.output.write_text(
                        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                except OSError as error:
                    raise MarketError(f"Không lưu được preview: {error}") from error
        elif args.command == "prepare":
            result = service.snapshot(output_dir=args.output, review_dir=args.review_dir)[
                "manifest"
            ]
        elif args.command == "predict":
            result = service.predict_profile(
                {
                    field: getattr(args, field)
                    for field in ("role", "experience", "skills", "location", "work_mode")
                }
            )
        elif args.command == "skills":
            result = service.extract_skills(args.title, args.description, args.requirements)
        elif args.command == "download":
            result = service.download_source(
                args.source_id, cache_dir=args.cache_dir, check_only=args.check_only
            )
        else:
            result = asdict(service.preview(args.source_id, args.limit))
    except MarketError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if args.command == "predict" and result["status"] == "invalid_input" else 0


if __name__ == "__main__":
    raise SystemExit(main())
