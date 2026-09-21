from typing import Generator
from .models import Transaction, Budget, validate_date, validate_type, validate_month, validate_amount
from .storage import TransactionRepository, CategoryRepository, BudgetRepository, write_csv


class BudgetService:
    def __init__(
        self,
        tx_repo: TransactionRepository,
        cat_repo: CategoryRepository,
        budget_repo: BudgetRepository,
    ):
        self.tx_repo = tx_repo
        self.cat_repo = cat_repo
        self.budget_repo = budget_repo

    def validate_category(self, category: str) -> str:
        clean = category.strip()
        if not clean:
            raise ValueError("카테고리는 공백일 수 없습니다.")
        if not self.cat_repo.is_registered(clean):
            cats = ", ".join(self.cat_repo.get_all())
            raise ValueError(f"등록되지 않은 카테고리입니다: '{clean}'. (등록된 카테고리: {cats})")
        return clean

    def add_category(self, name: str) -> str:
        clean = name.strip() if name else ""
        if not clean:
            raise ValueError("카테고리 이름은 공백일 수 없습니다.")
        if self.cat_repo.is_registered(clean):
            raise ValueError(f"이미 등록된 카테고리입니다: '{clean}'")
        self.cat_repo.add(clean)
        return clean

    def list_categories(self) -> list[str]:
        return self.cat_repo.get_all()

    def remove_category(self, name: str) -> None:
        clean = name.strip() if name else ""
        if not clean:
            raise ValueError("카테고리 이름은 공백일 수 없습니다.")
        if not self.cat_repo.is_registered(clean):
            raise ValueError(f"존재하지 않는 카테고리입니다: '{clean}'")

        for tx in self.tx_repo.get_all():
            if tx.category.lower() == clean.lower():
                raise ValueError(
                    f"'{clean}' 카테고리를 사용하는 거래 내역(예: [{tx.id}] {tx.memo})이 존재하여 삭제할 수 없습니다. "
                    "해당 거래를 먼저 수정하거나 삭제해 주세요."
                )

        self.cat_repo.remove(clean)

    def add_transaction(
        self, date: str, tx_type: str, category: str, amount, memo: str = "", tags: list[str] = None
    ) -> Transaction:
        valid_cat = self.validate_category(category)
        tx_id = self.tx_repo.get_next_id()
        new_tx = Transaction(
            id=tx_id,
            type=tx_type,
            date=date,
            category=valid_cat,
            amount=amount,
            memo=memo,
            tags=tags or [],
        )
        self.tx_repo.insert_sorted(new_tx)
        return new_tx

    def list_transactions(self, limit: int = 5) -> list[Transaction]:
        result = []
        for tx in self.tx_repo.get_all():
            result.append(tx)
            if len(result) == limit:
                break
        return result

    def search_transactions(
        self,
        category: str = None,
        tx_type: str = None,
        date_from: str = None,
        date_to: str = None,
        keyword: str = None,
        tag: str = None,
    ) -> Generator[Transaction, None, None]:
        return self.tx_repo.search(
            category=category,
            tx_type=tx_type,
            date_from=date_from,
            date_to=date_to,
            keyword=keyword,
            tag=tag,
        )

    def update_transaction(
        self,
        tx_id: str,
        date: str = None,
        tx_type: str = None,
        category: str = None,
        amount = None,
        memo: str = None,
        tags: list[str] = None,
    ) -> Transaction:
        clean_id = tx_id.strip() if tx_id else ""
        if not clean_id:
            raise ValueError("거래 ID는 공백일 수 없습니다.")

        updates = {}
        if date is not None:
            updates["date"] = validate_date(date)
        if tx_type is not None:
            updates["type"] = validate_type(tx_type)
        if category is not None:
            updates["category"] = self.validate_category(category)
        if amount is not None:
            updates["amount"] = validate_amount(amount)
        if memo is not None:
            updates["memo"] = memo.strip()
        if tags is not None:
            updates["tags"] = tags

        if not updates:
            raise ValueError("수정할 항목이 지정되지 않았습니다. (--amount, --category 등 수정할 옵션을 입력해 주세요)")

        return self.tx_repo.update(clean_id, updates)

    def delete_transaction(self, tx_id: str) -> bool:
        clean_id = tx_id.strip() if tx_id else ""
        if not clean_id:
            raise ValueError("거래 ID는 공백일 수 없습니다.")
        if not self.tx_repo.delete(clean_id):
            raise ValueError(f"존재하지 않는 거래 ID입니다: '{clean_id}'. 'list' 명령어로 ID를 확인해 주세요.")
        return True

    def set_budget(self, month: str, amount) -> Budget:
        valid_month = validate_month(month)
        valid_amount = validate_amount(amount)
        budget = Budget(month=valid_month, amount=valid_amount)
        self.budget_repo.set_budget(budget)
        return budget

    def get_budget(self, month: str) -> Budget | None:
        valid_month = validate_month(month)
        return self.budget_repo.get_budget(valid_month)

    def list_budgets(self) -> list[Budget]:
        return list(self.budget_repo.get_all())

    def _aggregate_monthly_transactions(self, month: str):
        total_income = 0
        total_expense = 0
        category_expenses = {}
        count = 0

        for tx in self.tx_repo.get_all():
            if tx.date.startswith(month):
                count += 1
                if tx.type == "income":
                    total_income += tx.amount
                elif tx.type == "expense":
                    total_expense += tx.amount
                    category_expenses[tx.category] = category_expenses.get(tx.category, 0) + tx.amount

        return total_income, total_expense, category_expenses, count

    def _get_top_categories(self, category_expenses: dict, top: int) -> list[tuple[str, int]]:
        sorted_expenses = sorted(category_expenses.items(), key=lambda item: item[1], reverse=True)
        return sorted_expenses[:top]

    def _calculate_budget_status(self, month: str, total_expense: int):
        budget = self.get_budget(month)
        if budget is None:
            return None, None, 0

        usage_percentage = (total_expense / budget.amount) * 100 if budget.amount > 0 else 0.0
        over_budget_amount = max(0, total_expense - budget.amount)

        return budget.amount, usage_percentage, over_budget_amount

    def get_summary(self, month: str, top: int = 3) -> dict:
        valid_month = validate_month(month)
        if top <= 0:
            raise ValueError(f"--top 옵션은 1 이상이어야 합니다: {top}")

        total_income, total_expense, category_expenses, count = self._aggregate_monthly_transactions(valid_month)
        top_expenses = self._get_top_categories(category_expenses, top)
        budget_amount, usage_percentage, over_budget_amount = self._calculate_budget_status(valid_month, total_expense)

        return {
            "month": valid_month,
            "has_data": count > 0,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_expenses": top_expenses,
            "budget": budget_amount,
            "usage_percentage": usage_percentage,
            "over_budget_amount": over_budget_amount,
        }

    def export_transactions(
        self,
        out_path: str,
        month: str = None,
        date_from: str = None,
        date_to: str = None,
    ) -> int:
        if not out_path or not out_path.strip():
            raise ValueError("출력 파일 경로(--out)를 입력해 주세요.")
        out_path = out_path.strip()

        month = month.strip() if month else ""
        date_from = date_from.strip() if date_from else ""
        date_to = date_to.strip() if date_to else ""

        if not month and not (date_from or date_to):
            raise ValueError("내보내기 조건을 최소 하나 이상 지정해야 합니다. (--month 또는 --from/--to)")

        if month:
            month = validate_month(month)
        if date_from:
            date_from = validate_date(date_from)
        if date_to:
            date_to = validate_date(date_to)
        if date_from and date_to and date_from > date_to:
            raise ValueError(f"시작 날짜({date_from})는 종료 날짜({date_to})보다 앞서야 합니다.")

        def _rows():
            for tx in self.tx_repo.get_all():
                if month and not tx.date.startswith(f"{month}-"):
                    continue
                if date_from and tx.date < date_from:
                    continue
                if date_to and tx.date > date_to:
                    continue
                yield {
                    "date": tx.date,
                    "type": tx.type,
                    "category": tx.category,
                    "amount": tx.amount,
                    "memo": tx.memo,
                    "tags": ",".join(tx.tags) if tx.tags else "",
                }

        return write_csv(out_path, _rows())
