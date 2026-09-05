import os


def get_api_base_url() -> str:
    value = os.environ.get("API_BASE_URL")
    if not value:
        raise RuntimeError(
            "API_BASE_URL environment variable is required to reach issue-tracker-api"
        )
    return value
