import os
import json
from typing import Generator
from .models import Transaction, Budget

DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary"]
DEFAULT_TRANSACTIONS = [
    {"id": "TX-000001", "type": "expense", "date": "2026-03-20", "category": "food", "amount": 15000, "memo": "점심 순대국밥", "tags": ["lunch"]},
    {"id": "TX-000002", "type": "expense", "date": "2026-03-19", "category": "transport", "amount": 2500, "memo": "지하철", "tags": ["subway"]},
    {"id": "TX-000003", "type": "income", "date": "2026-03-18", "category": "salary", "amount": 3500000, "memo": "3월 급여", "tags": ["monthly"]},
]


def atomic_replace(temp_path: str, target_path: str) -> None:
    try:
        os.replace(temp_path, target_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


def read_jsonl(file_path: str) -> Generator[dict, None, None]:
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(file_path: str, items) -> None:
    temp_file = file_path + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        for item in items:
            data = item.to_dict() if hasattr(item, "to_dict") else item
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    atomic_replace(temp_file, file_path)


def init_file(file_path: str, default_items: list = None) -> None:
    if os.path.exists(file_path):
        return
    write_jsonl(file_path, default_items or [])


def init_storage(data_dir: str = "./data"):
    os.makedirs(data_dir, exist_ok=True)
    init_file(os.path.join(data_dir, "categories.jsonl"), [{"name": cat} for cat in DEFAULT_CATEGORIES])
    init_file(os.path.join(data_dir, "transactions.jsonl"), DEFAULT_TRANSACTIONS)
    init_file(os.path.join(data_dir, "budgets.jsonl"))


def is_newer(tx_a: dict, tx_b: dict) -> bool:
    if tx_a["date"] > tx_b["date"]:
        return True
    elif tx_a["date"] < tx_b["date"]:
        return False
    else:
        return tx_a["id"] < tx_b["id"]


class TransactionRepository:
    def __init__(self, file_path: str = "./data/transactions.jsonl"):
        self.file_path = file_path

    def get_all(self) -> Generator[Transaction, None, None]:
        for data in read_jsonl(self.file_path):
            yield Transaction.from_dict(data)

    def get_next_id(self) -> str:
        max_num = 0
        for tx in self.get_all():
            if tx.id.startswith("TX-"):
                try:
                    num = int(tx.id.split("-")[1])
                    if num > max_num:
                        max_num = num
                except ValueError:  # "TX-abc"처럼 숫자가 아니면 무시
                    pass
        return f"TX-{max_num + 1:06d}"  # :06d는 6자리 0 채우기 (예: 4 -> 000004)

    def insert_sorted(self, new_tx: Transaction) -> None:
        temp_file = self.file_path + ".tmp"
        new_dict = new_tx.to_dict()
        inserted = False

        os.makedirs(os.path.dirname(self.file_path) or ".", exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(new_dict, ensure_ascii=False) + "\n")
            atomic_replace(temp_file, self.file_path)
            return

        with open(self.file_path, "r", encoding="utf-8") as src, \
             open(temp_file, "w", encoding="utf-8") as dst:
            for line in src:
                line = line.strip()
                if not line:
                    continue
                existing_dict = json.loads(line)

                if not inserted and is_newer(new_dict, existing_dict):
                    dst.write(json.dumps(new_dict, ensure_ascii=False) + "\n")
                    inserted = True

                dst.write(json.dumps(existing_dict, ensure_ascii=False) + "\n")

            if not inserted:
                dst.write(json.dumps(new_dict, ensure_ascii=False) + "\n")
                inserted = True

        atomic_replace(temp_file, self.file_path)

    def search(
        self,
        category: str = None,
        tx_type: str = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        tag: str = None,
    ) -> Generator[Transaction, None, None]:
        for tx in self.get_all():
            if category and tx.category.lower() != category:
                continue
            if tx_type and tx.type != tx_type:
                continue
            if date_from and tx.date < date_from:
                continue
            if date_to and tx.date > date_to:
                continue
            if keyword and keyword.lower() not in tx.memo.lower():
                continue
            if tag and tag not in tx.tags:
                continue
            yield tx

    def delete(self, tx_id: str) -> bool:
        found = False
        remaining = []
        for tx in self.get_all():
            if tx.id == tx_id:
                found = True
            else:
                remaining.append(tx)

        if not found:
            return False

        write_jsonl(self.file_path, remaining)
        return True

    def get_by_id(self, tx_id: str) -> Transaction | None:
        for tx in self.get_all():
            if tx.id == tx_id:
                return tx
        return None

    def update(self, tx_id: str, updates: dict) -> Transaction:
        found = False
        all_txs = []
        updated_tx = None

        for tx in self.get_all():
            if tx.id == tx_id:
                found = True
                current_dict = tx.to_dict()
                current_dict.update(updates)
                updated_tx = Transaction.from_dict(current_dict)
                all_txs.append(updated_tx)
            else:
                all_txs.append(tx)

        if not found:
            raise ValueError(f"존재하지 않는 거래 ID입니다: '{tx_id}'. 'list' 명령어로 ID를 확인해 주세요.")

        all_txs.sort(key=lambda t: t.id)
        all_txs.sort(key=lambda t: t.date, reverse=True)

        write_jsonl(self.file_path, all_txs)
        return updated_tx


class CategoryRepository:
    def __init__(self, file_path: str = "./data/categories.jsonl"):
        self.file_path = file_path

    def get_all(self) -> list[str]:
        return [item["name"] for item in read_jsonl(self.file_path)]

    def is_registered(self, name: str) -> bool:
        target = name.strip().lower()
        for cat in self.get_all():
            if cat.lower() == target:
                return True
        return False


class BudgetRepository:
    def __init__(self, file_path: str = "./data/budgets.jsonl"):
        self.file_path = file_path

    def get_all(self) -> Generator[Budget, None, None]:
        for data in read_jsonl(self.file_path):
            yield Budget.from_dict(data)

    def get_budget(self, month: str) -> Budget | None:
        for b in self.get_all():
            if b.month == month:
                return b
        return None

    def set_budget(self, budget: Budget) -> None:
        budgets = [b for b in self.get_all() if b.month != budget.month]
        budgets.append(budget)
        write_jsonl(self.file_path, budgets)



