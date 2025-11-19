import os
import sys
from types import SimpleNamespace
import json

# Ensure backend/ is on sys.path
TEST_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if TEST_BACKEND_ROOT not in sys.path:
    sys.path.insert(0, TEST_BACKEND_ROOT)

import domain.repositories.employee_repo as employee_repo
import domain.repositories.expense_repo as expense_repo
import domain.repositories.audit_log_repo as audit_repo
import domain.repositories.document_repo as document_repo


class MockDoc:
    def __init__(self, id, data, exists=True):
        self.id = id
        self._data = data
        self.exists = exists

    def to_dict(self):
        return self._data


class MockDocumentRef:
    def __init__(self, id, data_store=None):
        self.id = id
        self._data_store = data_store
        self._last_set = None
        self._last_updated = None

    def set(self, data):
        self._last_set = data
        if self._data_store is not None:
            self._data_store[self.id] = data

    def update(self, data):
        self._last_updated = data
        if self._data_store is not None and self.id in self._data_store:
            self._data_store[self.id].update(data)

    def delete(self):
        if self._data_store is not None and self.id in self._data_store:
            del self._data_store[self.id]

    def get(self):
        # return an object that has exists, id, to_dict
        exists = self._data_store is not None and self.id in self._data_store
        d = self._data_store.get(self.id) if self._data_store is not None else None
        return SimpleNamespace(exists=exists, id=self.id, to_dict=lambda: d)


class MockCollection:
    def __init__(self, docs=None, data_store=None):
        # docs: list of MockDoc for stream
        self._docs = docs or []
        self._data_store = data_store or {}

    def stream(self):
        return self._docs

    def order_by(self, *_args, **_kwargs):
        # for audit_repo usage
        return self

    def document(self, doc_id=None):
        if doc_id is None:
            # create new document ref with generated id
            new_id = "gen-id-1"
            return MockDocumentRef(new_id, data_store=self._data_store)
        else:
            return MockDocumentRef(doc_id, data_store=self._data_store)


class MockDB:
    def __init__(self, collections=None):
        # collections: dict name -> MockCollection
        self._collections = collections or {}

    def collection(self, name):
        return self._collections.get(name, MockCollection())


class MockBlob:
    def __init__(self, path, storage=None):
        self.path = path
        # ensure we keep the same storage dict even if it's empty
        self._storage = storage if storage is not None else {}
        self.content_type = "application/pdf"
        self.size = 123
        self.updated = "2025-01-01T00:00:00Z"

    def upload_from_string(self, data):
        print("DEBUG MockBlob.upload_from_string called for:", self.path, "storage id:", id(self._storage))
        self._storage[self.path] = data

    def generate_signed_url(self, expiration):
        return f"https://signed.url/{self.path}?exp={expiration}"

    def delete(self):
        if self.path in self._storage:
            del self._storage[self.path]

    def download_as_bytes(self):
        return self._storage.get(self.path, b"")

    def exists(self):
        return self.path in self._storage

    def reload(self):
        # no-op for metadata
        pass


class MockBucket:
    def __init__(self):
        self._storage = {}

    def blob(self, path):
        print("DEBUG MockBucket.blob called for:", path, "bucket storage id:", id(self._storage))
        return MockBlob(path, storage=self._storage)


# Tests for employee_repo

def test_employee_repo_crud(monkeypatch):
    # prepare data store for employees
    data_store = {"e1": {"name": "Alice"}, "e2": {"name": "Bob"}}
    docs = [MockDoc("e1", data_store["e1"]), MockDoc("e2", data_store["e2"])]
    mock_db = MockDB(collections={"employees": MockCollection(docs=docs, data_store=data_store)})

    # monkeypatch the module's db
    monkeypatch.setattr(employee_repo, "db", mock_db)

    # get_all
    all_emps = employee_repo.get_all()
    assert isinstance(all_emps, list)
    assert any(e["employee_id"] == "e1" for e in all_emps)

    # get existing
    emp = employee_repo.get("e1")
    assert emp.get("name") == "Alice"
    assert emp.get("employee_id") == "e1"

    # get non-existing returns None
    none_emp = employee_repo.get("missing")
    assert none_emp is None

    # create - should add employee_id and call set
    new_emp = {"name": "Carol"}
    res = employee_repo.create(new_emp)
    assert res.get("employee_id") is not None

    # update - call update and return expected dict
    up = employee_repo.update("e1", {"position": "eng"})
    assert up["update"] is True and up["employee_id"] == "e1"

    # delete
    d = employee_repo.delete("e2")
    assert d["deleted"] is True


