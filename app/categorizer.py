"""Rule-based lead categorization.

Stand-in for an LLM classifier: same interface (text in, category out),
so it can be swapped later without touching the rest of the service.
"""

# Order matters: the first matching category wins.
# Complaint goes first so "I booked and it was bad" is a complaint, not a booking.
RULES: list[tuple[str, tuple[str, ...]]] = [
    ("complaint", ("скарг", "жалоб", "незадоволен", "недоволен", "погано", "complaint")),
    ("booking", ("запис", "бронь", "заброн", "book", "appointment")),
    ("price", ("ціна", "ціни", "вартіст", "скільки кошту", "цена", "стоимост", "сколько стоит", "price")),
]

DEFAULT_CATEGORY = "other"


def categorize(message: str) -> str:
    text = message.lower()
    for category, keywords in RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return DEFAULT_CATEGORY
