"""Đo độ nhiễu nhãn lương và sàn sai số đạt được (issue theihoz/ML#77).

Chạy từ gốc repo:
    PYTHONPATH=job_market/src job_market/.venv/bin/python docs/research/salary_label_noise.py
"""

import re

import numpy as np
import pandas as pd

from career_market.salary_dataset import load_dataset
from career_market.salary_model import artifacts_dir, feature_frame

rng = np.random.default_rng(0)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 20)


def bound_kind(text, low, high):
    """Phân loại cách parse_salary tạo khoảng: hai đầu, suy ra một đầu, hay một điểm."""
    raw = str(text).lower()
    if np.isclose(low, high):
        return "point"
    if len(re.findall(r"\d+(?:[.,]\d+)*", raw)) >= 2:
        return "two-sided"
    if re.search(r"tới|đến|up to|dưới|max", raw):
        return "upper-only (low=0.7x)"
    if re.search(r"từ|trên|from|min", raw):
        return "lower-only (high=1.3x)"
    return "other"


def uniform_abs_err(pred, low, high):
    """E|pred - T| với T ~ U[low, high] (đóng dạng)."""
    pred, low, high = map(np.asarray, (pred, low, high))
    width = high - low
    inside = (pred >= low) & (pred <= high)
    mid = (low + high) / 2
    safe = np.where(width > 0, width, 1)
    inside_val = ((pred - low) ** 2 + (high - pred) ** 2) / (2 * safe)
    out = np.where(inside, inside_val, np.abs(pred - mid))
    return np.where(width > 0, out, np.abs(pred - low))


def mc_ape(pred_fn, low, high, draws=2000):
    """MAPE kỳ vọng khi lương thật T ~ U[low, high]; pred_fn(mid) -> dự đoán."""
    u = rng.random((draws, len(low)))
    t = low + u * (high - low)
    pred = pred_fn((low + high) / 2)
    return float(np.mean(np.abs(pred - t) / t) * 100)


data = load_dataset()
data["ratio"] = data.salary_max / data.salary_min
data["width"] = data.salary_max - data.salary_min
data["kind"] = [bound_kind(*r) for r in data[["salary_text", "salary_min", "salary_max"]].values]

print("== 1. Cách tạo khoảng (toàn bộ dữ liệu, n=%d)" % len(data))
print(data.kind.value_counts().to_frame("n").assign(share=lambda f: (f.n / f.n.sum()).round(3)))
print(data.groupby("kind").ratio.describe(percentiles=[0.1, 0.5, 0.9]).round(3))

print("\n== 2. Phân bố cao/thấp (chỉ khoảng hai đầu)")
two = data[data.kind == "two-sided"]
print(two.ratio.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(3))
print(pd.cut(data.ratio, [0.99, 1.0001, 1.2, 1.5, 2, 2.5, 3.01]).value_counts(sort=False))

print("\n== 3. Theo nguồn")
by_src = data.groupby("source").agg(
    n=("salary", "size"),
    median_salary=("salary", "median"),
    median_ratio=("ratio", "median"),
)
by_src["mean_halfwidth_over_mid"] = (data.width / 2 / data.salary).groupby(data.source).mean().round(3)
by_src["share_two_sided"] = (data.kind == "two-sided").groupby(data.source).mean().round(3)
by_src["share_one_sided"] = data.kind.str.contains("only").groupby(data.source).mean().round(3)
by_src["share_point"] = (data.kind == "point").groupby(data.source).mean().round(3)
by_src["mean_skill_count"] = data.groupby("source").skill_count.mean().round(2)
by_src["share_exp_missing"] = data.experience_years.isna().groupby(data.source).mean().round(3)
print(by_src)

print("\n== 4. Sàn nhiễu: dự đoán = trung điểm (mô hình hoàn hảo theo nhãn), T ~ U[low, high]")
test = data[data.split == "test"].copy()
for name, frame in [("all", data), ("test", test)]:
    floor_mae = float(((frame.width) / 4).mean())
    floor_mape = mc_ape(lambda m: m, frame.salary_min.values, frame.salary_max.values)
    print(f"{name}: E|mid - T| = {floor_mae:.3f} tr, MAPE = {floor_mape:.2f}%")

