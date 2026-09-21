import os
import sys
import argparse
from .error_handlers import handle_errors
from .models import validate_date, validate_type, validate_amount
from .storage import init_storage, TransactionRepository, CategoryRepository, BudgetRepository
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

    # 2. add
    subparsers.add_parser("add", help="대화형 거래 추가")

    # 3. search
    search_parser = subparsers.add_parser("search", help="조건 검색")
    search_parser.add_argument("--category", help="카테고리")
    search_parser.add_argument("--type", choices=["income", "expense"], help="거래 타입")
    search_parser.add_argument("--from", dest="date_from", help="시작 날짜 (YYYY-MM-DD, 해당 날짜 포함)")
    search_parser.add_argument("--to", dest="date_to", help="종료 날짜 (YYYY-MM-DD, 해당 날짜 포함)")
    search_parser.add_argument("--q", dest="keyword", help="메모 키워드")
    search_parser.add_argument("--tag", help="태그")

    # 4. budget
    budget_parser = subparsers.add_parser("budget", help="예산 관리")
    budget_sub = budget_parser.add_subparsers(dest="budget_cmd", required=True, title="예산 명령어", metavar="<subcommand>")
    budget_set_p = budget_sub.add_parser("set", help="월별 예산 설정")
    budget_set_p.add_argument("--month", required=True, help="대상 월 (YYYY-MM)")
    budget_set_p.add_argument("--amount", required=True, help="예산 금액 (양수)")
    budget_sub.add_parser("list", help="설정된 예산 목록 조회")

    return parser


@handle_errors
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


@handle_errors
def handle_add(service: BudgetService):
    date = validate_date(input("날짜(YYYY-MM-DD): ").strip())
    tx_type = validate_type(input("타입(income/expense): ").strip())
    category = service.validate_category(input("카테고리: ").strip())
    amount = validate_amount(input("금액(양수): ").strip())
    memo = input("메모(선택): ").strip()
    raw_tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tags = []
    if raw_tags:
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

    new_tx = service.add_transaction(
        date=date,
        tx_type=tx_type,
        category=category,
        amount=amount,
        memo=memo,
        tags=tags,
    )
    print(f"[저장 완료] id={new_tx.id}")


@handle_errors
def handle_search(service: BudgetService, args):
    category = None
    if args.category is not None:
        category = args.category.strip().lower()
        if not category:
            raise ValueError("카테고리는 공백일 수 없습니다.")

    date_from = None
    if args.date_from is not None:
        date_from = validate_date(args.date_from)

    date_to = None
    if args.date_to is not None:
        date_to = validate_date(args.date_to)

    if date_from and date_to and date_from > date_to:
        raise ValueError("시작 날짜는 종료 날짜보다 늦을 수 없습니다. --from과 --to를 확인해 주세요.")

    keyword = args.keyword.strip() if args.keyword is not None else None
    if keyword == "":
        raise ValueError("메모 키워드는 공백일 수 없습니다.")

    tag = args.tag.strip() if args.tag is not None else None
    if tag == "":
        raise ValueError("태그는 공백일 수 없습니다.")

    results = service.search_transactions(
        category=category,
        tx_type=args.type,
        date_from=date_from,
        date_to=date_to,
        keyword=keyword,
        tag=tag,
    )
    count = 0
    for tx in results:
        count += 1
        tags = f" #{' #'.join(tx.tags)}" if tx.tags else ""
        sign = "(+)" if tx.type == "income" else "(-)"
        print(f"[{tx.id}] {tx.date} | {sign} {tx.amount:>10,}원 | {tx.category:<10} | {tx.memo}{tags}")

    if count == 0:
        print("조건에 일치하는 거래 내역이 없습니다.")
    else:
        print(f"총 {count}건의 거래가 검색되었습니다.")


@handle_errors
def handle_budget(service: BudgetService, args):
    if args.budget_cmd == "set":
        b = service.set_budget(month=args.month, amount=args.amount)
        print(f"[저장 완료] {b.month} 예산 {b.amount}원")
    elif args.budget_cmd == "list":
        budgets = service.list_budgets()
        if not budgets:
            print("설정된 예산이 없습니다.")
            return
        print("=== [월별 예산 목록] ===")
        for b in budgets:
            print(f"- {b.month}: {b.amount:,}원")


@handle_errors
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
    cat_repo = CategoryRepository(file_path=os.path.join(data_dir, "categories.jsonl"))
    budget_repo = BudgetRepository(file_path=os.path.join(data_dir, "budgets.jsonl"))
    service = BudgetService(tx_repo=tx_repo, cat_repo=cat_repo, budget_repo=budget_repo)

    if args.command == "list":
        handle_list(service, args)
    elif args.command == "add":
        handle_add(service)
    elif args.command == "search":
        handle_search(service, args)
    elif args.command == "budget":
        handle_budget(service, args)



if __name__ == "__main__":
    main()
