from dataclasses import dataclass, field, asdict

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

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data:dict):
        return(cls(**data))
        
tx1 = Transaction(
    id = "000001",
    type = "expense",
    date = "2026-09-19",
    category = "food",
    amount = 12000,
    memo = "가물치 물회"
)

print(tx1)