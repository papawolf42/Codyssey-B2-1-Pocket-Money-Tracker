from .models import Transaction
from .storage import TransactionRepository


class BudgetService:
    def __init__(self, tx_repo: TransactionRepository):
        self.tx_repo = tx_repo

    def list_transactions(self, limit: int = 5) -> list[Transaction]:
        result = []
        for tx in self.tx_repo.get_all():
            result.append(tx)
            if len(result) == limit:
                break
        return result
