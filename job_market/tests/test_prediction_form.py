"""Demo flow through the main Streamlit entry and saved salary model."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_prediction_is_home_and_both_cities_use_real_model():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
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
    app.selectbox(key="salary_role").select("Backend")
    app.button[0].click().run()
    assert not app.exception
    assert not app.metric
    assert "chưa đủ dữ liệu" in app.info[0].value


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
