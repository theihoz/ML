"""Đọc mốc báo cáo; không tham gia huấn luyện lương chào tuyển."""

import pandas as pd

from ..paths import data_root


def load_reference(path=None):
    frame = pd.read_csv(
        path or data_root() / "reference" / "salary_reference.csv", dtype=object
    ).fillna("")
    if frame["id"].duplicated().any():
        raise ValueError("Bộ đối chiếu có id trùng.")
    if not (pd.to_numeric(frame["value"]) > 0).all():
        raise ValueError("Mốc lương đối chiếu phải dương.")
    return frame


def matching_profiles(frame, row):
    mask = pd.Series(True, index=frame.index)
    for key in ("role", "region"):
        if row[key]:
            mask &= frame[key] == row[key]
    if row["level"]:
        mask &= frame["level"].isin(row["level"].split("|"))
    if row["years_min"] != "":
        mask &= frame["experience_years"] >= float(row["years_min"])
        mask &= frame["experience_years"] < float(row["years_max"])
    return frame[mask]
