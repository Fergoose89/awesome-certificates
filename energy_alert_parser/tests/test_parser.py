from pathlib import Path

from parser import AlertParser


BASE = Path(__file__).resolve().parents[1]
RULES = BASE / "rules.json"
SAMPLES = BASE / "samples"


def test_parse_format_a_text():
    parser = AlertParser(RULES)
    text = (SAMPLES / "alert_format_a.txt").read_text(encoding="utf-8")

    record = parser.parse_text(
        text,
        source_subject="Alert - Overconsumption at Site ALP102",
        source_date="Tue, 25 Mar 2026 07:15:00 +0000",
    )

    assert record.site_code == "ALP102"
    assert record.site_name == "Alpha Retail Park"
    assert record.mpan_or_mprn == "12 3456 7890 123"
    assert record.issue_type == "Overconsumption"
    assert record.first_observed_date == "2026-03-24"
    assert record.daily_cost == 145.90
    assert record.rank == "3"
    assert record.needs_review is False


def test_parse_format_b_text_with_variations():
    parser = AlertParser(RULES)
    text = (SAMPLES / "alert_format_b.txt").read_text(encoding="utf-8")

    record = parser.parse_text(
        text,
        source_subject="Meter offline warning - BRV77",
        source_date="Wed, 26 Mar 2026 09:45:00 +0000",
    )

    assert record.site_code == "BRV77"
    assert record.site_name == "Bravo Distribution Hub"
    assert record.mpan_or_mprn == "998877665544"
    assert record.issue_type == "Meter offline"
    assert record.first_observed_date == "2026-03-25"
    assert record.daily_cost == 38.50
    assert record.rank == "P2"


def test_parse_eml_file():
    parser = AlertParser(RULES)
    record = parser.parse_eml(SAMPLES / "alert_email.eml")

    assert record.site_code == "CEN55"
    assert record.issue_type == "Energy spike"
    assert record.daily_cost == 210.0
    assert record.source_email_subject == "Energy spike detected at CEN55"


def test_low_confidence_is_flagged():
    parser = AlertParser(RULES)
    text = "Site Name: Unknown Site\nSomething happened."
    record = parser.parse_text(text)

    assert record.needs_review is True
    assert record.confidence < 0.75
