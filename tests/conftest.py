import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import get_session, make_engine
from app.inquiries.models import Customer, Inquiry
from app.main import app


@pytest.fixture
def test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    development_url = os.getenv("DATABASE_URL")
    if not url or not development_url:
        pytest.fail("Set DATABASE_URL and a separate TEST_DATABASE_URL")
    if not url.startswith("postgresql+psycopg://") or url == development_url:
        pytest.fail("TEST_DATABASE_URL must be a separate PostgreSQL database")
    return url


@pytest.fixture
def inquiry_client(test_database_url):
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", test_database_url)
    command.upgrade(config, "head")
    engine = make_engine(test_database_url)
    customer_id = uuid4()
    with Session(engine) as session:
        session.add(Customer(id=customer_id, display_name="API Test Customer"))
        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        with TestClient(app) as client:
            yield client, customer_id, engine
    finally:
        app.dependency_overrides.pop(get_session, None)
        with Session(engine) as session:
            session.execute(delete(Inquiry).where(Inquiry.customer_id == customer_id))
            session.execute(delete(Customer).where(Customer.id == customer_id))
            session.commit()
        engine.dispose()
