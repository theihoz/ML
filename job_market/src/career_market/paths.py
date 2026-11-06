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


FIRST_VERSION = "salary-v2"


def artifacts_root():
    """Thư mục artifacts/: mỗi thư mục con là một phiên bản model (#108)."""
    return data_root().parent / "artifacts"


def current_version(root=None):
    """Tên phiên bản đang phục vụ, đọc từ con trỏ artifacts/CURRENT (mặc định salary-v2)."""
    pointer = Path(root or artifacts_root()) / "CURRENT"
    if pointer.exists():
        return pointer.read_text(encoding="utf-8").strip() or FIRST_VERSION
    return FIRST_VERSION


def artifacts_dir():
    """Thư mục của phiên bản đang phục vụ: mô hình .joblib, metrics.json, validation.json."""
    return artifacts_root() / current_version()
