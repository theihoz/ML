"""Bộ dữ liệu lương mở rộng: gộp ba nguồn thô, chuẩn hóa và gắn nhãn train/valid/test.

Bản thăm dò ban đầu chỉ có 14 nhãn đã duyệt tay. Module này dùng toàn bộ tin có
khoảng lương trong ba file thô sẵn có của dự án, chuẩn hóa về triệu VND/tháng và
chia tập theo công ty để một công ty không xuất hiện ở hai tập cùng lúc.
"""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .training_labels import data_root

DATASET_VERSION = "salary-v2"
SPLIT_SEED = 42
SPLIT_SHARES = {"train": 0.70, "valid": 0.15, "test": 0.15}
USD_RATE = {2023: 23_500, 2024: 24_500, 2025: 25_500, 2026: 26_000}
SALARY_RANGE = (3.0, 150.0)  # triệu VND/tháng, ngoài khoảng này coi là lỗi nhập

# Thứ tự quan trọng: quy tắc cụ thể đứng trước quy tắc chung.
ROLE_RULES = [
    (
        "Quản lý IT / CTO",
        r"\b(?:cto|cio|it manager|head of (?:engineering|technology|it|data)|"
        r"trưởng phòng (?:it|cntt|công nghệ)|giám đốc (?:công nghệ|it|cntt|kỹ thuật)|"
        r"it director|engineering manager)\b",
    ),
    (
        "Tech Lead / Architect",
        r"\b(?:architect|kiến trúc sư|tech(?:nical)? lead|team ?lead(?:er)?|trưởng nhóm)\b",
    ),
    (
        "Bảo mật",
        r"\b(?:security|bảo mật|an ninh mạng|an toàn thông tin|pentest(?:er)?|"
        r"penetration|soc analyst|cyber)\b",
    ),
    (
        "AI / ML Engineer",
        r"\b(?:ai|machine learning|ml|deep learning|computer vision|nlp|llm|genai|"
        r"data scien\w*|trí tuệ nhân tạo|generative)\b",
    ),
    (
        "Data Engineer",
        r"\b(?:data engineer\w*|kỹ sư dữ liệu|big data|etl|data platform|data warehouse)\b",
    ),
    (
        "Data Analyst / BI",
        r"\b(?:data analy\w*|phân tích dữ liệu|bi|business intelligence|power bi|"
        r"reporting analyst)\b",
    ),
    (
        "Quản trị CSDL (DBA)",
        r"\b(?:dba|database admin\w*|quản trị (?:cơ sở dữ liệu|csdl)|database engineer)\b",
    ),
    (
        "DevOps / Cloud",
        r"\b(?:devops|devsecops|sre|site reliability|cloud engineer|kỹ sư cloud|"
        r"platform engineer|cloud)\b",
    ),
    (
        "Kiểm thử (QA/QC)",
        r"\b(?:tester|test|testing|qa|qc|kiểm thử|quality assurance|automation test\w*)\b",
    ),
    (
        "BrSE / Cầu nối",
        r"\b(?:brse|bridge (?:system )?(?:software )?engineer|kỹ sư cầu nối|comtor)\b",
    ),
    (
        "Business Analyst",
        r"\b(?:business analyst|ba|phân tích nghiệp vụ|system analyst|phân tích hệ thống)\b",
    ),
    (
        "Quản lý dự án / sản phẩm",
        r"\b(?:project manager|product manager|product owner|pm|po|scrum master|"
        r"quản lý dự án|quản trị dự án|delivery manager|project coordinator)\b",
    ),
    (
        "UI/UX Designer",
        r"(?:ui\s*/\s*ux|ux\s*/\s*ui|ui-ux|\bui ux\b|\bux designer\b|\bui designer\b|"
        r"\bproduct designer\b|thiết kế (?:ui|giao diện))",
    ),
    ("Game Developer", r"\b(?:game|unity|unreal|cocos)\b"),
    (
        "Embedded / IoT",
        r"\b(?:embedded|nhúng|firmware|iot|vi điều khiển|fpga|autosar)\b",
    ),
    (
        "Mobile Developer",
        r"\b(?:mobile|android|ios|flutter|react native|kotlin|swift)\b",
    ),
    ("Fullstack Developer", r"\bfull[ -]?stack\b"),
    (
        "Frontend Developer",
        r"\b(?:front[ -]?end|reactjs|react\.js|react|vue(?:\.?js)?|angular(?:js)?)\b",
    ),
    (
        "ERP / SAP Consultant",
        r"\b(?:erp|sap|odoo|dynamics 365|tư vấn triển khai|triển khai phần mềm)\b",
    ),
    (
        "Backend Developer",
        r"(?:\bback[ -]?end\b|\bjava\b(?!script)|\bphp\b|\.net\b|\bgolang\b|\bnode\.?js\b|"
        r"\bpython\b|\bruby\b|c#|c\+\+|\blaravel\b|\bspring\b|\bdjango\b)",
    ),
    (
        "Quản trị hệ thống / Mạng",
        r"\b(?:system admin\w*|sysadmin|quản trị hệ thống|quản trị mạng|network\w*|"
        r"kỹ sư mạng|hạ tầng|infrastructure|system engineer|kỹ sư hệ thống|"
        r"vận hành hệ thống)\b",
    ),
    (
        "IT Support / Helpdesk",
        r"\b(?:help ?desk|it support|hỗ trợ kỹ thuật|technical support|"
        r"kỹ thuật viên (?:it|máy tính|tin học)|nhân viên (?:it|công nghệ thông tin|cntt)|"
        r"it officer|it staff|chuyên viên (?:it|cntt)|it executive|it hardware)\b",
    ),
    (
        "Software Engineer (chung)",
        r"\b(?:software|developer|programmer|lập trình|phần mềm|coder|web developer)\b",
    ),
]
ROLE_ORDER = [name for name, _ in ROLE_RULES]
EXCLUDED_TITLE = (
    r"\b(?:sales|presales|kinh doanh|bán hàng|telesales?|marketing|kế toán|accountant|"
    r"tuyển dụng|recruit\w*|nhân sự|hr|chăm sóc khách hàng|customer service|giáo viên|"
    r"teacher|giảng viên|trainer|tuyển sinh|content|biên tập|copywriter|cơ khí|xây dựng)\b"
)

