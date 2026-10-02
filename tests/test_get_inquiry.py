from uuid import uuid4


def test_get_saved_inquiry(inquiry_client):
    client, customer_id, _ = inquiry_client
    created = client.post("/inquiries", json={
        "customer_id": str(customer_id), "body": "Where is my order?",
        "idempotency_key": str(uuid4()),
    })
    assert created.status_code == 201
    saved = created.json()
    response = client.get(f"/inquiries/{saved['id']}")
    assert response.status_code == 200
    assert response.json() == saved


def test_get_missing_inquiry(inquiry_client):
    client, _, _ = inquiry_client
    response = client.get(f"/inquiries/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Inquiry not found"


def test_get_invalid_uuid(inquiry_client):
    client, _, _ = inquiry_client
    assert client.get("/inquiries/not-a-uuid").status_code == 422
