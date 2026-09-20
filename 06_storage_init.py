import os
import json

DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary"]
DEFAULT_TRANSACTIONS = [
    {"id": "TX-000001", "type": "expense", "date": "2026-03-20", "category": "food", "amount": 15000, "memo": "점심 순대국밥", "tags": ["lunch"]},
    {"id": "TX-000002", "type": "expense", "date": "2026-03-19", "category": "transport", "amount": 2500, "memo": "지하철", "tags": ["subway"]},
    {"id": "TX-000003", "type": "income", "date": "2026-03-18", "category": "salary", "amount": 3500000, "memo": "3월 급여", "tags": ["monthly"]},
]

def init_storage(data_dir: str = "./data"):
    os.makedirs(data_dir, exist_ok=True)

    # - transactions.jsonl
    transcationPath = os.path.join(data_dir, "transactions.jsonl")
    if not os.path.exists(transcationPath):
        with open(transcationPath, "w", encoding="utf-8") as f:
            for tx in DEFAULT_TRANSACTIONS:
                line = json.dumps(tx)
                f.write(line + "\n")
                                                         
    # - budgets.jsonl
    budgetsPath = os.path.join(data_dir, "budgets.jsonl")
    if not os.path.exists(budgetsPath):
        with open(budgetsPath, "w", encoding="utf-8") as f:
            pass

    # - categories.jsonl (DEFAULT_CATEGORIES 기록)
    categoriesPath = os.path.join(data_dir, "categories.jsonl")
    if not os.path.exists(categoriesPath):
        with open(categoriesPath, "w", encoding="utf-8") as f:
            for category in DEFAULT_CATEGORIES:
                temp = {"name": category}
                line = json.dumps(temp)
                f.write(line + "\n")

init_storage("./data")