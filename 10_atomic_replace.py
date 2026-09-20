import os
import json

# [1] 사용자분이 직접 작성하신 최신순 비교 함수
def is_newer(tx_a: dict, tx_b: dict) -> dict:
    if tx_a["date"] > tx_b["date"]:
        return tx_a
    elif tx_a["date"] < tx_b["date"]:
        return tx_b
    else:
        if tx_a["id"] < tx_b["id"]:
            return tx_a
        else:
            return tx_b

# ----------------------------------------------------------------------
# [2] 기존 파일(data/transactions.jsonl)을 활용한 os.replace 실습 스켈레톤
# ----------------------------------------------------------------------
target_file = "./data/transactions.jsonl"
temp_file = target_file + ".tmp"

print("=== 1. 교체 전 원본 첫 번째 줄 ===")
with open(target_file, "r", encoding="utf-8") as f:
    first_line = f.readline().strip()
    print(" ", first_line)

# [TODO 1] 원본(src)에서 한 줄씩 읽어와서,
#          메모(memo) 뒤에 ' [확인]'을 덧붙인 뒤 임시 파일(dst)에 써보세요.

with open(target_file, "r", encoding="utf-8") as src, \
     open(temp_file, "w", encoding="utf-8") as dst:
    for line in src:
        tx = json.loads(line)
        # TODO: tx["memo"] 수정 후 dst.write()로 json 문자열 + "\n" 기록하기
        tx["memo"] += "[확인]"
        dst.write(json.dumps(tx, ensure_ascii=False) + "\n")

# [TODO 2] os.replace()를 한 줄 호출하여 temp_file로 target_file을 원자적 교체해 보세요.
# TODO: os.replace(..., ...)
os.replace(temp_file, target_file)

print("\n=== 2. 교체 후 원본 첫 번째 줄 확인 ===")
with open(target_file, "r", encoding="utf-8") as f:
    print(" ", f.readline().strip())

print("\n임시 파일(.tmp)이 자동으로 사라졌나요?", not os.path.exists(temp_file))
