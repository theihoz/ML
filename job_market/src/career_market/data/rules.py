"""BƯỚC 1 — Quy tắc chuẩn hóa một tin tuyển dụng.

Mục này làm gì: từ chữ thô (chức danh, chuỗi lương, kinh nghiệm, địa điểm) suy ra
vai trò, lương triệu VND/tháng, số năm kinh nghiệm, cấp bậc, khu vực và kỹ năng.
"""

import re

import numpy as np
import pandas as pd

# Tỉ giá USD theo năm đăng tin; lương ngoài SALARY_RANGE coi là lỗi nhập.

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


# Điều kiện giới tính ghi trong tin. Chỉ xét chữ có dấu để "Tu 4 Nam Kinh Nghiem"
# (năm kinh nghiệm, không dấu) hay "Việt Nam" không bị nhận nhầm.
GENDER_RULES = [
    ("Nam/Nữ", r"nam\s*(?:/|,|hoặc|và)\s*nữ|nữ\s*(?:/|,|hoặc|và)\s*nam|không phân biệt giới tính"),
    ("Chỉ nam", r"chỉ tuyển nam\b|giới tính\s*[:：-]?\s*nam\b|tuyển nam\b|\bnam giới\b"),
    ("Chỉ nữ", r"chỉ tuyển nữ\b|giới tính\s*[:：-]?\s*nữ\b|tuyển nữ\b|\bnữ giới\b"),
    ("Ưu tiên nam", r"ưu tiên (?:ứng viên )?nam\b"),
    ("Ưu tiên nữ", r"ưu tiên (?:ứng viên )?nữ\b"),
]
_GENDER_PATTERNS = [(name, re.compile(pattern)) for name, pattern in GENDER_RULES]


def gender_requirement(*texts):
    """Nhãn điều kiện giới tính trong tin; mô hình không dùng cột này làm đặc trưng."""
    text = re.sub(r"<[^>]+>", " ", " \n ".join(str(t) for t in texts if isinstance(t, str)))
    text = text.lower()
    for name, pattern in _GENDER_PATTERNS:
        if pattern.search(text):
            return name
    return "Không đề cập"
