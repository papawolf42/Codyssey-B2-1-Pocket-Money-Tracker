import os
import sys
import argparse
from .storage import init_storage, TransactionRepository
from .services import BudgetService


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m budget_app",
        description="[나만의 가계부 CLI]",
    )
    parser.add_argument("--data-dir", default="./data", help="데이터 저장 디렉터리 지정 (기본값: ./data)")

    subparsers = parser.add_subparsers(dest="command", required=True, title="사용 가능한 명령어", metavar="<command>")

    # 1. list
    list_parser = subparsers.add_parser("list", help="거래 목록 조회")
    list_parser.add_argument("--limit", type=int, default=5, help="출력 건수 (기본값: 5)")

    return parser


def handle_list(service: BudgetService, args):
    txs = service.list_transactions(limit=args.limit)
    if not txs:
        print("등록된 거래 내역이 없습니다.")
        return

    print(f"=== [최신 거래 목록 (최대 {args.limit}건)] ===")
    for tx in txs:
        tags = f" #{' #'.join(tx.tags)}" if tx.tags else ""
        sign = "(+)" if tx.type == "income" else "(-)"
        print(f"[{tx.id}] {tx.date} | {sign} {tx.amount:>10,}원 | {tx.category:<10} | {tx.memo}{tags}")


def main():
    parser = create_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # 저장소 초기화
    data_dir = os.path.abspath(args.data_dir)
    init_storage(data_dir=data_dir)

    # 서비스 연결
    tx_repo = TransactionRepository(file_path=os.path.join(data_dir, "transactions.jsonl"))
    service = BudgetService(tx_repo=tx_repo)

    if args.command == "list":
        handle_list(service, args)


if __name__ == "__main__":
    main()
