import os
import json
import argparse
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Generator

# ==========================================
# [기존 코드 재사용] 06번 저장소 초기화
# ==========================================
DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary"]
DEFAULT_TRANSACTIONS = [
    {"id": "TX-000001", "type": "expense", "date": "2026-03-20", "category": "food", "amount": 15000, "memo": "점심 순대국밥", "tags": ["lunch"]},
    {"id": "TX-000002", "type": "expense", "date": "2026-03-19", "category": "transport", "amount": 2500, "memo": "지하철", "tags": ["subway"]},
    {"id": "TX-000003", "type": "income", "date": "2026-03-18", "category": "salary", "amount": 3500000, "memo": "3월 급여", "tags": ["monthly"]},
]

def init_storage(data_dir: str = "./data"):
    os.makedirs(data_dir, exist_ok=True)

    # 1. transactions.jsonl
    tx_path = os.path.join(data_dir, "transactions.jsonl")
    if not os.path.exists(tx_path):
        with open(tx_path, "w", encoding="utf-8") as f:
            for tx in DEFAULT_TRANSACTIONS:
                f.write(json.dumps(tx) + "\n")

    # 2. budgets.jsonl
    budgets_path = os.path.join(data_dir, "budgets.jsonl")
    if not os.path.exists(budgets_path):
        with open(budgets_path, "w", encoding="utf-8") as f:
            pass

    # 3. categories.jsonl
    categories_path = os.path.join(data_dir, "categories.jsonl")
    if not os.path.exists(categories_path):
        with open(categories_path, "w", encoding="utf-8") as f:
            for cat in DEFAULT_CATEGORIES:
                f.write(json.dumps({"name": cat}) + "\n")


# ==========================================
# [기존 코드 재사용] 04/11번 Transaction 모델 & 정렬 비교
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


def is_newer(tx_a: dict, tx_b: dict) -> bool:
    """tx_a가 tx_b보다 더 최신(앞쪽)이면 True 반환"""
    if tx_a["date"] > tx_b["date"]:
        return True
    elif tx_a["date"] < tx_b["date"]:
        return False
    else:
        return tx_a["id"] < tx_b["id"]


# ==========================================
# [기존 코드 재사용] 09/11번 TransactionRepository
# ==========================================
class TransactionRepository:
    def __init__(self, file_path: str = "data/transactions.jsonl"):
        self.file_path = file_path

    def get_all(self) -> Generator[Transaction, None, None]:
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                yield Transaction.from_dict(obj)

    def insert_sorted(self, new_tx: Transaction) -> None:
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(new_tx.to_dict(), ensure_ascii=False) + "\n")
            return

        temp_file = self.file_path + ".tmp"
        inserted = False
        new_dict = new_tx.to_dict()

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

        os.replace(temp_file, self.file_path)


# ==========================================
# [14번 실습] 대화형 add 구현
# ==========================================
def main():
    parser = argparse.ArgumentParser(
        prog="python -m budget_app",
        description="[나만의 가계부 CLI]"
    )

    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 디렉터리 지정 (기본값: ./data)"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="사용 가능한 명령어",
        metavar="<command>"
    )

    list_parser = subparsers.add_parser("list", help="거래 목록 조회")
    list_parser.add_argument("--limit", type=int, default=5, help="출력 건수 (기본값: 5)")

    add_parser = subparsers.add_parser("add", help="거래 추가")

    args = parser.parse_args()

    # 저장소 초기화 및 연결
    init_storage(data_dir=args.data_dir)
    path_tx_file = os.path.join(args.data_dir, "transactions.jsonl")
    repo = TransactionRepository(file_path=path_tx_file)

    if args.command == "list":
        for i, tx in enumerate(repo.get_all(), 1):
            print(f"[{tx.date}] {tx.category} : {tx.amount}원 ({tx.memo})")
            if i == args.limit:
                break

    elif args.command == "add":
        # -------------------------------------------------------------
        # [TODO 14-1] 등록된 카테고리 목록 읽어오기
        # - 대상 파일: os.path.join(args.data_dir, "categories.jsonl")
        # - 파일 각 줄의 json에서 "name" 값을 읽어 유효한 카테고리 집합(또는 리스트)을 만듭니다.
        # -------------------------------------------------------------

        # -------------------------------------------------------------
        # [TODO 14-2] 새 거래 ID 생성하기 (TX-000001 형식)
        # - 힌트: repo.get_all()을 순회하면서 가장 큰 숫자 번호를 찾고, 그 번호 + 1로 새 ID를 생성합니다.
        # - 예: 가장 큰 번호가 3이면 f"TX-{4:06d}" -> "TX-000004"
        # -------------------------------------------------------------

        # -------------------------------------------------------------
        # [TODO 14-3] 대화형으로 거래 정보 입력받기 (input) 및 검증
        # - 날짜(date): datetime.strptime(..., "%Y-%m-%d") 활용 (형식 안 맞으면 안내 후 재입력 또는 오류)
        # - 타입(type): "income" 또는 "expense"
        # - 카테고리(category): TODO 14-1의 등록된 카테고리 목록에 있는지 확인
        # - 금액(amount): int 변환 및 양수(> 0) 확인
        # - 메모(memo): input(선택)
        # - 태그(tags): input(선택, 쉼표 구분)
        # -------------------------------------------------------------

        # -------------------------------------------------------------
        # [TODO 14-4] Transaction 객체 생성 및 정렬 저장
        # - repo.insert_sorted(new_tx) 호출
        # - 성공 안내 메시지와 함께 발급된 ID 출력
        # -------------------------------------------------------------
        pass


if __name__ == "__main__":
    main()
