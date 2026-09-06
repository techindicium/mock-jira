import subprocess
import sys


def test_bare_pytest_collection_excludes_tests_e2e():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        capture_output=True, text=True, cwd=".", check=False,
    )
    # Checked as a path prefix ("tests_e2e/"), not the bare substring "tests_e2e" --
    # this test's own name (test_bare_pytest_collection_excludes_tests_e2e) contains
    # that substring, which would make the assertion trip on its own collected name.
    assert "tests_e2e/" not in result.stdout
    assert "tests/test_projects.py" in result.stdout or "test_projects.py" in result.stdout
