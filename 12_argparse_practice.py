import os
import json
import argparse
from dataclasses import dataclass, field
from typing import Generator

# ==========================================
# [기존 코드 재사용] 04/09에서 완성한 모델 & 저장소
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
# [12번 실습] argparse 4대 블록 단계별 조립
# ==========================================
def main():
    # -------------------------------------------------------------
    # [블록 1] 메인 파서(안내 데스크) 만들기
    # 사용 함수: argparse.ArgumentParser(description=...)
    # -------------------------------------------------------------
    # TODO: parser = argparse.ArgumentParser(description="나만의 가계부 CLI")
    parser = argparse.ArgumentParser(description="[나만의 가계부 CLI]")

    # -------------------------------------------------------------
    # [블록 2] 공통 옵션 달기
    # 사용 함수: parser.add_argument("--옵션명", default=..., help=...)
    # -------------------------------------------------------------
    # TODO: parser.add_argument("--data-dir", default="./data", help="데이터 저장 디렉터리")
    parser.add_argument("--data-dir", default="./data", help="데이터 저장 디렉터리 지정 (기본값: ./data)")

    # -------------------------------------------------------------
    # [블록 3] 하위 명령어(subcommand) 분류기 만들기
    # 사용 함수: parser.add_subparsers(dest="command", required=True)
    # (dest="command"로 지정해야 어떤 명령을 쳤는지 args.command로 확인 가능)
    # -------------------------------------------------------------
    # TODO: subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True, title="사용 가능한 명령어", metavar="<command>")
    # subparsers = parser.add_subparsers(dest="command", required=True, title="사용 가능한 명령어")

    # -------------------------------------------------------------
    # [블록 4] 각 하위 명령어 창구 등록 및 전용 옵션 달기
    # 사용 함수: subparsers.add_parser("명령어"), 창구파서.add_argument(...)
    # -------------------------------------------------------------
    # TODO 4-1: list_parser = subparsers.add_parser("list", help="거래 목록 조회")
    #           list_parser.add_argument("--limit", type=int, default=5, help="출력 건수")
    #
    # TODO 4-2: add_parser = subparsers.add_parser("add", help="거래 추가")
    list_parser = subparsers.add_parser("list", help="거래 목록 조회")
    list_parser.add_argument("--limit", type=int, default=5, help="출력 건수 (기본값: 5)")
    add_parser = subparsers.add_parser("add", help="거래 추가")

    # -------------------------------------------------------------
    # [블록 5] 터미널 입력 해석 및 명령어 분기 실행
    # 사용 함수: args = parser.parse_args()
    # -------------------------------------------------------------
    # TODO: args = parser.parse_args()
    #
    #       # 저장소 연결
    #       tx_file = os.path.join(args.data_dir, "transactions.jsonl")
    #       repo = TransactionRepository(file_path=tx_file)
    #
    #       # 명령어에 따른 분기
    #       if args.command == "list":
    #           for i, tx in enumerate(repo.get_all(), 1):
    #               print(f"[{tx.date}] {tx.category} : {tx.amount}원 ({tx.memo})")
    #               if i == args.limit:
    #                   break
    #       elif args.command == "add":
    #           print("add 명령어가 호출되었습니다!")
    args = parser.parse_args()

    # 저장소 연결
    tx_file = os.path.join(args.data_dir, "transactions.jsonl")
    repo = TransactionRepository(file_path=tx_file) 

    # 명령어에 따른 분기
    if args.command == "list":
        for i, tx in enumerate(repo.get_all(), 1):
            print(f"[{tx.date}] {tx.category} : {tx.amount}원 ({tx.memo})")
            if i == args.limit:
                break
    elif args.command == "add":
        print("add 명령어가 호출되었습니다!")

if __name__ == "__main__":
    main()
