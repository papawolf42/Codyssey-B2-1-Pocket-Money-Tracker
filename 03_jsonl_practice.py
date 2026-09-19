import json

data = {
    "id": "000001",
    "type": "expense",
    "date": "2026-09-19",
    "category": "food",
    "amount": 12000,
    "memo": "가물치 물회",
    "tags": ["식비", "외식"]
}

line = json.dumps(data, ensure_ascii=False)

with open("03_jsons_practice.jsonl", "a", encoding="utf-8") as f:
    f.write(line + "\n")

with open("03_jsons_practice.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        tx = json.loads(line)
        print(tx)