import pytest
from pathlib import Path

from infrastructure.chroma_client import (
    init_chroma_policy_client,
    store_policy_to_chroma,
)


@pytest.fixture(scope="session")
def client():
    """Initialize Chroma client once for all tests."""
    client = init_chroma_policy_client()
    return client


def test_pdf_exists(client):
    """Ensure the policy PDF file exists."""
    assert client.pdf_path.exists(), f"Policy PDF not found: {client.pdf_path}"


def test_store_policy_to_chroma(client):
    """Test inserting PDF chunks into ChromaDB."""
    count = client.store_policy_pdf()
    assert count > 0, "No chunks inserted into Chroma"
    print(f"\nInserted {count} chunks into Chroma")


def test_query_missing_receipt_rule(client):
    """Test retrieval for Rule R4 (Missing Receipt)."""
    result = client.query("What is the rule for missing receipt?")
    docs = result.get("documents", [[]])[0]

    assert len(docs) > 0, "No results returned for 'missing receipt' query"

    print("\nTop retrieved chunk:")
    print(docs[0])

    # Policy must reference Rule R4 or documentation requirements
    matched = any(
        "R4" in chunk or "Missing" in chunk or "receipt" in chunk
        for chunk in docs
    )

    assert matched, "Query did not retrieve expected R4/missing receipt content"


def test_query_large_amount_rule(client):
    """Test retrieval for large amount > $500 (Rule R3)."""
    result = client.query("expense over 500 dollars")
    docs = result.get("documents", [[]])[0]

    assert len(docs) > 0, "No results returned for 'large amount' query"

    matched = any(
        "> $500" in chunk or "$500" in chunk or "R3" in chunk
        for chunk in docs
    )

    assert matched, "Query did not retrieve expected R3 large amount rule"


def test_query_frequency_violation_rule(client):
    """Test retrieval for frequency limit (Rule R2)."""
    result = client.query("multiple submissions per day")
    docs = result.get("documents", [[]])[0]

    assert len(docs) > 0, "No results returned for frequency query"

    matched = any(
        "R2" in chunk or "submission" in chunk or "second" in chunk
        for chunk in docs
    )

    assert matched, "Query did not retrieve expected R2 frequency rule"
