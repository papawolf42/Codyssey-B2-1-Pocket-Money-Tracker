from dataclasses import dataclass, field, asdict
from datetime import datetime


def validate_date(date_str: str) -> str:
    date_str = date_str.strip()
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"날짜 형식이 올바르지 않습니다: '{date_str}' (예: 2026-03-20)")


def validate_amount(amount_input) -> int:
    try:
        val = int(amount_input)
    except (ValueError, TypeError):
        raise ValueError(f"금액은 숫자여야 합니다: '{amount_input}'")

    if val <= 0:
        raise ValueError(f"금액은 0보다 큰 양수여야 합니다: {val}")
    return val


def validate_type(type_str: str) -> str:
    t = type_str.strip().lower()
    if t not in ("income", "expense"):
        raise ValueError(f"거래 타입은 'income' 또는 'expense'여야 합니다: '{type_str}'")
    return t


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.type = validate_type(self.type)
        self.date = validate_date(self.date)
        self.amount = validate_amount(self.amount)
        self.category = self.category.strip()
        if not self.category:
            raise ValueError("카테고리는 비어 있을 수 없습니다.")
        self.memo = self.memo.strip()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        raw_tags = data.get("tags") or []
        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        else:
            tags = list(raw_tags)

        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            date=str(data["date"]),
            category=str(data["category"]),
            amount=int(data["amount"]),
            memo=str(data.get("memo", "")),
            tags=tags,
        )
