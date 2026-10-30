"""Explicit language mentions with original, field-specific evidence."""

import re

LANGUAGES = {
    "JavaScript": r"javascript",
    "Java": r"java",
    "Objective-C": r"objective-c",
    "C++": r"c\+\+",
    "C#": r"c\#",
    "C": r"c",
    "TypeScript": r"typescript",
    "Python": r"python",
    "PHP": r"php",
    "Kotlin": r"kotlin",
    "Swift": r"swift",
    "Dart": r"dart",
    "Ruby": r"ruby",
    "Go": r"golang|go",
    "R": r"r",
    "SQL": r"sql",
}

# Tên được quan sát trong hai nguồn mới; chỉ gom alias của cùng khái niệm.
TECHNOLOGIES = {
    "Flutter": r"flutter",
    "Unity": r"unity(?:3d)?",
    "React": r"react(?:\.?js)?",
    "Vue.js": r"vue(?:\.?js)?",
    "Angular": r"angular(?!js)",
    "AngularJS": r"angularjs",
    "Node.js": r"node\.?js",
    "Next.js": r"next\.?js",
    ".NET": r"\.net|dotnet",
    "ASP.NET": r"asp\.net",
    "Spring Boot": r"spring\s*boot",
    "Django": r"django",
    "Flask": r"flask",
    "FastAPI": r"fastapi",
    "Laravel": r"laravel",
    "MySQL": r"mysql",
    "PostgreSQL": r"postgres(?:ql)?",
    "MongoDB": r"mongodb",
    "Redis": r"redis",
    "SQL Server": r"sql\s*server|mssql",
    "Oracle": r"oracle",
    "AWS": r"aws|amazon web services",
    "Azure": r"azure",
    "GCP": r"gcp|google cloud(?: platform)?",
    "Docker": r"docker",
    "Kubernetes": r"kubernetes|k8s",
}


def _technical_context(text: str, match: re.Match) -> bool:
    before = text[: match.start()]
    after = text[match.end() :]
    if match.group().lower() == "sql":
        query_language = re.match(
            r"\s+(?:developer|programming|queries|query|joins?)\b", after, re.I
        ) or re.search(r"\b(?:lập trình|query|queries)\b.{0,30}$", before, re.I)
        return bool(
            query_language
            or not re.search(
                r"sales[ -]qualified|leads?|marketing|khách hàng tiềm năng", text, re.I
            )
        )
    if match.group().lower() == "r" and re.match(r"\s*&\s*d\b", after, re.I):
        return False
    if match.group().lower() == "go" and re.match(
        r"\s+(?:to|home|live|ahead|out|on|back|through)\b", after, re.I
    ):
        return False
    if match.group().lower() == "golang":
        return True
    opening = text.rfind("(", 0, match.start())
    closing = text.find(")", match.end())
    if (
        opening >= 0
        and closing >= 0
        and re.search(r"developer|engineer|lập trình", text[:opening], re.I)
    ):
        parts = re.split(r"[,/]", text[opening + 1 : closing])
        if len(parts) > 1 and all(
            re.fullmatch("(?:" + "|".join(LANGUAGES.values()) + ")", part.strip(), re.I)
            for part in parts
        ):
            return True
    language_list = all(
        re.fullmatch(r"(?:" + "|".join(LANGUAGES.values()) + r")", part.strip(), re.I)
        for part in re.split(r"[,/]", text)
    )
    return bool(
        re.search(
            r"\b(?:programming|language|code|coding|develop|services|experience|use|using|"
            r"knowledge|skills|proficient|lập trình|ngôn ngữ|kinh nghiệm|sử dụng|thành thạo)"
            r"\b[^.!?;\n]{0,45}$",
            before,
            re.I,
        )
        or re.match(r"\s+(?:developer|engineer|programmer|programming|language)\b", after, re.I)
        or text.strip() == match.group()
        and match.group() not in {"go", "r"}
        or language_list
        and len(re.split(r"[,/]", text)) > 1
    )


def _incidental_mention(skill: str, text: str, match: re.Match) -> bool:
    if skill not in {"Swift", "PHP"}:
        return False
    # Bằng chứng lập trình cục bộ được ưu tiên hơn lĩnh vực tài chính của sản phẩm.
    context = text[max(0, match.start() - 65) : match.end() + 65]
    before = text[max(0, match.start() - 65) : match.start()]
    programming = _technical_context(text, match) or re.search(
        r"\b(?:iOS|developer|lập trình viên)\b[^;.!?]{0,45}$", before, re.I
    )
    if skill == "Swift":
        return bool(
            not programming
            and re.search(
                r"payments?|banking|bank|transfers?|messaging|thanh toán|chuyển tiền", context, re.I
            )
        )
    if skill == "PHP":
        return bool(not programming and re.search(r"currency|pesos?|tiền tệ", context, re.I))
    return False


def extract_languages(title: str, description: str = "", requirements: str = "") -> dict:
    skills = []
    evidence = []
    for field, value in (
        ("title", title),
        ("description", description),
        ("requirements", requirements),
    ):
        seen = set()
        for text in re.split(r"(?<=[.!?])\s+|\n+", value):
            matches = []
            for skill, alias in (LANGUAGES | TECHNOLOGIES).items():
                for match in re.finditer(
                    rf"(?<![\w\u0300-\u036f-])(?:{alias})(?![\w\u0300-\u036f+#-])", text, re.I
                ):
                    if not _incidental_mention(skill, text, match) and (
                        skill not in {"C", "Go", "R", "SQL"} or _technical_context(text, match)
                    ):
                        matches.append((match.start(), skill))
                        break
            for _, skill in sorted(matches):
                if skill not in skills:
                    skills.append(skill)
                if skill not in seen:
                    evidence.append({"skill": skill, "field": field, "text": text})
                    seen.add(skill)
    reason = (
        "Có bằng chứng kỹ năng công nghệ trong tin."
        if skills
        else "Không tìm thấy bằng chứng kỹ năng trong danh mục đã xác minh."
    )
    if not description.strip() and not requirements.strip():
        reason += " Thiếu JD/yêu cầu: chỉ xét tiêu đề."
    return {
        "skills": skills,
        "skill_evidence": evidence,
        "skills_reason": reason,
    }
