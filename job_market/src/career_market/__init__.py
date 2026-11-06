"""Dự đoán lương CNTT Việt Nam và tư vấn kỹ năng.

Luồng xử lý (đọc theo thứ tự khi thuyết trình):
    data/rules.py         Bước 1: chuẩn hóa một tin (vai trò, lương, kinh nghiệm, kỹ năng)
    data/dataset.py       Bước 2: gộp 3 nguồn, khử trùng, chia train/valid/test
    model/estimators.py   Bước 3a: đặc trưng + 4 mô hình
    model/training.py     Bước 3b: huấn luyện, chọn mô hình, lưu artifact
    model/advisor.py      Bước 4: dự đoán cho hồ sơ + gợi ý kỹ năng
    model/validation.py   Bước 5: kiểm định (hiệu chuẩn, bootstrap, công bằng)
    ui/                   Biểu đồ, cache và giao diện cho Streamlit
"""
