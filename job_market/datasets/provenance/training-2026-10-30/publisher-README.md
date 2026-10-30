# Vietnam IT Job Posts

This dataset contains 6,779 job-posting records collected from Vietnamese recruitment platforms. It can be used for job-market exploration, skill analysis, salary analysis, location filtering, and machine-learning experiments.

## File

- `vietnam_it_job_posts.csv`: UTF-8 CSV with one header row and 6,779 data rows.

## Columns

| Column | Description |
| --- | --- |
| `id` | Source database identifier |
| `job_hash` | Deduplication hash |
| `title` | Job title |
| `company` | Company name |
| `location` | Job location |
| `salary` | Salary text as published |
| `experience` | Experience requirement |
| `level` | Seniority or job level |
| `skills` | Skills stored as a JSON array |
| `requirements` | Job requirements text |
| `posted_at` | Source posting timestamp/text |
| `source_url` | Original job-posting URL |
| `source_platform` | Recruitment platform |
| `crawl_time` | Collection timestamp |
| `created_at` | Database creation timestamp |
| `updated_at` | Database update timestamp |
| `job_type` | Employment type, when available |
| `mode` | Work mode, when available |
| `field` | Job field, when available |

Missing PostgreSQL values (`\\N`) are represented as empty CSV fields. Text is encoded as UTF-8.
