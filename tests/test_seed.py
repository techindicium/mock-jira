import pytest

from app.seed import SEED_ISSUES, SEED_PROJECT, SeedError, _validate_seed_data

_CANON_ASSIST_NAMES = {"Mei Tan", "Kofi Adjei", "Priya Nair", "Joao Pinto"}


def test_seed_project_key_and_name_are_not_placeholder_text():
    assert SEED_PROJECT["key"] == "ASSIST"
    assert SEED_PROJECT["name"] == "Portwell Assist Engineering"
    assert "lorem" not in SEED_PROJECT["description"].lower()


def test_seed_issues_use_real_canon_names():
    for issue in SEED_ISSUES:
        assert issue["assignee"] in _CANON_ASSIST_NAMES
        assert issue["reporter"] in _CANON_ASSIST_NAMES


def test_validate_seed_data_passes_for_shipped_fixture():
    _validate_seed_data(SEED_PROJECT, SEED_ISSUES)  # must not raise


def test_validate_seed_data_rejects_canon_reserved_key_prefix():
    bad_project = {**SEED_PROJECT, "key": "ACCOUNT-1"}
    with pytest.raises(SeedError) as exc_info:
        _validate_seed_data(bad_project, SEED_ISSUES)
    assert exc_info.value.code == "SEED_DATA_INVALID"


def test_validate_seed_data_rejects_invalid_status():
    bad_issues = [dict(SEED_ISSUES[0], status="blocked")] + SEED_ISSUES[1:]
    with pytest.raises(SeedError) as exc_info:
        _validate_seed_data(SEED_PROJECT, bad_issues)
    assert exc_info.value.code == "SEED_DATA_INVALID"
