"""Demo flow through the main Streamlit entry and saved salary model."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_pilot_prediction_page_and_both_cities_use_real_model():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    app.switch_page("pages/predict.py").run()
    assert not app.exception
    assert app.title[0].value == "Dự đoán lương"
    assert not app.text_input
    app.button[0].click().run()
    assert not app.exception
    first = app.metric[0].value
    assert float(first) > 0
    app.selectbox(key="salary_city").select("HCM")
    app.button[0].click().run()
    assert not app.exception
    assert float(app.metric[0].value) > 0
    assert app.metric[0].value != first
    hcm_salary = app.metric[0].value
    app.switch_page("pages/models.py").run()
    app.switch_page("pages/predict.py").run()
    assert app.selectbox(key="salary_city").value == "HCM"
    assert app.metric[0].value == hcm_salary
    assert not app.json
    assert len(app.get("image")) == 1
    app.selectbox(key="salary_role").select("Backend")
    app.button[0].click().run()
    assert not app.exception
    assert float(app.metric[0].value) > 0
    assert not app.info
    app.selectbox(key="salary_city").select("Đà Nẵng")
    app.button[0].click().run()
    assert not app.exception
    assert float(app.metric[0].value) > 0
    assert not any("Trung bình theo thành phố" in caption.value for caption in app.caption)


def test_data_page_distinguishes_fit_and_held_out_labels():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    app.switch_page("pages/data.py").run()
    assert not app.exception
    table = app.dataframe[0].value
    assert len(table) == 14
    assert table["Mục đích"].value_counts().to_dict() == {
        "Học": 10,
        "Chọn mô hình": 2,
        "Kiểm tra": 2,
    }
    assert "Trung điểm lương (triệu/tháng)" in table.columns


def test_manual_model_switching_updates_prediction_and_comparison():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=40).run()
    app.switch_page("pages/predict.py").run()
    app.button[0].click().run()
    ridge = app.metric[0].value
    app.selectbox(key="salary_model").select("LinearRegression")
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value != ridge
    assert any("LinearRegression" in caption.value for caption in app.caption)
    app.switch_page("pages/models.py").run()
    app.selectbox(key="compare_model").select("LinearRegression").run()
    assert app.metric[0].value == "LinearRegression"
    assert app.metric[1].value == "17.58"
    app.radio(key="compare_part").set_value("validation").run()
    assert app.metric[1].value == "13.58"
    app.button[0].click().run()
    assert not app.exception
    assert app.title[0].value == "Dự đoán lương"
    assert app.selectbox(key="salary_model").value == "LinearRegression"


def test_overview_shows_every_role_and_links_to_advisor():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=60).run()
    app.switch_page("pages/overview.py").run(timeout=60)
    assert not app.exception
    assert app.title[0].value == "Tổng quan thị trường việc làm"
    assert len(app.metric) == 3
    assert app.metric[1].value == "23"
    assert len(app.get("image")) == 6
    assert any("23 vai trò" in header.value for header in app.subheader)
    app.button[0].click().run()
    assert not app.exception
    assert app.title[0].value == "Tư vấn & dự đoán lương"
