"""Dòng lệnh: python -m career_market <lệnh>.

build-dataset   Bước 2: tạo lại datasets/processed/salary_dataset_v2.csv
train           Bước 3: huấn luyện vào thư mục ứng viên, chỉ thay model khi qua cổng
validate        Bước 5: kiểm định mô hình đã lưu (gồm chuẩn production)
reality-check   Đối chiếu mô hình đã lưu với báo cáo lương và hồ sơ vàng
advise          Bước 4: dự đoán + gợi ý kỹ năng cho một hồ sơ
import-batch    Nhập lô tin tuyển dụng từ CSV
"""

import argparse
import json
import sys
from pathlib import Path

from .data.batches import BatchError, import_batch
from .data.dataset import write_dataset
from .data.rules import REGIONS, ROLE_ORDER
from .model.advisor import advise
from .model.promotion import retrain
from .model.reality import reality_check
from .model.training import train
from .model.validation import validate
from .paths import artifacts_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Dự đoán lương CNTT và tư vấn kỹ năng.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build-dataset", help="Gộp ba nguồn thô thành bộ salary-v2 có split")
    commands.add_parser(
        "train",
        help="Huấn luyện lại vào thư mục ứng viên; chỉ thay model đang phục vụ khi qua cổng",
    )
    commands.add_parser("validate", help="Hiệu chuẩn, bootstrap và công bằng của mô hình đã lưu")
    reality = commands.add_parser(
        "reality-check", help="Đối chiếu mô hình đã lưu với báo cáo lương"
    )
    reality.add_argument("--golden-path", help="CSV hồ sơ vàng ẩn danh; mặc định dùng mẫu đóng gói")
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
    args = parser.parse_args()

    if args.command == "build-dataset":
        result = write_dataset()
    elif args.command == "train":
        serving = artifacts_dir()
        result = retrain(
            serving,
            serving.with_name(serving.name + "-candidate"),
            train=lambda output: train(output),
            validate=lambda directory: validate(directory=directory),
            rescore=lambda directory, output: validate(output=output, directory=directory),
        )
    elif args.command == "validate":
        result = validate()
        for difference in result["bootstrap"]["differences"].values():
            difference.pop("samples")  # bỏ 1000 mẫu bootstrap cho gọn khi in
    elif args.command == "reality-check":
        result = reality_check(golden_path=args.golden_path)
    elif args.command == "import-batch":
        try:
            result = import_batch(args.csv, args.source, directory=args.batches_dir)
        except BatchError as error:
            print(str(error), file=sys.stderr)
            return 2
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
