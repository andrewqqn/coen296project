from domain.repositories import audit_repo
def list_logs(): return audit_repo.get_all()
def create_log(data): return audit_repo.create(data)
