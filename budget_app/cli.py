import os
import sys
import argparse
from .error_handlers import handle_errors
from .models import Transaction, validate_date, validate_type, validate_amount
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

    # 5. summary
    summary_parser = subparsers.add_parser("summary", help="월별 결산 및 예산 요약")
    summary_parser.add_argument("--month", required=True, help="대상 월 (YYYY-MM)")
    summary_parser.add_argument("--top", type=int, default=3, help="지출 상위 카테고리 수 (기본값: 3)")

    # 6. delete
    delete_parser = subparsers.add_parser("delete", help="특정 거래 내역 삭제")
    delete_parser.add_argument("--id", required=True, help="삭제할 거래 ID (예: TX-000001)")

    # 7. update
    update_parser = subparsers.add_parser("update", help="특정 거래 내역 수정")
    update_parser.add_argument("--id", required=True, help="수정할 거래 ID (예: TX-000001)")
    update_parser.add_argument("--date", help="새 날짜 (YYYY-MM-DD)")
    update_parser.add_argument("--type", choices=["income", "expense"], help="새 타입 (income/expense)")
    update_parser.add_argument("--category", help="새 카테고리")
    update_parser.add_argument("--amount", help="새 금액 (양수)")
    update_parser.add_argument("--memo", help="새 메모")
    update_parser.add_argument("--tags", help="새 태그 (쉼표로 구분)")

    # 8. category
    cat_parser = subparsers.add_parser("category", help="카테고리 관리")
    cat_sub = cat_parser.add_subparsers(dest="category_cmd", required=True, title="카테고리 명령어", metavar="<command>")
    cat_add = cat_sub.add_parser("add", help="새 카테고리 추가")
    cat_add.add_argument("name", help="추가할 카테고리 이름")
    cat_sub.add_parser("list", help="등록된 카테고리 목록 조회")
    cat_rm = cat_sub.add_parser("remove", help="카테고리 삭제")
    cat_rm.add_argument("name", help="삭제할 카테고리 이름")

    return parser


def format_transaction(tx: Transaction) -> str:
    tags = f" #{' #'.join(tx.tags)}" if tx.tags else ""
    sign = "(+)" if tx.type == "income" else "(-)"
    return f"[{tx.id}] {tx.date} | {sign} {tx.amount:>10,}원 | {tx.category:<10} | {tx.memo}{tags}"


def parse_tags(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    return [t.strip() for t in raw.split(",") if t.strip()]


@handle_errors
def handle_list(service: BudgetService, args):
    txs = service.list_transactions(limit=args.limit)
    if not txs:
        print("등록된 거래 내역이 없습니다.")
        return

    print(f"=== [최신 거래 목록 (최대 {args.limit}건)] ===")
    for tx in txs:
        print(format_transaction(tx))


@handle_errors
def handle_add(service: BudgetService):
    date = validate_date(input("날짜(YYYY-MM-DD): ").strip())
    tx_type = validate_type(input("타입(income/expense): ").strip())
    category = service.validate_category(input("카테고리: ").strip())
    amount = validate_amount(input("금액(양수): ").strip())
    memo = input("메모(선택): ").strip()
    raw_tags = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tags = parse_tags(raw_tags) or []

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
        print(format_transaction(tx))

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
def handle_summary(service: BudgetService, args):
    s = service.get_summary(month=args.month, top=args.top)
    if not s["has_data"] and s["budget"] is None:
        print(f"[{s['month']}] 해당 월의 데이터가 없습니다.")
        return

    print(f"총 수입: {s['total_income']}원")
    print(f"총 지출: {s['total_expense']}원")
    print(f"잔액: {s['balance']}원")
    if s["budget"] is not None:
        print(f"예산: {s['budget']}원 (사용률 {s['usage_percentage']:.1f}%)")
        if s["over_budget_amount"] > 0:
            print(f"[경고] 예산을 {s['over_budget_amount']}원 초과했습니다!")

    if s["top_expenses"]:
        print(f"\n지출 TOP {len(s['top_expenses'])}")
        for rank, (cat, amt) in enumerate(s["top_expenses"], 1):
            print(f"{rank}) {cat} {amt}원")


@handle_errors
def handle_delete(service: BudgetService, args):
    service.delete_transaction(args.id)
    print(f"[삭제 완료] 거래 내역 '{args.id}'가 성공적으로 삭제되었습니다.")


@handle_errors
def handle_update(service: BudgetService, args):
    tags = parse_tags(args.tags)

    updated = service.update_transaction(
        tx_id=args.id,
        date=args.date,
        tx_type=args.type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=tags,
    )
    print(f"[수정 완료] {format_transaction(updated)}")


@handle_errors
def handle_category(service: BudgetService, args):
    if args.category_cmd == "add":
        cat = service.add_category(args.name)
        print(f"[추가 완료] 카테고리 '{cat}'가 성공적으로 등록되었습니다.")
    elif args.category_cmd == "list":
        cats = service.list_categories()
        if not cats:
            print("등록된 카테고리가 없습니다.")
            return
        print("=== [등록된 카테고리 목록] ===")
        for cat in cats:
            print(f"- {cat}")
    elif args.category_cmd == "remove":
        service.remove_category(args.name)
        print(f"[삭제 완료] 카테고리 '{args.name}'가 성공적으로 삭제되었습니다.")


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
    elif args.command == "summary":
        handle_summary(service, args)
    elif args.command == "delete":
        handle_delete(service, args)
    elif args.command == "update":
        handle_update(service, args)
    elif args.command == "category":
        handle_category(service, args)


if __name__ == "__main__":
    main()
