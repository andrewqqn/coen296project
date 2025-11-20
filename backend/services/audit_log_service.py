from domain.repositories import audit_log_repo

def list_logs(): return audit_log_repo.get_all()
def create_log(data): return audit_log_repo.create(data)
