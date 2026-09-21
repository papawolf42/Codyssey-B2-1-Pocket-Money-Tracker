from typing import Generator
from .models import Transaction, Budget, validate_month, validate_amount
from .storage import TransactionRepository, CategoryRepository, BudgetRepository


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