# Từ vựng kỹ năng dùng chung cho dashboard, mô hình và tư vấn.
SKILLS = {
    "Python": r"python",
    "Java": r"java(?!\s*script)",
    "JavaScript": r"javascript|\bjs\b",
    "TypeScript": r"typescript",
    "C#": r"c#",
    "C++": r"c\+\+",
    "PHP": r"php",
    "Golang": r"golang|\bgo developer",
    "Kotlin": r"kotlin",
    "Swift": r"swift",
    "Dart": r"\bdart\b",
    "Ruby": r"\bruby\b",
    "Rust": r"\brust\b",
    "Scala": r"\bscala\b",
    "SQL": r"\bsql\b",
    "HTML/CSS": r"\bhtml5?\b|\bcss3?\b",
    "React": r"react(?:\.?js)?(?!\s*native)",
    "React Native": r"react\s*native",
    "Vue.js": r"\bvue(?:\.?js)?\b",
    "Angular": r"\bangular(?:js)?\b",
    "Node.js": r"node\.?js",
    "Next.js": r"next\.?js",
    ".NET": r"\.net\b|dotnet|asp\.net",
    "Spring Boot": r"spring\s*boot|\bspring\b",
    "Django": r"django",
    "FastAPI/Flask": r"fastapi|\bflask\b",
    "Laravel": r"laravel",
    "Flutter": r"flutter",
    "Unity": r"\bunity(?:3d)?\b",
    "MySQL": r"mysql",
    "PostgreSQL": r"postgres(?:ql)?",
    "MongoDB": r"mongo(?:db)?",
    "Redis": r"\bredis\b",
    "SQL Server": r"sql\s*server|mssql",
    "Oracle": r"\boracle\b",
    "AWS": r"\baws\b|amazon web services",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|google cloud",
    "Docker": r"docker",
    "Kubernetes": r"kubernetes|\bk8s\b",
    "Linux": r"\blinux\b|ubuntu|centos",
    "Git": r"\bgit\b|github|gitlab",
    "CI/CD": r"ci\s*/\s*cd|jenkins|github actions",
    "Microservices": r"micro-?services?",
    "REST API": r"rest(?:ful)?\s*api|\bapi\b",
    "Kafka": r"kafka",
    "Spark": r"\bspark\b|pyspark",
    "Airflow": r"airflow",
    "Power BI": r"power\s*bi",
    "Tableau": r"tableau",
    "Excel": r"\bexcel\b",
    "Machine Learning": r"machine learning|\bml\b",
    "Deep Learning": r"deep learning|neural network",
    "TensorFlow/PyTorch": r"tensorflow|pytorch|keras",
    "NLP": r"\bnlp\b|xử lý ngôn ngữ",
    "Computer Vision": r"computer vision|thị giác máy|opencv",
    "LLM / GenAI": r"\bllms?\b|genai|generative ai|langchain|rag\b|chatgpt|openai",
    "Selenium": r"selenium",
    "Automation Test": r"automation test\w*|test automation|kiểm thử tự động",
    "Figma": r"figma",
    "Agile/Scrum": r"agile|scrum|kanban",
    "Jira": r"\bjira\b",
    "SAP": r"\bsap\b",
    "Odoo": r"odoo",
    "Mạng (CCNA)": r"ccna|ccnp|cisco|routing|switching",
    "An ninh mạng": r"pentest|owasp|siem|bảo mật|security",
    "Embedded C": r"embedded|vi điều khiển|microcontroller|\bmcu\b|rtos",
    "Tiếng Anh": r"tiếng anh|english|toeic|ielts",
    "Tiếng Nhật": r"tiếng nhật|japanese|\bjlpt\b|\bn[1-3]\b",
}
_SKILL_PATTERNS = {name: re.compile(rf"(?:{alias})", re.I) for name, alias in SKILLS.items()}
_ROLE_PATTERNS = [(name, re.compile(pattern, re.I)) for name, pattern in ROLE_RULES]
_EXCLUDED = re.compile(EXCLUDED_TITLE, re.I)
LEVELS = ["Intern", "Fresher", "Junior", "Middle", "Senior", "Lead", "Manager"]
REGIONS = ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Tỉnh/thành khác", "Remote"]


