# Bộ đối chiếu

`salary_reference.csv` stores million VND/month. It is excluded from model fitting.

- `evaluation`: all ten national TopDev 2024–2025 gross role medians, pages 28–30. Grouped roles use published occupational representatives as disclosed in each row. These are not city/level cells.
- `calibration`: fifteen TopDev level/city gross **means**, page 25, separate approximate anchors for later calibration. Lead and Manager share one source cell.
- `role_calibration`: ten fixed occupational representatives per verified ITviec edition (2023–2024 and 2024–2025), for #117. Equal edition weight produces an approximate composite anchor, not a pooled population median. Tester represents QA/QC; DevOps/DevSecOps represents DevOps/Cloud. Data Analyst includes DS and AI includes Blockchain: imperfect proxies disclosed in `mapping_caveat`. Alternative Cloud and QA-QC rows remain `context`.
- `context` with unknown basis: ITviec 2025–2026 public role/experience figures, excluded from gross scoring. Earlier editions' verified gross basis does not establish the 2025–2026 basis.

`value` means exactly `statistic`; `median` is populated only for median rows. Blank p25/p75 means unpublished, not inferred from a salary range. Blank `sample_size` means unknown cell count; `report_total_respondents` is a separate report total. ITviec experience coordinates are median years **in the current position**, not total experience and not a restriction on the national role cohort.

TopDev values retain the known PDF mirror URL, explicitly distinguished from the publisher landing page in notes. ITviec verified rows link to primary official PDFs with printed and PDF page numbers. Full methodology and sources: `docs/research/luong-it-viet-nam-doi-chieu.md`.

TopDev USD values multiply by the report's stated 25,000 VND/USD, then divide by 1,000,000. VND values divide by 1,000,000. No net figures are converted: a future conversion needs an explicit sourced tax/insurance rule; unknown is never silently gross.

`python -m career_market reality-check` scores saved predictions at inference year 2026 on TRAIN profiles, without reading their salaries as survey outcomes. It reports all ten evaluation cells, counts missing cohorts against the denominator, and applies ≤15% error in ≥80% of cells. Means and unknown-basis figures appear separately. The frozen two-stage policy first matches TopDev level/city means, then scales each role to the equal-edition arithmetic mean of its two published ITviec medians. This composite anchor is not a pooled population median. No city refit follows role scaling, so final city means can shift; before/after diagnostics are reported separately. The ten TopDev role evaluation cells never fit or tune factors: 8/10 meet the unchanged threshold, with Frontend and Mobile failures retained. No inflation adjustment or HN/HCM subgroup accuracy is claimed. Calibration anchors are fitted quantities, not independent validation. See ADR 0014.
