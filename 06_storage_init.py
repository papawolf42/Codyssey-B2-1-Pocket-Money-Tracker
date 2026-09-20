import os
import json

DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary"]

def init_storage(data_dir: str = "./data"):
    os.makedirs(data_dir, exist_ok=True)

    # - transactions.jsonl
    transcationPath = os.path.join(data_dir, "transactions.jsonl")
    if not os.path.exists(transcationPath):
        with open(transcationPath, "w", encoding="utf-8") as f:
            pass
                                                         
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