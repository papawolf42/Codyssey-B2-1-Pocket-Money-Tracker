from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class Transaction:
    id: str
    type: str
    date: str
    category: str
    amount: int

    # 기본값을 안주면 필수, 주면 선택
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.date = self.validate_date_lib(self.date)
        self.type = self.validate_type(self.type)
        self.amount = self.validate_amount(self.amount)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data:dict):
        return(cls(**data))

    def validate_date_own(self, date_str: str) -> str:
        """날짜 형식 (YYYY-MM-DD) 검증"""
        parts = date_str.split('-')
        if len(parts) != 3:
            raise ValueError("split했는데 3조각이 아니야!")

        if not (1 <= int(parts[0]) <= 2026):
            raise ValueError("년도를 제대로 입력해주세요")
        elif not (1 <= int(parts[1]) <= 12):
            raise ValueError("달을 제대로 입력해주세요")
        elif not (1 <= int(parts[2]) <= 31):
            raise ValueError("일을 제대로 입력해주세요")

        return date_str
        
    def validate_date_lib(self, date_str: str) -> str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except:
            raise ValueError("형식에 맞지 않습니다!") from None
        return date_str

    def validate_amount(self, amount: int) -> int:
        if not isinstance(amount, int): 
            raise ValueError("amount는 정수여야 합니다.")

        if amount <= 0:
            raise ValueError("amount는 양수여야 합니다.") 

        return amount

    def validate_type(self, type: str) -> str:
        type = type.lower()
        if not (type in ["income", "expense"]):
            raise ValueError("type은 income이나 expence여야 합니다.")

        return type


        
tx1 = Transaction(
    id = "000001",
    type = "expense",
    date = "2026-09-19",
    category = "food",
    amount = 12000,
    memo = "가물치 물회"
)

print(tx1)
