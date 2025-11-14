from domain.repositories import expense_repo
def list_expenses(): return expense_repo.get_all()
def get_expense(expense_id: str): return expense_repo.get(expense_id)
def create_expense(data): return expense_repo.create(data)
def update_expense(expense_id, data): return expense_repo.update(expense_id, data)
def delete_expense(expense_id): return expense_repo.delete(expense_id)
