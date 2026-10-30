"""Normalization remains shared by CSV/Excel inspection tools."""

from career_market import MarketService


def test_single_and_csv_profiles_share_canonical_values():
    service = MarketService()
    profile = {
        "role": " backend ",
        "experience": "2–4 năm",
        "skills": "ReactJS; Python",
        "location": "ho chi minh | HN | Remote",
    }
    normalized = service.normalize_profile(profile)
    assert normalized["status"] == "valid"
    assert normalized["role"] == "Backend"
    assert (normalized["experience_min"], normalized["experience_max"]) == (2, 4)
    assert normalized["locations"] == ["HCM", "HN"]
    assert normalized["work_modes"] == ["Remote"]
    assert set(normalized["skills"]) == {"React", "Python"}
    content = "role,experience,skills,location\n backend ,2–4 năm,ReactJS; Python,ho chi minh | HN | Remote\n".encode()
    row = service.preview_profiles(content, {key: key for key in profile})["rows"][0]
    assert {key: row[key] for key in normalized} == normalized


def test_missing_zero_and_experience_bounds_remain_distinct():
    service = MarketService()
    for raw, low, high, kind, status in [
        ("", None, None, "missing", "invalid"),
        ("0", 0, 0, "exact", "valid"),
        ("trên 3 năm", 3, None, "greater_than", "valid"),
        ("dưới 2 năm", None, 2, "less_than", "valid"),
        ("-1", None, None, "exact", "invalid"),
        ("61", None, None, "exact", "invalid"),
    ]:
        result = service.normalize_profile({"role": "Data/ML", "experience": raw})
        assert result["status"] == status
        assert (result["experience_min"], result["experience_max"], result["experience_kind"]) == (
            low,
            high,
            kind,
        )


def test_invalid_shapes_and_values_return_errors():
    service = MarketService()
    for profile in [
        None,
        [],
        "Backend",
        {},
        {"role": None},
        {"role": ["Backend"], "experience": "2"},
        {"role": "Backend", "experience": "2", "skills": ["Python"]},
        {"role": "Backend", "experience": "2", "location": 42},
        {"role": "Backend", "experience": "2", "work_mode": "remote sensing"},
        {"role": "astronaut", "experience": "2"},
    ]:
        result = service.normalize_profile(profile)
        assert result["status"] == "invalid"
        assert result["errors"]
