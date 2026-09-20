import os
import json
from typing import Generator
from .models import Transaction

DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary"]


def init_storage(data_dir: str = "./data"):
    os.makedirs(data_dir, exist_ok=True)

    # 1. categories.jsonl (기본 카테고리 4개 등록)
    cat_path = os.path.join(data_dir, "categories.jsonl")
    if not os.path.exists(cat_path):
        with open(cat_path, "w", encoding="utf-8") as f:
            for cat in DEFAULT_CATEGORIES:
                f.write(json.dumps({"name": cat}, ensure_ascii=False) + "\n")

    # 2. transactions.jsonl (빈 파일 생성)
    tx_path = os.path.join(data_dir, "transactions.jsonl")
    if not os.path.exists(tx_path):
        with open(tx_path, "w", encoding="utf-8") as f:
            pass

    # 3. budgets.jsonl (빈 파일 생성)
    budgets_path = os.path.join(data_dir, "budgets.jsonl")
    if not os.path.exists(budgets_path):
        with open(budgets_path, "w", encoding="utf-8") as f:
            pass


class TransactionRepository:
    def __init__(self, file_path: str = "./data/transactions.jsonl"):
        self.file_path = file_path

    def get_all(self) -> Generator[Transaction, None, None]:
        if not os.path.exists(self.file_path):
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Transaction.from_dict(json.loads(line))
