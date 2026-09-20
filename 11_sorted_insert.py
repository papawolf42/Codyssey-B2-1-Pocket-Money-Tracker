import os
import json
from dataclasses import dataclass, field, asdict
from typing import Generator

# ==========================================
# [기존 코드 1] 04/09에서 만든 Transaction 모델
# ==========================================
@dataclass
class Transaction:
    id: str
    type: str
    date: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


# ==========================================
# [기존 코드 2] 10번에서 완성한 최신순 판별 함수
# ==========================================
def is_newer(tx_a: dict, tx_b: dict) -> bool:
    """tx_a가 tx_b보다 더 최신(앞쪽)이면 True 반환"""
    if tx_a["date"] > tx_b["date"]:
        return True
    elif tx_a["date"] < tx_b["date"]:
        return False
    else:
        # 같은 날짜면 ID 오름차순 (작은 ID가 앞쪽)
        return tx_a["id"] < tx_b["id"]


# ==========================================
# [09번 확장] TransactionRepository에 insert_sorted 추가
# ==========================================
class TransactionRepository:
    def __init__(self, file_path: str = "data/transactions.jsonl"):
        self.file_path = file_path

    # [09번에서 작성한 스트리밍 읽기 메서드]
    def get_all(self) -> Generator[Transaction, None, None]:# 기본적으로 제네레이터를 반환 yeild를 쓰는 함수란거지
        if not os.path.exists(self.file_path):# tracations.jsonl이 존재하지않으면 중단
            return
        # 존재하면 열어서, 한줄씩 읽고, 빈줄은 넘기고. yield로 Generator를 반환한다!
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                yield Transaction.from_dict(obj)


    # -------------------------------------------------------------
    # [11번 신규] 한 건씩 정렬 위치를 찾아 삽입하는 원자적 재작성 메서드
    # -------------------------------------------------------------
    def insert_sorted(self, new_tx: Transaction) -> None:
        # 파일이 아예 없으면 바로 새 파일로 생성
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(new_tx.to_dict(), ensure_ascii=False) + "\n")
            return

        temp_file = self.file_path + ".tmp"
        inserted = False  # 새 거래가 삽입되었는지 추적하는 플래그
        new_dict = new_tx.to_dict()

        with open(self.file_path, "r", encoding="utf-8") as src, \
             open(temp_file, "w", encoding="utf-8") as dst:
            
            for line in src:
                line = line.strip()
                if not line:
                    continue
                existing_dict = json.loads(line)

                # [TODO 1] 아직 새 거래가 삽입되지 않았고(not inserted),
                #          new_dict가 existing_dict보다 더 최신(is_newer)이라면?
                #          1) new_dict를 먼저 dst에 쓰고 (json 문자열 + "\n")
                #          2) inserted = True로 바꿔주세요.
                # TODO: if not inserted and is_newer(new_dict, existing_dict):
                #           ...
                if not inserted and is_newer(new_dict, existing_dict):
                    dst.write(json.dumps(new_dict, ensure_ascii=False) + "\n")
                    inserted = True

                # 기존 거래는 그대로 기록
                dst.write(json.dumps(existing_dict, ensure_ascii=False) + "\n")

            # [TODO 2] 원본 파일을 다 읽었는데도 아직 삽입되지 않았다면?
            #          (즉, new_tx가 파일의 모든 거래보다 오래되었을 때)
            #          new_dict를 파일 맨 끝에 써주세요.
            # TODO: if not inserted:
            #           ...
            if not inserted:
                dst.write(json.dumps(new_dict, ensure_ascii=False) + "\n")
                inserted = True

        # [TODO 3] 10번에서 실습한 os.replace()로 임시 파일(temp_file)을 원본(self.file_path)으로 교체하세요.
        # TODO: os.replace(..., ...)
        os.replace(temp_file, self.file_path)


# ==========================================
# 테스트 실행부
# ==========================================
if __name__ == "__main__":
    repo = TransactionRepository()

    print("=== 1. 추가 전 기존 거래 목록 ===")
    for tx in repo.get_all():
        print(f"  [{tx.date}] {tx.id} - {tx.memo}")

    # 중간에 끼어들어야 할 새로운 거래 (2026-03-19 저녁 치킨)
    # 2026-03-20(순대국밥) 다음, 2026-03-19(지하철 TX-000002) 사이에 쏙 들어가야 합니다!
    new_chicken = Transaction(
        id="TX-000004",
        type="expense",
        date="2026-03-19",
        category="food",
        amount=22000,
        memo="저녁 치킨",
        tags=["dinner"]
    )

    print(f"\n새 거래 추가 시도: [{new_chicken.date}] {new_chicken.id} - {new_chicken.memo}")
    repo.insert_sorted(new_chicken)

    print("\n=== 2. 추가 후 거래 목록 (정렬 확인) ===")
    for tx in repo.get_all():
        print(f"  [{tx.date}] {tx.id} - {tx.memo}")
