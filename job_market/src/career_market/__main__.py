"""Dòng lệnh: python -m career_market <lệnh>.

build-dataset   Bước 2: tạo lại datasets/processed/salary_dataset_v2.csv
train           Bước 3: huấn luyện và lưu mô hình vào artifacts/salary-v2
validate        Bước 5: kiểm định mô hình đã lưu
advise          Bước 4: dự đoán + gợi ý kỹ năng cho một hồ sơ
"""

import argparse
import json

from .data.dataset import write_dataset
from .data.rules import REGIONS, ROLE_ORDER
from .model.advisor import advise
from .model.reality import reality_check
from .model.training import train
from .model.validation import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Dự đoán lương CNTT và tư vấn kỹ năng.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build-dataset", help="Gộp ba nguồn thô thành bộ salary-v2 có split")
    commands.add_parser("train", help="Huấn luyện Ridge/Random Forest/Gradient Boosting")
    commands.add_parser("validate", help="Hiệu chuẩn, bootstrap và công bằng của mô hình đã lưu")
    commands.add_parser("reality-check", help="Đối chiếu mô hình đã lưu với báo cáo lương")
    advice = commands.add_parser("advise", help="Dự đoán lương và gợi ý kỹ năng cho hồ sơ")
    advice.add_argument("--role", choices=ROLE_ORDER, required=True)
    advice.add_argument("--region", choices=REGIONS, default="Hà Nội")
    advice.add_argument("--years", type=float, default=0)
    advice.add_argument("--skills", default="", help="Danh sách kỹ năng, phân tách bằng dấu phẩy")
    args = parser.parse_args()

    if args.command == "build-dataset":
        result = write_dataset()
    elif args.command == "train":
        result = train()
    elif args.command == "reality-check":
        result = reality_check()
    elif args.command == "validate":
        result = validate()
        for difference in result["bootstrap"]["differences"].values():
            difference.pop("samples")  # bỏ 1000 mẫu bootstrap cho gọn khi in
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
