"""Offline, audited training on one admitted cohort. UI never calls train()."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from .companies import stable_id
from .training_labels import RAW_SHA256, data_root

POLICY_SHA256 = "33cadf3ac969766f3eec7cb9503ae04613c1f1688f352c44ec0fd044cec7ce86"
LABEL_MANIFEST_SHA256 = "4bb9edadeaf88122a038309fe10c781d4be66800a60623b29457396a08116cab"
APPROVED_REPORTS = {
    "7137291a5d16b71f1861": "5ffa9e899695b58ed9aca2b07b334276c11479c642e9b7377981adaaca0c6d5e"
}


def policy_path():
    package = Path(__file__).resolve().parent
    bundled = package / "config/training-policy-v1.json"
    return bundled if bundled.is_file() else package.parents[1] / "config/training-policy-v1.json"


def readiness(service):
    content = policy_path().read_bytes()
    if hashlib.sha256(content).hexdigest() != POLICY_SHA256:
        raise ValueError("Policy changed after lock; review and a new pre-fit policy are required.")
    policy = json.loads(content)
    # This is the immutable evidence bundle written BEFORE the first fit, rather
    # than a new adjudication with today's parser/catalog rules.
    label_dir = data_root() / "labels/2026-10-30"
    manifest_bytes = (label_dir / "manifest.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != LABEL_MANIFEST_SHA256:
        raise ValueError("Frozen label manifest changed; refuse fit.")
    manifest = json.loads(manifest_bytes)
    required = {"accepted.json", "accepted.csv", "review-ledger.json", "readiness-before-fit.json"}
    if not required.issubset(manifest["files"]):
        raise ValueError("Incomplete frozen label manifest.")
    for name, expected in manifest["files"].items():
        if (
            Path(name).name != name
            or hashlib.sha256((label_dir / name).read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Frozen label file changed: " + name)
    raw_path = data_root() / "raw/vietnam_it_job_posts_v1.csv"
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != RAW_SHA256:
        raise ValueError("Frozen source checksum mismatch.")
    frozen = json.loads((label_dir / "readiness-before-fit.json").read_text())
    labels = frozen["labels"]
    if stable_id(labels["rows"]) != manifest["labels_sha256"]:
        raise ValueError("Frozen label identity mismatch.")
    if labels["rows"] != json.loads((label_dir / "accepted.json").read_text()):
        raise ValueError("Frozen accepted evidence mismatch.")
    if labels["source_raw_sha256"] != policy["source_raw_sha256"]:
        raise ValueError("Policy/source mismatch.")
    split = frozen["split"]
    recomputed = service.preview_split(
        labels["rows"], basis=policy["cohort"]["basis"], scope=policy["cohort"]["scope"]
    )
    if recomputed != split or frozen["policy_sha256"] != POLICY_SHA256:
        raise ValueError("Split/rules drift from the pre-fit frozen membership.")
    blockers = []
    if len(labels["rows"]) < policy["minimum_entities"]:
        blockers.append("insufficient_entities")
    if split["eligible_groups"] < policy["minimum_groups"]:
        blockers.append("insufficient_groups")
    for part in ("train", "validation", "test"):
        members = [r for r in split["membership"] if r["split"] == part]
        if len(members) < policy["minimum_split_entities"][part]:
            blockers.append(f"insufficient_{part}_entities")
        if len({r["group_id"] for r in members}) < policy["minimum_split_groups"][part]:
            blockers.append(f"insufficient_{part}_groups")
    if split["conflicting_entities"]:
        blockers.append("conflicting_entities")
    return {
        "ready": not blockers,
        "blockers": blockers,
        "policy": policy,
        "policy_sha256": POLICY_SHA256,
        "labels_sha256": labels["labels_sha256"],
        "split": split,
        "labels": labels,
        "note": "Approved exploratory cohort only; EDA and YODY gates are separate.",
    }


def features(row):
    # Strict allowlist: salary, title/JD, ID, employer and source never enter X.
    result = {"role=" + row["role"]: 1.0, "experience_kind=" + row["experience_kind"]: 1.0}
    for key in ("experience_min", "experience_max"):
        value = row.get(key)
        result[key + "_missing"] = float(value is None)
        if value is not None:
            result[key] = float(value)
    for field in ("skills", "locations", "work_modes"):
        for value in row.get(field, []):
            result[field + "=" + value] = 1.0
    return result


def scores(actual, predicted):
    import numpy as np

    error = np.asarray(predicted) - np.asarray(actual)
    if not np.isfinite(error).all():
        raise ValueError("Nonfinite model prediction.")
    return {
        "MAE": float(np.abs(error).mean()),
        "RMSE": float(np.sqrt((error**2).mean())),
        "n": len(error),
    }


def default_runs():
    return data_root().parent / "artifacts/runs"


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )


def evaluation_registry():
    # Always under the application, never beneath a caller-selected output root.
    return data_root().parent / "artifacts/evaluation-reservations"


def cohort_key(ready):
    return stable_id(
        [
            ready["labels"]["source_raw_sha256"],
            ready["policy"]["cohort"],
            sorted(row["posting_id"] for row in ready["labels"]["rows"]),
        ]
    )


def reserve_evaluation(ready, run_dir):
    registry = evaluation_registry()
    registry.mkdir(parents=True, exist_ok=True)
    record = registry / (cohort_key(ready) + ".json")
    value = {
        "run_dir": str(run_dir.resolve()),
        "labels_sha256": ready["labels_sha256"],
        "policy_sha256": POLICY_SHA256,
        "status": "reserved_before_evaluation",
    }
    if (run_dir / "report.json").is_file():
        value.update(
            status="evaluated",
            report_sha256=hashlib.sha256((run_dir / "report.json").read_bytes()).hexdigest(),
        )
    try:
        with record.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
    except FileExistsError:
        old = json.loads(record.read_text())
        if (
            old["run_dir"] != str(run_dir.resolve())
            or old["labels_sha256"] != ready["labels_sha256"]
            or old["policy_sha256"] != POLICY_SHA256
        ):
            raise ValueError(
                "Cohort test is already reserved/evaluated elsewhere; no automatic refit or new output-root bypass."
            )
        if not (run_dir / "report.json").is_file():
            raise ValueError(
                "Interrupted evaluation reservation exists; do not retry automatically."
            )
        if old.get("report_sha256") and old["report_sha256"] != value["report_sha256"]:
            raise ValueError("Evaluated report changed after registration.")
        if "report_sha256" not in old:
            update = record.with_suffix(".tmp")
            write_json(update, value)
            update.replace(record)
    return record


def train(service, output_root=None):
    import joblib
    import numpy as np
    import sklearn
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    ready = readiness(service)
    if not ready["ready"]:
        raise ValueError("Training blocked: " + ", ".join(ready["blockers"]))
    policy = ready["policy"]
    split = ready["split"]
    run_id = stable_id([ready["labels_sha256"], split["membership_sha256"], POLICY_SHA256])[:20]
    root = Path(output_root) if output_root else default_runs()
    run_dir = root / run_id
    # A distributed, evaluated run also reserves the cohort in a fresh install,
    # before callers can attempt a first fit through a different destination.
    for existing in default_runs().glob("*/report.json"):
        previous = load_run(existing.parent)["report"]
        if (
            previous["source_raw_sha256"] == ready["labels"]["source_raw_sha256"]
            and previous["cohort"] == policy["cohort"]
        ):
            if previous["labels_sha256"] != ready["labels_sha256"]:
                raise ValueError(
                    "Cohort already evaluated with another feature snapshot; a fresh untouched holdout is required."
                )
            reserve_evaluation(ready, existing.parent)
    if run_dir.exists():
        if (run_dir / "report.json").is_file():
            report = load_run(run_dir)["report"]
            # Adopt the completed v1 run into the new guard without fitting it again.
            reserve_evaluation(ready, run_dir)
            return report
        raise ValueError(
            "Incomplete immutable run exists; inspect it before any retry. Test is not retried automatically."
        )
    root.mkdir(parents=True, exist_ok=True)
    for old_report in root.glob("*/report.json"):
        old = json.loads(old_report.read_text())
        if old.get("labels_sha256") == ready["labels_sha256"]:
            raise ValueError(
                "This dataset already has an evaluated run. Reusing test for another configuration is forbidden."
            )
    reservation = reserve_evaluation(ready, run_dir)
    run_dir.mkdir()
    write_json(run_dir / "policy.json", policy)
    write_json(
        run_dir / "split.json",
        {
            **split,
            "status": "locked",
            "policy_sha256": POLICY_SHA256,
            "labels_sha256": ready["labels_sha256"],
            "training_ready": True,
            "blockers": [],
        },
    )
    rows = {r["posting_id"]: r for r in ready["labels"]["rows"]}
    partitions = {
        part: [rows[r["entity_id"]] for r in split["membership"] if r["split"] == part]
        for part in ("train", "validation", "test")
    }
    x = {part: [features(r) for r in members] for part, members in partitions.items()}
    y = {
        part: np.array([r["salary_target_vnd_month"] for r in members])
        for part, members in partitions.items()
    }
    baseline = float(np.median(y["train"]))
    models, validation = {}, {}
    # alpha and solver were locked before fit; no parameter search on this small cohort.
    for name, estimator in (
        ("Ridge", Ridge(**policy["models"]["Ridge"])),
        ("LinearRegression", LinearRegression()),
    ):
        pipeline = Pipeline(
            [
                ("vocabulary", DictVectorizer(sparse=False)),
                ("scale", StandardScaler()),
                ("model", estimator),
            ]
        )
        pipeline.fit(x["train"], y["train"] / 1000000)
        prediction = pipeline.predict(x["validation"]) * 1000000
        validation[name] = scores(y["validation"], prediction)
        models[name] = pipeline
        joblib.dump(pipeline, run_dir / f"{name}.joblib")
    chosen = min(validation, key=lambda name: (validation[name]["MAE"], name != "LinearRegression"))
    # Selection is persisted BEFORE the first test prediction is requested.
    write_json(
        run_dir / "selection.json",
        {"chosen": chosen, "validation": validation, "policy_sha256": POLICY_SHA256},
    )
    metrics, predictions = {}, []
    for name, model in models.items():
        metrics[name] = {}
        for part in partitions:
            predicted = model.predict(x[part]) * 1000000
            metrics[name][part] = scores(y[part], predicted)
            for row, truth, estimate in zip(partitions[part], y[part], predicted):
                predictions.append(
                    {
                        "model": name,
                        "split": part,
                        "posting_id": row["posting_id"],
                        "actual_vnd_month": float(truth),
                        "predicted_vnd_month": float(estimate),
                        "role": row["role"],
                    }
                )
    metrics["train_median_baseline"] = {
        part: scores(y[part], [baseline] * len(y[part])) for part in partitions
    }
    promoted = all(
        metrics[chosen][part]["MAE"] < metrics["train_median_baseline"][part]["MAE"]
        for part in ("validation", "test")
    )
    write_json(run_dir / "predictions.json", predictions)
    write_json(run_dir / "train-support.json", partitions["train"])
    paths = [p for p in run_dir.iterdir() if p.is_file()]
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    report = {
        "run_id": run_id,
        "run_dir": str(run_dir.resolve()),
        "status": "trained",
        "chosen_model": chosen,
        "promoted": promoted,
        "release_reason": "beats_baseline_on_validation_and_test"
        if promoted
        else "baseline_release_criterion_failed",
        "metrics": metrics,
        "unit": "VND/month",
        "cohort": policy["cohort"],
        "counts": split["counts"],
        "actual_ratios": split["actual_ratios"],
        "labels_sha256": ready["labels_sha256"],
        "policy_sha256": POLICY_SHA256,
        "membership_sha256": split["membership_sha256"],
        "source_raw_sha256": ready["labels"]["source_raw_sha256"],
        "source_entities": len(rows),
        "company_count": ready["labels"]["company_count"],
        "feature_names": models[chosen].named_steps["vocabulary"].get_feature_names_out().tolist(),
        "feature_coverage": {
            "experience_evidenced": sum(r["experience_min"] is not None for r in rows.values()),
            "with_title_skills": sum(bool(r["skills"]) for r in rows.values()),
            "train_roles": dict(Counter(r["role"] for r in partitions["train"])),
        },
        "limitations": ready["labels"]["limitations"],
        "versions": {
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "artifact_sha256": hashes,
        "test_policy": "One fixed split, selection locked before test; no refit on train+validation or test-driven retry.",
    }
    write_json(run_dir / "report.json", report)
    reservation_update = reservation.with_suffix(".tmp")
    write_json(
        reservation_update,
        {
            "run_dir": str(run_dir.resolve()),
            "labels_sha256": ready["labels_sha256"],
            "policy_sha256": POLICY_SHA256,
            "status": "evaluated",
            "report_sha256": hashlib.sha256((run_dir / "report.json").read_bytes()).hexdigest(),
        },
    )
    reservation_update.replace(reservation)
    return report


def load_run(run_dir, model_name=None):
    import joblib

    directory = Path(run_dir)
    report = json.loads((directory / "report.json").read_text())
    if model_name is not None and model_name not in {"Ridge", "LinearRegression"}:
        raise ValueError("Unknown prediction model.")
    # Only locally produced artifacts are loaded. No upload/model-import adapter
    # accepts this format, and hashes alone do not authenticate an external pickle.
    if report["chosen_model"] not in {"Ridge", "LinearRegression"}:
        raise ValueError("Unknown chosen model.")
    required = {
        "Ridge.joblib",
        "LinearRegression.joblib",
        "policy.json",
        "split.json",
        "selection.json",
        "predictions.json",
        "train-support.json",
    }
    if set(report["artifact_sha256"]) != required:
        raise ValueError("Incomplete or unexpected artifact manifest.")
    if (
        APPROVED_REPORTS.get(report["run_id"])
        != hashlib.sha256((directory / "report.json").read_bytes()).hexdigest()
    ):
        raise ValueError(
            "Report is not an approved local training run; external pickles are not accepted."
        )
    for name, expected in report["artifact_sha256"].items():
        if (
            Path(name).name != name
            or (directory / name).resolve().parent != directory.resolve()
            or hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Artifact integrity check failed: " + name)
    if (
        hashlib.sha256((directory / "policy.json").read_bytes()).hexdigest()
        != report["artifact_sha256"]["policy.json"]
    ):
        raise ValueError("Policy artifact changed.")
    if json.loads((directory / "selection.json").read_text())["chosen"] != report["chosen_model"]:
        raise ValueError("Selection/report mismatch.")
    return {
        "report": report,
        "artifact_directory": str(directory.resolve()),
        "model": joblib.load(directory / f"{model_name or report['chosen_model']}.joblib"),
        "prediction_model": model_name or report["chosen_model"],
        "train": json.loads((directory / "train-support.json").read_text()),
        "policy": json.loads((directory / "policy.json").read_text()),
    }


def audit_run(run_dir=None):
    import numpy as np

    if run_dir is None:
        reports = sorted(default_runs().glob("*/report.json"))
        if not reports:
            raise ValueError("Chưa có run huấn luyện đã hoàn tất.")
        run_dir = reports[-1].parent
    directory = Path(run_dir)
    loaded = load_run(directory)
    report = loaded["report"]
    saved = json.loads((directory / "predictions.json").read_text())
    expected = {
        p["posting_id"]: p["predicted_vnd_month"]
        for p in saved
        if p["model"] == report["chosen_model"] and p["split"] == "train"
    }
    predictions = loaded["model"].predict([features(r) for r in loaded["train"]]) * 1000000
    errors = [
        abs(float(prediction) - expected[row["posting_id"]])
        for row, prediction in zip(loaded["train"], predictions)
    ]
    maximum = max(errors)
    return {
        "report": report,
        "reload_check": {
            "consistent": bool(np.isfinite(maximum) and maximum < 0.01),
            "max_absolute_error_vnd": maximum,
            "observations": len(errors),
        },
        "split": json.loads((directory / "split.json").read_text()),
        "predictions": saved,
        "artifact_directory": str(directory.resolve()),
        "review_addendum": json.loads(
            (data_root() / "provenance/training-2026-10-30/post-fit-corrections.json").read_text()
        ),
    }