# Tests for expense_repo

def test_expense_repo_crud(monkeypatch):
    data_store = {"ex1": {"amount": 10}}
    docs = [MockDoc("ex1", data_store["ex1"])]
    mock_db = MockDB(collections={"expenses": MockCollection(docs=docs, data_store=data_store)})
    monkeypatch.setattr(expense_repo, "db", mock_db)

    # get_all
    all_exp = expense_repo.get_all()
    assert isinstance(all_exp, list)
    assert any(e["expense_id"] == "ex1" for e in all_exp)

    # get existing
    ex = expense_repo.get("ex1")
    assert ex["expense_id"] == "ex1"

    # get non-existent
    miss = expense_repo.get("nope")
    assert miss is None

    # create - expense_repo.create expects an object with .json() (per current implementation)
    class FakeModel:
        def __init__(self, d):
            self._d = d
        def json(self):
            return json.dumps(self._d)

    fake = FakeModel({"amount": 50})
    new_id = expense_repo.create(fake)
    assert isinstance(new_id, str)

    # update
    updated = expense_repo.update("ex1", {"amount": 20})
    assert updated["expense_id"] == "ex1"

    # delete
    d = expense_repo.delete("ex1")
    assert d["deleted"] is True


# Tests for audit_repo

def test_audit_repo(monkeypatch):
    data_store = {"a1": {"actor": "x", "timestamp": "t1"}}
    docs = [MockDoc("a1", data_store["a1"])]
    mock_db = MockDB(collections={"audit_logs": MockCollection(docs=docs, data_store=data_store)})
    monkeypatch.setattr(audit_repo, "db", mock_db)

    all_logs = audit_repo.get_all()
    assert isinstance(all_logs, list) and len(all_logs) == 1

    created = audit_repo.create({"actor": "y", "log": "ok"})
    assert created["actor"] == "y" and "id" in created


# Tests for document_repo

def test_document_repo_storage(monkeypatch):
    mock_bucket = MockBucket()
    monkeypatch.setattr(document_repo, "bucket", mock_bucket)
    print("DEBUG document_repo.bucket is", document_repo.bucket, "mock_bucket id", id(mock_bucket))

    # upload_file
    path = document_repo.upload_file("r1.pdf", b"PDFDATA")
    print("DEBUG after upload, bucket._storage id", id(mock_bucket._storage))
    assert path.startswith("expense_receipts/")

    # generate_signed_url
    url = document_repo.generate_signed_url(path, expire_seconds=60)
    assert "signed.url" in url

    # debug: inspect storage state before file_exists check
    print("DEBUG STORAGE KEYS:", list(mock_bucket._storage.keys()))
    # file_exists
    exists = document_repo.file_exists(path)
    print("DEBUG file_exists returned:", exists)
    assert exists is True

    # download_file
    data = document_repo.download_file(path)
    assert data == b"PDFDATA"

    # get_metadata
    meta = document_repo.get_metadata(path)
    assert meta["file_path"] == path

    # delete_file
    res = document_repo.delete_file(path)
    assert res["deleted"] is True
    assert document_repo.file_exists(path) is False

def test_document_repo_storage(monkeypatch):
    mock_bucket = MockBucket()
    monkeypatch.setattr(document_repo, "bucket", mock_bucket)

    # upload_file
    path = document_repo.upload_file("r1.pdf", b"PDFDATA")
    assert path.startswith("expense_receipts/")

    # generate_signed_url
    url = document_repo.generate_signed_url(path, expire_seconds=60)
    assert "signed.url" in url

    # debug: inspect storage state before file_exists check
    print("DEBUG STORAGE KEYS:", list(mock_bucket._storage.keys()))
    # file_exists
    exists = document_repo.file_exists(path)
    print("DEBUG file_exists returned:", exists)
    assert exists is True

    # download_file
    data = document_repo.download_file(path)
    assert data == b"PDFDATA"

    # get_metadata
    meta = document_repo.get_metadata(path)
    assert meta["file_path"] == path

    # delete_file
    res = document_repo.delete_file(path)
    assert res["deleted"] is True
    assert document_repo.file_exists(path) is False
