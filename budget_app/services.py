from typing import Generator
from .models import Transaction
from .storage import TransactionRepository, CategoryRepository


class BudgetService:
    def __init__(self, tx_repo: TransactionRepository, cat_repo: CategoryRepository = None):
        self.tx_repo = tx_repo
        self.cat_repo = cat_repo

    def add_transaction(
        self, date: str, tx_type: str, category: str, amount, memo: str = "", tags: list[str] = None
    ) -> Transaction:
        if self.cat_repo and not self.cat_repo.is_registered(category):
            cats = ", ".join(self.cat_repo.get_all())
            raise ValueError(f"등록되지 않은 카테고리입니다: '{category}'. (등록된 카테고리: {cats})")

        tx_id = self.tx_repo.get_next_id()
        new_tx = Transaction(
            id=tx_id,
            type=tx_type,
            date=date,
            category=category,
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

    def search_transactions(self, category: str = None, tx_type: str = None) -> Generator[Transaction, None, None]:
        return self.tx_repo.search(category=category, tx_type=tx_type)