def dataset_dir():
    return data_root() / "processed"


def dataset_path():
    return dataset_dir() / "salary_dataset_v2.csv"


def classify_role(title):
    """Gán một vai trò CNTT theo chức danh; None nếu ngoài ngành hoặc không rõ."""
    text = re.sub(r"\s+", " ", str(title or "")).strip()
    if not text or _EXCLUDED.search(text):
        return None
    for name, pattern in _ROLE_PATTERNS:
        if pattern.search(text):
            return name
    return None


def parse_salary(text, year=2026):
    """Chuẩn hóa chuỗi lương về (thấp, cao, trung điểm) triệu VND/tháng."""
    if not isinstance(text, str):
        return None
    raw = text.lower().replace("triẹu", "triệu").replace("lương:", "").strip()
    if not re.search(r"\d", raw) or re.search(
        r"thỏa thuận|thoả thuận|thương lượng|cạnh tranh", raw
    ):
        return None
    usd = "$" in raw or "usd" in raw
    yearly = bool(re.search(r"/\s*năm|per year|/year", raw))
    numbers = []
    for token in re.findall(r"\d+(?:[.,]\d+)*", raw):
        if usd or re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", token):
            value = float(re.sub(r"[.,]", "", token))
        elif re.fullmatch(r"\d+(?:[.,]\d+)?", token):
            value = float(token.replace(",", "."))
        else:
            return None  # số dạng "2.147.5" không đọc được một cách chắc chắn
        numbers.append(value)
    if not numbers:
        return None
    numbers = numbers[:2]
    if usd:
        numbers = [n * USD_RATE.get(year, 26_000) / 1e6 for n in numbers]
    else:
        numbers = [n / 1e6 if n >= 100_000 else n for n in numbers]
    if yearly:
        numbers = [n / 12 for n in numbers]
    if len(numbers) == 2:
        low, high = sorted(numbers)
    elif re.search(r"tới|đến|up to|dưới|max", raw):
        high = numbers[0]
        low = high * 0.7
    elif re.search(r"từ|trên|from|min", raw):
        low = numbers[0]
        high = low * 1.3
    else:
        low = high = numbers[0]
    if low <= 0 or high / low > 3:
        return None  # khoảng quá rộng như "1 - 40 triệu" không mang thông tin
    middle = (low + high) / 2
    if not SALARY_RANGE[0] <= middle <= SALARY_RANGE[1]:
        return None
    return round(low, 3), round(high, 3), round(middle, 3)


