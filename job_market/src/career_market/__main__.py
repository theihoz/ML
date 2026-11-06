"""Dòng lệnh: python -m career_market <lệnh>.

build-dataset   Bước 2: tạo lại datasets/processed/salary_dataset_v2.csv
train           Bước 3: huấn luyện thành phiên bản mới, chỉ phục vụ khi qua cổng
versions        Liệt kê phiên bản model, đánh dấu bản đang phục vụ
rollback        Quay lại phiên bản đã phục vụ trước đó
validate        Bước 5: kiểm định mô hình đã lưu (gồm chuẩn production)
reality-check   Đối chiếu mô hình đã lưu với báo cáo lương bên ngoài
advise          Bước 4: dự đoán + gợi ý kỹ năng cho một hồ sơ
import-batch    Nhập lô tin tuyển dụng từ CSV
refresh         Nhập lô → dựng dữ liệu → huấn luyện → cổng thay model, một lệnh
"""

import argparse
import json
import sys
from pathlib import Path

from .data.batches import BatchError, import_batch
from .data.dataset import write_dataset
from .data.rules import REGIONS, ROLE_ORDER
from .model.advisor import advise
from .model.reality import reality_check
from .model.training import train
from .model.validation import validate
from .model.versions import list_versions, retrain_version, rollback
from .refresh import refresh


def main() -> int:
    """Đọc lệnh người dùng gõ, chạy bước tương ứng và in kết quả dạng JSON."""
    parser = argparse.ArgumentParser(description="Dự đoán lương CNTT và tư vấn kỹ năng.")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-dataset", help="Gộp nguồn thô và lô thành bộ salary-v2")
    build.add_argument(
        "--single-salary-rule",
        choices=["ratio", "expand30", "point"],
        default="ratio",
        help="Cách suy đầu còn lại của tin chỉ ghi một con số lương (#118)",
    )
    commands.add_parser(
        "train", help="Huấn luyện thành phiên bản mới; chỉ phục vụ khi qua cổng thay model"
    )
    commands.add_parser("versions", help="Liệt kê phiên bản model và bản đang phục vụ")
    commands.add_parser("rollback", help="Quay lại phiên bản đã phục vụ trước đó")
    commands.add_parser("validate", help="Hiệu chuẩn, bootstrap và công bằng của mô hình đã lưu")
    commands.add_parser("reality-check", help="Đối chiếu mô hình đã lưu với báo cáo lương")
    advice = commands.add_parser("advise", help="Dự đoán lương và gợi ý kỹ năng cho hồ sơ")
    advice.add_argument("--role", choices=ROLE_ORDER, required=True)
    advice.add_argument("--region", choices=REGIONS, default="Hà Nội")
    advice.add_argument("--years", type=float, default=0)
    advice.add_argument("--skills", default="", help="Danh sách kỹ năng, phân tách bằng dấu phẩy")
    batch = commands.add_parser("import-batch", help="Nhập lô tin tuyển dụng từ CSV (#105)")
    batch.add_argument("csv", type=Path)
    batch.add_argument("--source", help="Tên nguồn của lô, ghi đè cột source trong file")
    batch.add_argument(
        "--batches-dir", type=Path, help="Thư mục lưu lô (mặc định datasets/batches)"
    )
    fresh = commands.add_parser("refresh", help="Chạy cả chuỗi huấn luyện lại (#109)")
    fresh.add_argument("csv", nargs="*", type=Path, help="Các lô CSV cần nhập trước khi dựng")
    fresh.add_argument("--source", help="Tên nguồn của các lô, ghi đè cột source")
    args = parser.parse_args()

    if args.command == "build-dataset":
        result = write_dataset(single_salary_rule=args.single_salary_rule)
    elif args.command == "train":
        result = retrain_version(
            train=lambda output: train(output),
            validate=lambda directory: validate(directory=directory),
            rescore=lambda directory, output: validate(output=output, directory=directory),
        )
    elif args.command == "versions":
        result = list_versions()
    elif args.command == "rollback":
        try:
            result = rollback()
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 2
    elif args.command == "validate":
        result = validate()
        for difference in result["bootstrap"]["differences"].values():
            difference.pop("samples")  # bỏ 1000 mẫu bootstrap cho gọn khi in
    elif args.command == "reality-check":
        result = reality_check()
    elif args.command == "import-batch":
        try:
            result = import_batch(args.csv, args.source, directory=args.batches_dir)
        except BatchError as error:
            print(str(error), file=sys.stderr)
            return 2
    elif args.command == "refresh":
        result = refresh(
            args.csv,
            args.source,
            build=write_dataset,
            retrain=lambda batches: retrain_version(
                train=lambda output: train(output),
                validate=lambda directory: validate(directory=directory),
                rescore=lambda directory, output: validate(output=output, directory=directory),
                batches=batches,
            ),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "ok" else 1
    else:
        skills = [s.strip() for s in args.skills.split(",") if s.strip()]
        result = advise(
            {
                "role": args.role,
                "region": args.region,
                "experience_years": args.years,
                "skills": skills,
            }
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "import-batch":
        return 1 if result["status"] == "rejected" else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
