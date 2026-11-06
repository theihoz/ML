"""Luật gán nhãn sửa theo kết quả duyệt mẫu #79 (ticket #98); ví dụ lấy từ mẫu duyệt."""

import pytest

from career_market.salary_dataset import classify_role, derive_level, extract_skills


@pytest.mark.parametrize(
    "title",
    [
        "MERN Stack Developer",
        "MEAN Stack Developer",
        "Middle Fullstack Developer (PHP/Laravel)",
    ],
)
def test_mern_and_mean_stacks_are_fullstack(title):
    assert classify_role(title) == "Fullstack Developer"


@pytest.mark.parametrize(
    "title",
    [
        "Nhan Vien Tu Van Sale Online Cham Soc Khach Hang Game Thu Nhap Hap Dan",
        "Chuyên Viên Pháp Chế & Tuân Thủ (Mảng Tech/ Game)",
        "Chỉ Huy Trưởng Dự Án/ Kỹ Sư Quản Lý Dự Án - Thu Nhập Upto 30 Triệu ++",
        "Nhân Viên Lập Trình & Vận Hành Phay CNC",
        "2D Game Artist (Casual/ Puzzle) - Junior (Nghỉ Thứ 7 Chủ Nhật)",
    ],
)
def test_non_it_postings_are_excluded(title):
    assert classify_role(title) is None


@pytest.mark.parametrize(
    "title",
    [
        "Unity Game Developer (Từ 3 Năm Kinh Nghiệm)",
        "Tư Vấn Triển Khai ERP",
        "Scrum Master",
        "Senior AI Engineer (Rag / LLM) Building Vietnam Legal AI Platform",
        "Salesforce Developer",
    ],
)
def test_it_postings_near_the_new_exclusions_are_kept(title):
    assert classify_role(title) is not None


@pytest.mark.parametrize(
    ("title", "years", "source_level", "level"),
    [
        ("Senior Embedded Engineer", 7, "Trưởng nhóm", "Senior"),
        ("Senior Vue.js Developer", 6, "Trưởng nhóm", "Senior"),
        ("Technical Lead (Kotlin/ Java/ Spring Ecosystem)", 5, "Trưởng phòng", "Lead"),
        ("Junior Full-stack Engineer", 2, "Intern", "Junior"),
        ("2D Game Artist - Junior", 1, "Mới Tốt Nghiệp", "Junior"),
        ("Senior Product Manager", 6, "Nhân viên", "Senior"),
        ("Product Manager", 3, "", "Middle"),
        ("Product Owner", 2, "Nhân viên", "Junior"),
        ("Engineering Manager", 8, "Trưởng nhóm", "Manager"),
        ("QA Engineer", 2, "Intern", "Junior"),
        ("Android Developer", 0, "Intern", "Intern"),
        ("Data Analyst Intern", 1, "Nhân viên", "Intern"),
    ],
)
def test_level_prefers_the_title_and_ignores_product_manager(title, years, source_level, level):
    assert derive_level(title, years, source_level) == level


@pytest.mark.parametrize(
    "text",
    [
        "QA Tester Selenium API Testing TestNG",
        "AI Engineer PyTorch MLflow OpenAI API Vector Database",
        "AI Engineering Manager MLflow Python Airflow LLM API SQL",
        "Experience in conducting API Automation testing.",
    ],
)
def test_api_testing_and_llm_apis_are_not_rest_api(text):
    assert "REST API" not in extract_skills(text)


@pytest.mark.parametrize(
    "text", ["Thiết kế RESTful API", "REST API, GraphQL", "Xây dựng API cho mobile"]
)
def test_real_api_work_is_still_rest_api(text):
    assert "REST API" in extract_skills(text)


def test_language_mentioned_only_as_a_benefit_is_not_a_requirement():
    benefit = "Phúc lợi: trợ cấp ngoại ngữ (với ứng viên có chứng chỉ tiếng Nhật N3 trở lên)"
    assert "Tiếng Nhật" not in extract_skills(benefit)
    assert "Tiếng Nhật" in extract_skills("Yêu cầu: tiếng Nhật N2 trở lên")
