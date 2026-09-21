import os
import json
import csv
from typing import Generator
from .models import Transaction, Budget

CSV_HEADERS = ["date", "type", "category", "amount", "memo", "tags"]

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


def write_csv(file_path: str, rows) -> int:
    temp_file = file_path + ".tmp"
    os.makedirs(os.path.dirname(os.path.abspath(file_path)) or ".", exist_ok=True)
    count = 0
    with open(temp_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    atomic_replace(temp_file, file_path)
    return count


def read_csv(file_path: str) -> Generator[dict, None, None]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return
        fieldnames = [fn.strip() if fn else "" for fn in reader.fieldnames]
        required_cols = {"date", "type", "category", "amount"}
        if not required_cols.issubset(set(fieldnames)):
            missing = required_cols - set(fieldnames)
            raise ValueError(f"CSV 헤더가 올바르지 않습니다. 필수 컬럼이 누락되었습니다: {missing}")
        for raw_row in reader:
            if not any(raw_row.values()):
                continue
            row = {}
            for k, v in raw_row.items():
                if k is not None:
                    clean_k = k.strip()
                    clean_v = v.strip() if isinstance(v, str) else v
                    row[clean_k] = clean_v
            yield row


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

    def get_max_id_num(self) -> int:
        max_num = 0
        for tx in self.get_all():
            if tx.id.startswith("TX-"):
                try:
                    num = int(tx.id.split("-")[1])
                    if num > max_num:
                        max_num = num
                except ValueError:  # "TX-abc"처럼 숫자가 아니면 무시
                    pass
        return max_num

    def get_next_id(self) -> str:
        return f"TX-{self.get_max_id_num() + 1:06d}"

    def insert_batch(self, new_txs: list[Transaction]) -> None:
        if not new_txs:
            return
        all_txs = list(self.get_all()) + new_txs
        all_txs.sort(key=lambda t: t.id)
        all_txs.sort(key=lambda t: t.date, reverse=True)
        write_jsonl(self.file_path, all_txs)

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
            if category and tx.category.lower() != category.lower():
                continue
            if tx_type and tx.type != tx_type:
                continue
            if date_from and tx.date < date_from:
                continue
            if date_to and tx.date > date_to:
                continue
            if keyword and keyword.lower() not in tx.memo.lower():
                continue
            if tag and tag.lower() not in [t.lower() for t in tx.tags]:
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

    def add(self, name: str) -> None:
        categories = self.get_all()
        categories.append(name.strip())
        write_jsonl(self.file_path, [{"name": c} for c in categories])

    def remove(self, name: str) -> bool:
        target = name.strip().lower()
        current_cats = self.get_all()
        remaining = [c for c in current_cats if c.lower() != target]
        if len(remaining) == len(current_cats):
            return False
        write_jsonl(self.file_path, [{"name": c} for c in remaining])
        return True


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



