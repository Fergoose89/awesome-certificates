"""Integration placeholders for future data collection upgrades.

Add concrete implementations here when moving beyond static URL/file ingestion.
"""


def collect_with_browser_automation(council: str, operators: list[str]) -> list[dict]:
    """TODO: integrate Playwright/Selenium for JS-heavy portals.

    Candidate targets:
    - dynamic planning portals
    - document libraries behind filters/search forms
    """
    return []


def collect_from_find_a_tender_api(query: str) -> list[dict]:
    """TODO: integrate Find a Tender API or structured feed endpoint."""
    return []


def collect_from_council_open_data_api(council_slug: str) -> list[dict]:
    """TODO: integrate council-specific CKAN/Socrata/open-data APIs."""
    return []
