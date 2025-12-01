from repositories import employee_repo

def list_employees():
    return employee_repo.get_all()

def get_employee(emp_id: str):
    return employee_repo.get(emp_id)

def get_employee_by_auth_id(auth_id: str):
    return employee_repo.get_by_authentication_id(auth_id)

def create_employee(data):
    return employee_repo.create(data)

def update_employee(emp_id, data):
    return employee_repo.update(emp_id, data)

def delete_employee(emp_id):
    return employee_repo.delete(emp_id)
