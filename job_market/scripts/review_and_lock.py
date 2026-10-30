"""Verify the frozen pre-fit dossier without rewriting an exposed-test dataset."""

import json

from career_market import MarketService

ready = MarketService().training_readiness()
print(
    json.dumps(
        {
            "ready": ready["ready"],
            "counts": ready["split"]["counts"],
            "entities": ready["labels"]["accepted_entities"],
            "companies": ready["labels"]["company_count"],
            "policy_sha256": ready["policy_sha256"],
            "note": "Frozen pre-fit files verified; no adjudication rewrite or fit.",
        },
        ensure_ascii=False,
        indent=2,
    )
)
