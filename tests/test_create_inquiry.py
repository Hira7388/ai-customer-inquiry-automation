from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from app.inquiries.models import Inquiry


def payload(customer_id):
    return {"customer_id": str(customer_id), "body": "Where is my order?", "idempotency_key": str(uuid4())}


def count_rows(engine, key):
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(Inquiry).where(Inquiry.idempotency_key == key))


def test_create_persists_inquiry(inquiry_client):
    client, customer_id, engine = inquiry_client
    data = payload(customer_id)
    response = client.post("/inquiries", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "RECEIVED"
    assert result["customer_id"] == str(customer_id)
    assert result["body"] == data["body"]
    with Session(engine) as session:
        saved = session.get(Inquiry, UUID(result["id"]))
        assert saved is not None
        assert saved.body == data["body"]


@pytest.mark.parametrize("field,value", [("body", "   "), ("body", ""), ("customer_id", "bad-id"), ("idempotency_key", " "), ("idempotency_key", "x" * 129)])
def test_invalid_input_writes_nothing(inquiry_client, field, value):
    client, customer_id, engine = inquiry_client
    data = payload(customer_id)
    data[field] = value
    assert client.post("/inquiries", json=data).status_code == 422
    assert count_rows(engine, data["idempotency_key"]) == 0


def test_missing_customer_returns_404(inquiry_client):
    client, _, engine = inquiry_client
    data = payload(uuid4())
    response = client.post("/inquiries", json=data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"
    assert count_rows(engine, data["idempotency_key"]) == 0


def test_repeat_request_returns_existing_id(inquiry_client):
    client, customer_id, engine = inquiry_client
    data = payload(customer_id)
    first = client.post("/inquiries", json=data)
    second = client.post("/inquiries", json=data)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert count_rows(engine, data["idempotency_key"]) == 1


def test_simultaneous_repeat_creates_only_one_row(inquiry_client):
    client, customer_id, engine = inquiry_client
    data = payload(customer_id)
    barrier = Barrier(2)

    def wait_before_insert(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO inquiries"):
            barrier.wait(timeout=5)

    event.listen(engine, "before_cursor_execute", wait_before_insert)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: client.post("/inquiries", json=data), range(2)))
    finally:
        event.remove(engine, "before_cursor_execute", wait_before_insert)
    assert sorted(result.status_code for result in results) == [200, 201]
    assert results[0].json()["id"] == results[1].json()["id"]
    assert count_rows(engine, data["idempotency_key"]) == 1


@pytest.mark.parametrize("field,value", [("body", "Different question"), ("customer_id", str(uuid4()))])
def test_same_key_different_request_conflicts(inquiry_client, field, value):
    client, customer_id, engine = inquiry_client
    data = payload(customer_id)
    assert client.post("/inquiries", json=data).status_code == 201
    changed = dict(data, **{field: value})
    assert client.post("/inquiries", json=changed).status_code == 409
    assert count_rows(engine, data["idempotency_key"]) == 1
