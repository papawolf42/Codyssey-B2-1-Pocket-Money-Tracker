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

texts = json.dumps(data)
print(texts)
print(type(texts))

obj = json.loads(texts)
print(type(obj))