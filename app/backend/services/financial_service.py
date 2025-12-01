from domain.repositories import bank_account_repo


# ---- Base generic bank account API ----

def get_bank_account(bank_account: str):
    """Get bank account details by account identifier"""
    return bank_account_repo.get(bank_account)


def create_bank_account(bank_account: str, data: dict):
    """Create a new bank account with the provided data"""
    return bank_account_repo.create(bank_account, data)


def update_bank_account(bank_account: str, data: dict):
    """Update an existing bank account with new data"""
    return bank_account_repo.update(bank_account, data)


# ---- Domain-specific wrappers (optional) ----

def get_account_balance(bank_account: str):
    """Get the current balance of a bank account"""
    account = get_bank_account(bank_account)
    return account.get("balance") if account else None


def update_account_balance(bank_account: str, new_balance: float):
    """Update the balance of a bank account"""
    return update_bank_account(bank_account, {"balance": new_balance})


def get_account_status(bank_account: str):
    """Get the status of a bank account (active, frozen, closed, etc.)"""
    account = get_bank_account(bank_account)
    return account.get("status") if account else None


def update_account_status(bank_account: str, status: str):
    """Update the status of a bank account"""
    return update_bank_account(bank_account, {"status": status})
