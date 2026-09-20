import os
import json
import argparse
from dataclasses import dataclass, field
from typing import Generator

# ==========================================
# [기존 코드 재사용] 06번 저장소 초기화 함수
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
# [기존 코드 재사용] 04/09번 모델 & 저장소
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

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


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


# ==========================================
# [13번 실습] python -m budget_app 진입점과 --data-dir 연동
# ==========================================
def main():
    # -------------------------------------------------------------
    # [스텝 1] 메인 파서 생성
    # TODO: prog="python -m budget_app"을 추가하여,
    #       도움말(usage)에 스크립트 파일명이 아니라 'python -m budget_app'이 뜨게 만드세요.
    # -------------------------------------------------------------
    parser = argparse.ArgumentParser(
        prog="python -m budget_app", # usage: __main__.py [-h] [--data-dir DATA_DIR] <command> ... -> usage: python -m budget_app [-h] [--data-dir DATA_DIR] <command> ...
        description="[나만의 가계부 CLI]"
    )

    # 공통 옵션 (--data-dir)
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 디렉터리 지정 (기본값: ./data)"
    )

    # 하위 명령어 분류기
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="사용 가능한 명령어",
        metavar="<command>"
    )

    # 하위 명령어 등록 (list, add)
    list_parser = subparsers.add_parser("list", help="거래 목록 조회")
    list_parser.add_argument("--limit", type=int, default=5, help="출력 건수 (기본값: 5)")

    add_parser = subparsers.add_parser("add", help="거래 추가")

    # 터미널 입력 해석
    args = parser.parse_args()

    # -------------------------------------------------------------
    # [스텝 2] --data-dir 연동 및 저장소 초기화
    # TODO: 사용자가 넘겨준 args.data_dir 경로를 init_storage()에 전달하여
    #       해당 디렉터리가 없으면 자동 생성하고 3개 파일(기본 데이터)을 준비하세요.
    # -------------------------------------------------------------
    # init_storage(...)
    init_storage(data_dir=args.data_dir)

    # -------------------------------------------------------------
    # [스텝 3] TransactionRepository 생성
    # TODO: args.data_dir 내부의 "transactions.jsonl" 경로를 만들어
    #       TransactionRepository에 넘겨주세요.
    # -------------------------------------------------------------
    # tx_file = os.path.join(..., "transactions.jsonl")
    # repo = TransactionRepository(file_path=tx_file)
    path_tx_file = os.path.join(args.data_dir, "transactions.jsonl")
    repo = TransactionRepository(file_path=path_tx_file)

    # -------------------------------------------------------------
    # [스텝 4] 명령어 분기 실행
    # -------------------------------------------------------------
    # if args.command == "list":
    #     for i, tx in enumerate(repo.get_all(), 1):
    #         print(f"[{tx.date}] {tx.category} : {tx.amount}원 ({tx.memo})")
    #         if i == args.limit:
    #             break
    # elif args.command == "add":
    #     print("add 명령어가 호출되었습니다!")
    if args.command == "list":
        for i, tx in enumerate(repo.get_all(), 1):
            print(f"[{tx.date}] {tx.category} : {tx.amount}원 ({tx.memo})")
            if i == args.limit:
                break
    elif args.command == "add":
        print("add 명령어가 호출되었습니다!")

if __name__ == "__main__":
    main()
