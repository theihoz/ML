"""Small synthetic postings for logic tests only; never market/training data."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from career_market import MarketService


def test_explicit_backend_title_returns_role_and_verbatim_evidence():
    result = MarketService().classify_role("Senior BACK-END Developer")
    assert result == {
        "role": "Backend",
        "role_status": "matched",
        "role_evidence": [{"field": "title", "text": "BACK-END"}],
        "role_reason": "Có bằng chứng cho Backend từ chức danh hoặc nhiệm vụ.",
    }


@pytest.mark.parametrize(
    ("title", "role"),
    [
        ("Front End Engineer", "Frontend"),
        ("Lập trình viên Full-stack", "Fullstack"),
        ("Mobile Developer", "Mobile"),
        ("Android Developer", "Mobile"),
        ("iOS Engineer", "Mobile"),
        ("Flutter Developer", "Mobile"),
    ],
)
def test_explicit_software_roles_remain_distinct(title, role):
    result = MarketService().classify_role(title)
    assert (result["role"], result["role_status"]) == (role, "matched")
    assert result["role_evidence"][0]["text"] in title


@pytest.mark.parametrize(
    "title",
    ["Java Developer", ".NET Developer", "PHP Developer", "Software Developer", "Lập trình viên"],
)
def test_generic_developer_needs_review_without_responsibility_evidence(title):
    result = MarketService().classify_role(title, requirements="Java, SQL, React, Flutter")
    assert (result["role"], result["role_status"]) == (None, "review")
    assert result["role_evidence"] == []


@pytest.mark.parametrize(
    "title",
    [
        "CNC Programmer",
        "PLC Software Engineer",
        "Hardware Engineer",
        "Customer Sales Mobile",
        "Knitwear Developer",
        "Fullstack Marketing",
        "Nhân viên Marketing Full-stack",
        "Kỹ sư lập trình PLC",
        "Android Sales Consultant",
    ],
)
def test_non_software_occupations_are_out_of_scope_despite_role_words(title):
    result = MarketService().classify_role(title, requirements="Backend, frontend, Flutter")
    assert (result["role"], result["role_status"]) == (None, "out_of_scope")
    assert result["role_evidence"][0]["text"] in title


def test_backend_responsibilities_resolve_java_without_using_required_skills():
    description = "Thiết kế và phát triển REST API cho dịch vụ máy chủ."
    result = MarketService().classify_role(
        "Java Developer", description, requirements="Biết thêm Frontend, Android là lợi thế."
    )
    assert (result["role"], result["role_status"]) == ("Backend", "matched")
    assert result["role_evidence"] == [{"field": "description", "text": description}]


@pytest.mark.parametrize(
    ("description", "role"),
    [
        ("Develop user interfaces for web applications.", "Frontend"),
        ("Xây dựng giao diện web cho người dùng.", "Frontend"),
        ("Build Android applications for customers.", "Mobile"),
        ("Phát triển ứng dụng iOS.", "Mobile"),
        ("Develop full-stack web applications.", "Fullstack"),
    ],
)
def test_job_tasks_can_identify_each_role_without_language_guessing(description, role):
    result = MarketService().classify_role("Software Developer", description)
    assert (result["role"], result["role_status"]) == (role, "matched")
    assert result["role_evidence"] == [{"field": "description", "text": description}]


@pytest.mark.parametrize(
    ("title", "description"),
    [
        ("Backend / Frontend Developer", ""),
        ("Fullstack / Mobile Engineer", ""),
        ("Backend Developer", "Develop Android applications."),
        ("Software Engineer", "Build REST APIs. Develop user interfaces."),
    ],
)
def test_intersecting_actual_roles_are_reviewed_instead_of_first_match(title, description):
    result = MarketService().classify_role(title, description)
    assert (result["role"], result["role_status"]) == (None, "review")
    assert len(result["role_evidence"]) == 2
    assert "nhiều vai trò" in result["role_reason"]


def test_long_jd_skills_and_collaborators_do_not_create_competing_roles():
    description = (
        "Develop REST APIs.\n"
        "Work with frontend and mobile developers.\n"
        "Requirements:\nAbility to develop Android and frontend applications is a plus.\n"
        "Kỹ năng: Fullstack, Flutter, SQL."
    )
    result = MarketService().classify_role("Backend Developer", description)
    assert (result["role"], result["role_status"]) == ("Backend", "matched")
    assert result["role_evidence"] == [
        {"field": "title", "text": "Backend"},
        {"field": "description", "text": "Develop REST APIs."},
    ]


@pytest.mark.parametrize(
    "description",
    [
        "Experience to develop Android applications is preferred.",
        "Knowledge of how to build REST APIs and frontend is a plus.",
        "Work with frontend developers to build REST APIs.",
    ],
)
def test_only_assigned_tasks_not_experience_or_collaborators_are_evidence(description):
    result = MarketService().classify_role("Backend Developer", description)
    assert (result["role"], result["role_status"]) == ("Backend", "matched")


def test_vague_fullstack_marketing_tasks_do_not_become_software_work():
    result = MarketService().classify_role("Specialist", "Develop fullstack marketing campaigns.")
    assert (result["role"], result["role_status"]) == (None, "out_of_scope")


@pytest.mark.parametrize(
    "description",
    [
        "Nhiệm vụ\nPhát triển REST API.\nYêu cầu công việc\nPhát triển Android là lợi thế.",
        "<p>Develop REST APIs.</p><h3>Requirements</h3><p>Develop Android apps.</p>",
    ],
)
def test_requirements_sections_in_plain_and_html_jd_do_not_supply_roles(description):
    result = MarketService().classify_role("Software Developer", description)
    assert (result["role"], result["role_status"]) == ("Backend", "matched")
    for item in result["role_evidence"]:
        assert item["text"] in description


def test_role_page_shows_raw_evidence_filters_and_csv_download():
    # UI smoke uses only the newly approved T01 sources, never legacy data.
    page = Path(__file__).parents[1] / "pages/tools/roles.py"
    app = AppTest.from_file(str(page), default_timeout=30).run()
    assert not app.exception
    table = app.dataframe[0].value
    assert {"raw_title", "role", "role_evidence", "role_status", "role_reason"} <= set(table)
    assert table.iloc[0]["raw_title"] == "Performance Marketing"
    assert table.iloc[0]["role_status"] == "out_of_scope"
    app.selectbox(key="role_filter").select("Backend").run()
    assert not app.exception
    filtered = app.dataframe[0].value
    assert len(filtered) > 0
    assert set(filtered["role"]) == {"Backend"}
    assert set(filtered["role_status"]) == {"matched"}
    assert app.get("download_button")[0].proto.url


def test_fullstack_responsibilities_include_frontend_and_backend():
    result = MarketService().classify_role(
        "Fullstack Developer", "Develop REST APIs.\nDevelop user interfaces."
    )
    assert (result["role"], result["role_status"]) == ("Fullstack", "matched")


@pytest.mark.parametrize(
    ("title", "role"),
    [
        ("Data Engineer", "Data/ML"),
        ("Machine Learning Developer", "Data/ML"),
        ("Lập Trình Viên AI", "Data/ML"),
        ("Senior DevOps Engineer", "DevOps"),
        ("Site Reliability Engineer", "DevOps"),
        ("Software Tester (Manual & Automation)", "QA Automation"),
        ("Intern Automation Test", "QA Automation"),
    ],
)
def test_specialized_roles_need_explicit_occupational_evidence(title, role):
    result = MarketService().classify_role(title)
    assert (result["role"], result["role_status"]) == (role, "matched")
    assert result["role_evidence"][0]["text"] in title


def test_canonical_data_ml_role_matches_the_profile_and_dataset_rules():
    result = MarketService().classify_role("Data/ML")
    assert (result["role"], result["role_status"]) == ("Data/ML", "matched")
