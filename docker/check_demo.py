"""Kiểm tra trước khi demo: đủ dữ liệu + 4 mô hình chạy được. Không huấn luyện, không tải mạng."""

import json
import math

import pandas as pd
from career_market.data.dataset import load_dataset
from career_market.model.advisor import advise, predict_profile
from career_market.model.calibration import load_calibration
from career_market.model.estimators import MODEL_LABELS
from career_market.model.training import load_skill_value
from career_market.paths import artifacts_dir, data_root, dataset_path


def check_demo():
    # Check before calling loaders: missing files must not trigger automatic training.
    required = [dataset_path(), dataset_path().with_suffix(".json")]
    required += [artifacts_dir() / f"{name}.joblib" for name in MODEL_LABELS]
    required += [
        artifacts_dir() / name
        for name in ("metrics.json", "skill_value.csv", "test_predictions.csv", "calibration.json")
    ]
    required.append(data_root() / "reference" / "salary_reference.csv")
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
        load_calibration(name)
        value = predict_profile(profile, model_name=name)["predicted"]
        if not math.isfinite(value) or value <= 0:
            raise RuntimeError(f"Model {name} trả kết quả không hợp lệ: {value}")
    advice = advise(profile)
    if not advice["recommendations"] or not advice["experience_path"]:
        raise RuntimeError("Không tạo được tư vấn kỹ năng/lộ trình kinh nghiệm.")

    print(
        f"Demo OK: {len(frame):,} tin; 4 model salary-v2; "
        f"{advice['model']} dự đoán {advice['salary']:.2f} triệu VND/tháng; tư vấn sẵn sàng.",
        flush=True,
    )


if __name__ == "__main__":
    check_demo()
