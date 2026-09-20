from dataclasses import dataclass, field, asdict
from typing import Generator
import os
import json

@dataclass
class Transaction:
    id: str
    type: str
    date: str
    category: str
    amount: int

    memo: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class TransactionRepository:
    def __init__(self, file_path: str = "./data/transactions.jsonl"):
        self.file_path = file_path

    def get_all(self) -> Generator[Transaction, None, None]:
        """파일을 한 줄씩 읽어 Tranaction 객체로 yield하는 스트리밍 메서드"""

        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                obj = json.loads(line)
                yield Transaction.from_dict(obj)

repo = TransactionRepository()
for i, tx in enumerate(repo.get_all(), 1):
    print(tx)
    # print(f"[{tx.date}] {tx.category} : {tx.amount}원 ({tx.memo})")
    if i == 2:
        break