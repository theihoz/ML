"""Đường dẫn dữ liệu và mô hình — mọi module lấy đường dẫn từ đây."""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def data_root():
    """Thư mục datasets/ (bản cài đặt dùng bản đóng gói kèm, bản dev dùng job_market/datasets)."""
    bundled = PACKAGE / "datasets"
    return bundled if bundled.is_dir() else PACKAGE.parents[1] / "datasets"


def dataset_path():
    """File CSV salary-v2 đã làm sạch (kèm file .json tóm tắt cùng tên)."""
    return data_root() / "processed" / "salary_dataset_v2.csv"


def artifacts_dir():
    """Thư mục chứa mô hình .joblib, metrics.json, validation.json."""
    return data_root().parent / "artifacts" / "salary-v2"