def parse_experience(text, title=""):
    """Số năm kinh nghiệm yêu cầu (float) hoặc NaN nếu nguồn không ghi."""
    raw = str(text or "").lower()
    if re.search(r"không yêu cầu|chưa có kinh nghiệm|no experience|không cần kinh nghiệm", raw):
        return 0.0
    if match := re.search(r"dưới\s*(\d+(?:[.,]\d+)?)", raw):
        return float(match[1].replace(",", ".")) / 2
    if match := re.search(r"trên\s*(\d+)", raw):
        return float(match[1]) + 1
    if match := re.search(r"(\d+)\s*-\s*(\d+)", raw):
        return (float(match[1]) + float(match[2])) / 2
    if match := re.search(r"(\d+(?:[.,]\d+)?)", raw):
        value = float(match[1].replace(",", "."))
        return value if value <= 20 else np.nan
    if match := re.search(r"(\d+)\s*\+?\s*(?:yoe|years?|năm)", str(title).lower()):
        return float(match[1])
    return np.nan


def derive_level(title, years, source_level=""):
    title = str(title or "").lower()
    source_level = str(source_level or "").lower()
    if re.search(r"intern|thực tập", title + " " + source_level):
        return "Intern"
    if re.search(r"giám đốc|director|trưởng phòng|\bmanager\b|head of", title + " " + source_level):
        return "Manager"
    if re.search(r"\blead|trưởng nhóm|principal|architect", title + " " + source_level):
        return "Lead"
    if re.search(r"fresher|mới tốt nghiệp|graduate", title + " " + source_level):
        return "Fresher"
    if re.search(r"\bsenior\b|\bsr\.?\b|cao cấp", title):
        return "Senior"
    if re.search(r"\bjunior\b|\bjr\.?\b", title):
        return "Junior"
    if re.search(r"\bmiddle\b|\bmid\b", title):
        return "Middle"
    if pd.isna(years):
        return "Junior"
    if years < 1:
        return "Fresher"
    if years < 2.5:
        return "Junior"
    if years < 4.5:
        return "Middle"
    return "Senior"


def normalize_region(text):
    raw = str(text or "").lower()
    if re.search(r"hà nội|ha noi|hanoi", raw):
        return "Hà Nội"
    if re.search(r"hồ chí minh|ho chi minh|hcm|sài gòn|saigon", raw):
        return "TP. Hồ Chí Minh"
    if re.search(r"đà nẵng|da nang", raw):
        return "Đà Nẵng"
    if re.search(r"remote|từ xa", raw):
        return "Remote"
    return "Tỉnh/thành khác"


def extract_skills(*texts):
    text = " \n ".join(str(t) for t in texts if isinstance(t, str))
    text = re.sub(r"<[^>]+>", " ", text)
    return [name for name, pattern in _SKILL_PATTERNS.items() if pattern.search(text)]


def _year(value, default):
    match = re.search(r"(20\d\d)", str(value or ""))
    return int(match[1]) if match else default


def _topcv(raw):
    frame = pd.read_csv(raw / "topcv_jobs.csv")
    for row in frame.itertuples():
        yield {
            "source": "TopCV 2026",
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "salary_text": row.salary,
            "experience_text": row.experience,
            "level_text": "",
            "year": _year(row.date_posted, 2026),
            "skill_text": (row.title,),
        }


def _it_posts(raw):
    frame = pd.read_csv(raw / "vietnam_it_job_posts_v1.csv")
    for row in frame.itertuples():
        try:
            listed = " ".join(json.loads(row.skills)) if isinstance(row.skills, str) else ""
        except json.JSONDecodeError:
            listed = str(row.skills)
        yield {
            "source": f"IT Jobs 2026 ({row.source_platform})",
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "salary_text": row.salary,
            "experience_text": row.experience,
            "level_text": row.level,
            # posted_at của bộ này phân bố đều 2018–2025 ở mọi nền tảng nên không
            # phản ánh ngày đăng thật; dùng năm thu thập (created_at) thay thế.
            "year": _year(row.created_at, 2026),
            "skill_text": (row.title, listed, row.requirements),
        }


