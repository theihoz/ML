"""Structural split preview. Policy approval and training remain separate."""

import math
from collections import defaultdict

from .companies import company_report, stable_id

RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}
SEED = 42


def preview_split(rows, *, basis, scope):
    report = company_report(rows)
    entities = defaultdict(list)
    for row in report["rows"]:
        target = row.get("salary_target_vnd_month")
        if (
            row["status"] == "ready_for_split"
            and row.get("partition") in {"eda", "duplicates"}
            and row.get("salary_currency") == "VND"
            and row.get("salary_period") == "MONTH"
            and row.get("salary_basis") == basis
            and row.get("compensation_scope") == scope
            and isinstance(target, (int, float))
            and not isinstance(target, bool)
            and math.isfinite(target)
            and target > 0
        ):
            entities[row["entity_id"]].append(row)
    blockers = ["salary_gate_not_open", "approved_support_policy_required"]
    conflicts = sorted(
        entity
        for entity, members in entities.items()
        if len({r["salary_target_vnd_month"] for r in members}) > 1
    )
    groups = defaultdict(list)
    for entity, members in sorted(entities.items()):
        row = min(members, key=lambda r: (r["company_canonical"], r["source_id"]))
        groups[row["group_id"]].append(
            {
                "entity_id": entity,
                "group_id": row["group_id"],
                "company_canonical": row["company_canonical"],
                "source_id": row["source_id"],
            }
        )
    if conflicts:
        blockers.append("conflicting_entity_targets")
    if len(groups) < 3:
        blockers.append("insufficient_independent_labeled_groups")
    membership = []
    counts = dict.fromkeys(RATIOS, 0)
    if not conflicts and len(groups) >= 3:
        # Largest groups first; seeded hashes break equal-size ties independent of row order.
        ordered = sorted(groups, key=lambda key: (-len(groups[key]), stable_id([SEED, key])))
        total = len(entities)
        for index, key in enumerate(ordered):
            empty = [name for name, count in counts.items() if not count]
            choices = empty if len(ordered) - index == len(empty) else list(RATIOS)
            size = len(groups[key])
            chosen = min(
                choices,
                key=lambda name: sum(
                    (counts[part] + (size if part == name else 0) - total * ratio) ** 2
                    for part, ratio in RATIOS.items()
                ),
            )
            counts[chosen] += size
            membership.extend({**row, "split": chosen} for row in groups[key])
    membership.sort(key=lambda r: r["entity_id"])
    return {
        "status": "preview_only" if membership else "blocked",
        "training_ready": False,
        "blockers": blockers,
        "seed": SEED,
        "target_ratios": dict(RATIOS),
        "cohort": {"currency": "VND", "period": "MONTH", "basis": basis, "scope": scope},
        "eligible_entities": len(entities),
        "eligible_groups": len(groups),
        "conflicting_entities": conflicts,
        "counts": counts,
        "actual_ratios": {
            name: count / len(membership) if membership else 0 for name, count in counts.items()
        },
        "membership": membership,
        "membership_sha256": stable_id(membership),
        "input_sha256": stable_id(sorted(rows, key=stable_id)),
        "group_rules_version": report["rules_version"],
        "policy_sha256": None,
        "note": "Xem trước cấu trúc; chưa khóa manifest huấn luyện. Không fit hoặc chọn model.",
    }
