import pytest

from app.categorizer import categorize


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Хочу записатися на процедуру наступного тижня", "booking"),
        ("Можно записаться на завтра?", "booking"),
        ("Скільки коштує манікюр?", "price"),
        ("Какая цена на стрижку?", "price"),
        ("Хочу залишити скаргу", "complaint"),
        ("Привіт!", "other"),
    ],
)
def test_categorize(message, expected):
    assert categorize(message) == expected


def test_case_insensitive():
    assert categorize("ХОЧУ ЗАПИСАТИСЯ") == "booking"


def test_complaint_has_priority_over_booking():
    assert categorize("Записалась минулого разу, було погано") == "complaint"