def _careerbuilder(raw):
    frame = pd.read_csv(raw / "vietnamese-job-posting.csv")
    frame = frame[frame["category"].fillna("").str.contains("CNTT")]
    for row in frame.itertuples():
        yield {
            "source": "CareerBuilder 2023",
            "title": row.job_title,
            "company": row.company_title,
            "location": row.location,
            "salary_text": row.salary,
            "experience_text": row.exp,
            "level_text": "",
            "year": 2023,
            "skill_text": (row.job_title, row.job_requirements, row.job_description, row.job_tags),
        }


def _company_key(name):
    text = re.sub(r"\s+", " ", str(name or "").lower())
    text = re.sub(r"^(?:pro|hot|top)\s*", "", text)
    return re.sub(r"[^\w]", "", text) or "unknown"


def _split_for(company_key):
    """Chia theo hash công ty: ổn định, tái lập được, không rò rỉ giữa các tập."""
    digest = hashlib.sha256(f"{SPLIT_SEED}:{company_key}".encode()).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    if bucket < SPLIT_SHARES["train"]:
        return "train"
    if bucket < SPLIT_SHARES["train"] + SPLIT_SHARES["valid"]:
        return "valid"
    return "test"


def build_dataset(raw_dir=None):
    """Đọc ba nguồn thô và trả về DataFrame đã làm sạch kèm cột split."""
    raw = Path(raw_dir) if raw_dir else data_root() / "raw"
    funnel = {"raw": 0, "has_salary": 0, "it_role": 0, "deduplicated": 0}
    records = []
    for reader in (_it_posts, _topcv, _careerbuilder):
        for item in reader(raw):
            funnel["raw"] += 1
            year = min(max(item["year"], 2023), 2026)
            salary = parse_salary(item["salary_text"], year)
            if salary is None:
                continue
            funnel["has_salary"] += 1
            title = re.sub(r"\s+", " ", str(item["title"])).strip()
            role = classify_role(title)
            if role is None:
                continue
            funnel["it_role"] += 1
            years = parse_experience(item["experience_text"], title)
            skills = extract_skills(*item["skill_text"])
            records.append(
                {
                    "source": item["source"],
                    "title": title,
                    "company": re.sub(r"\s+", " ", str(item["company"])).strip(),
                    "company_key": _company_key(item["company"]),
                    "role": role,
                    "region": normalize_region(item["location"]),
                    "location_text": item["location"],
                    "experience_years": years,
                    "level": derive_level(title, years, item["level_text"]),
                    "year": year,
                    "skills": "|".join(skills),
                    "skill_count": len(skills),
                    "salary_text": item["salary_text"],
                    "salary_min": salary[0],
                    "salary_max": salary[1],
                    "salary": salary[2],
                }
            )
    frame = pd.DataFrame(records)
    frame["title_key"] = frame["title"].str.lower().str.replace(r"[^\w]", "", regex=True)
    frame = frame.drop_duplicates(["title_key", "company_key", "salary"], keep="first")
    frame = frame.drop(columns="title_key").reset_index(drop=True)
    funnel["deduplicated"] = len(frame)
    frame["split"] = frame["company_key"].map(_split_for)
    frame.insert(0, "row_id", [f"v2-{i:05d}" for i in range(len(frame))])
    return frame, funnel


def write_dataset(raw_dir=None, output=None):
    frame, funnel = build_dataset(raw_dir)
    output = Path(output) if output else dataset_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    summary = {
        "version": DATASET_VERSION,
        "rows": len(frame),
        "companies": int(frame["company_key"].nunique()),
        "funnel": funnel,
        "split": frame["split"].value_counts().to_dict(),
        "roles": frame["role"].value_counts().to_dict(),
        "sources": frame["source"].value_counts().to_dict(),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    output.with_suffix(".json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def load_dataset():
    path = dataset_path()
    if not path.exists():
        write_dataset()
    frame = pd.read_csv(path)
    frame["skills"] = frame["skills"].fillna("")
    return frame


def skill_lists(frame):
    return frame["skills"].fillna("").map(lambda value: [s for s in value.split("|") if s])
