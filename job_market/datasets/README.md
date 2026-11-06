# Dữ liệu

`raw/` giữ nguyên 3 file tải từ Kaggle; `processed/` là kết quả của `python -m career_market build-dataset`.

| File thô | Nguồn | Giấy phép |
| --- | --- | --- |
| `raw/topcv_jobs.csv` | Châu Gia Bảo, *Vietnam IT Jobs – Raw Data from TopCV (2026)*, [Kaggle](https://www.kaggle.com/datasets/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026) | CC BY 4.0 |
| `raw/vietnam_it_job_posts_v1.csv` | Việt Thành Nguyễn, *ADY201m Dataset* (VietnamWorks, ITviec, TopCV, CareerViet), [Kaggle](https://www.kaggle.com/datasets/vitthnhnguyn138/vietnam-it-job-posts) | MIT |
| `raw/vietnamese-job-posting.csv` | Nguyen Tran Huu Thinh, *Vietnamese Job Posting* (CareerBuilder 2023), [Kaggle](https://www.kaggle.com/datasets/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version) | CC0 |

`processed/salary_dataset_v2.csv`: 3.809 tin, mỗi dòng một tin có lương, cột `split` = train/valid/test. File `.json` cùng tên ghi phễu làm sạch, số tin theo vai trò/nguồn và SHA-256.