print("\n== 5. Mô hình GradientBoosting trên test, theo lát")
pred = pd.read_csv(artifacts_dir() / "test_predictions.csv")[["row_id", "predicted"]]
test = test.merge(pred, on="row_id", how="inner")
assert len(test) == 696
test["ae_mid"] = (test.predicted - test.salary).abs()
test["ape_mid"] = test.ae_mid / test.salary * 100
test["ae_uniform"] = uniform_abs_err(test.predicted, test.salary_min, test.salary_max)
test["dist_to_range"] = np.maximum(
    0, np.maximum(test.salary_min - test.predicted, test.predicted - test.salary_max)
)
test["inside"] = test.dist_to_range == 0
test["floor"] = test.width / 4


def summary(frame):
    return pd.Series(
        {
            "n": len(frame),
            "MAE_mid": frame.ae_mid.mean(),
            "MAPE_mid": frame.ape_mid.mean(),
            "MAE_vs_uniformT": frame.ae_uniform.mean(),
            "noise_floor": frame.floor.mean(),
            "dist_to_range": frame.dist_to_range.mean(),
            "share_inside": frame.inside.mean(),
        }
    ).round(3)


print(summary(test).to_frame("all").T)
print(test.groupby("kind").apply(summary, include_groups=False))
print(test.groupby("source").apply(summary, include_groups=False))
test["ratio_bin"] = pd.cut(test.ratio, [0.99, 1.0001, 1.25, 1.5, 2, 3.01])
print(test.groupby("ratio_bin", observed=True).apply(summary, include_groups=False))

print("\n== 6. Sàn do đặc trưng: tin trùng hệt vector đặc trưng (toàn bộ dữ liệu)")
features = feature_frame(data).apply(lambda row: "|".join(map(str, row)), axis=1)
data["fkey"] = features
grp = data.groupby("fkey").salary
size = grp.transform("size")
dup = data[size >= 2].copy()
dup["dev_median"] = (dup.salary - dup.groupby("fkey").salary.transform("median")).abs()
dup["ape_median"] = dup.dev_median / dup.salary * 100
print(
    f"tin nằm trong nhóm trùng đặc trưng: {len(dup)} / {len(data)} "
    f"({len(dup) / len(data):.1%}), số nhóm: {dup.fkey.nunique()}"
)
print(f"MAE so với trung vị nhóm (in-sample, lạc quan): {dup.dev_median.mean():.3f} tr, "
      f"MAPE {dup.ape_median.mean():.2f}%")
# Bias-corrected: leave-one-out median for groups >=3
loo = []
for _, g in dup.groupby("fkey"):
    if len(g) < 3:
        continue
    vals = g.salary.values
    for i in range(len(vals)):
        others = np.delete(vals, i)
        loo.append((abs(vals[i] - np.median(others)), vals[i]))
loo = np.array(loo)
print(f"LOO (nhóm >=3, n={len(loo)}): MAE {loo[:, 0].mean():.3f} tr, "
      f"MAPE {(loo[:, 0] / loo[:, 1]).mean() * 100:.2f}%")
dup_test = test[test.row_id.isin(dup.row_id)]
print(f"GB trên các tin test thuộc nhóm trùng (n={len(dup_test)}): MAE {dup_test.ae_mid.mean():.3f}")

print("\n== 7. Hiệu chỉnh hệ số suy ra một đầu so với khoảng hai đầu")
print(f"trung vị cao/thấp hai đầu: {two.ratio.median():.3f}; "
      f"giả định 'từ X': 1.300; 'tới X': {1 / 0.7:.3f}")
for kind in ["upper-only (low=0.7x)", "lower-only (high=1.3x)"]:
    sub = test[test.kind == kind]
    if len(sub):
        signed = (sub.predicted - sub.salary).mean()
        print(f"{kind}: n_test={len(sub)}, sai số có dấu (pred - mid) = {signed:+.3f} tr")
two_test = test[test.kind == "two-sided"]
print(f"two-sided: n_test={len(two_test)}, sai số có dấu = {(two_test.predicted - two_test.salary).mean():+.3f} tr")

print("\n== 8. Phân rã phương sai: Var(T | khoảng) = width^2/12 so với MSE của GB")
noise_var = float((test.width**2 / 12).mean())
mse = float(((test.predicted - test.salary) ** 2).mean())
print(f"nhiễu nhãn trung bình = {noise_var:.2f} tr^2 (SD {np.sqrt(noise_var):.2f}); "
      f"MSE(GB, mid) = {mse:.2f} (RMSE {np.sqrt(mse):.2f}); tỉ lệ = {noise_var / mse:.1%}")
print(f"RMSE kỳ vọng so với T = sqrt(MSE + noise) = {np.sqrt(mse + noise_var):.2f}")
