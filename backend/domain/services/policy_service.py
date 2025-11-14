from domain.repositories import policy_repo
def list_policies(): return policy_repo.get_all()
def create_policy(data): return policy_repo.create(data)
def update_policy(policy_id, data): return policy_repo.update(policy_id, data)
def delete_policy(policy_id): return policy_repo.delete(policy_id)
