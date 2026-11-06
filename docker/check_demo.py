"""Verify bundled demo data and real inference; never train or download assets."""

import json
import math

import pandas as pd
from career_market import MarketService
from career_market.salary_dataset import dataset_path, load_dataset
from career_market.salary_model import (
    MODEL_LABELS,
    advise,
    artifacts_dir,
    load_skill_value,
    predict_profile,
)


def check_demo():
    # Check before calling loaders: missing files must not trigger automatic training.
    required = [dataset_path(), dataset_path().with_suffix(".json")]
    required += [artifacts_dir() / f"{name}.joblib" for name in MODEL_LABELS]
    required += [
        artifacts_dir() / name
        for name in ("metrics.json", "skill_value.csv", "test_predictions.csv")
    ]
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Thiếu dữ liệu/model demo: {path}. Hãy khôi phục rồi build lại.")

    frame = load_dataset()
    summary = json.loads(dataset_path().with_suffix(".json").read_text(encoding="utf-8"))
    if frame.empty or len(frame) != summary["rows"]:
        raise RuntimeError("Bộ dữ liệu demo trống hoặc không khớp metadata.")
    if load_skill_value().empty or pd.read_csv(artifacts_dir() / "test_predictions.csv").empty:
        raise RuntimeError("Thiếu dữ liệu đánh giá hoặc tư vấn kỹ năng.")

    profile = {
        "role": "Backend Developer",
        "region": "Hà Nội",
        "experience_years": 2,
        "skills": ["Java", "SQL"],
    }
    for name in MODEL_LABELS:
        value = predict_profile(profile, model_name=name)["salary"]
        if not math.isfinite(value) or value <= 0:
            raise RuntimeError(f"Model {name} trả kết quả không hợp lệ: {value}")
    advice = advise(profile)
    if not advice["recommendations"] or not advice["experience_path"]:
        raise RuntimeError("Không tạo được tư vấn kỹ năng/lộ trình kinh nghiệm.")

    service = MarketService()
    if not service.prepare()["rows"]:
        raise RuntimeError("Không đọc được dữ liệu thị trường.")
    for name in ("Ridge", "LinearRegression"):
        result = service.estimate_salary("Data/ML", "HN", model_name=name)
        if result["status"] != "ok" or not result["salary_vnd_month"] > 0:
            raise RuntimeError(f"Model thăm dò {name} không chạy được: {result}")
    print(
        f"Demo OK: {len(frame):,} tin; 4 model salary-v2, 2 model thăm dò; "
        f"{advice['model']} dự đoán {advice['salary']:.2f} triệu VND/tháng; tư vấn sẵn sàng.",
        flush=True,
    )


if __name__ == "__main__":
    check_demo()
