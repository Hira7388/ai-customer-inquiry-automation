from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, inspect, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

def test_models_round_trip_in_memory() -> None:
    from app.db import Base
    from app.inquiries.models import Customer, Inquiry

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    customer_id = uuid4()
    inquiry_id = uuid4()

    with Session(engine) as session:
        session.add(Customer(id=customer_id, display_name="Demo Customer"))
        session.add(
            Inquiry(
                id=inquiry_id,
                customer_id=customer_id,
                body="Where is my order?",
                idempotency_key=str(uuid4()),
            )
        )
        session.commit()

    with Session(engine) as session:
        inquiry = session.get(Inquiry, inquiry_id)
        assert inquiry is not None
        assert inquiry.status == "RECEIVED"
        assert inquiry.body == "Where is my order?"
        assert session.get(Customer, customer_id) is not None

    engine.dispose()


def test_migration_creates_customers_and_inquiries_tables(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'schema.db').as_posix()}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        assert {"customers", "inquiries"}.issubset(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_seed_demo_customer_is_repeatable() -> None:
    from app.db import Base
    from app.inquiries.models import Customer
    from scripts.seed_demo import seed_demo_customer

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            first_id = seed_demo_customer(session)
            second_id = seed_demo_customer(session)
            count = session.scalar(select(func.count()).select_from(Customer))
            assert first_id == second_id
            assert count == 1
    finally:
        engine.dispose()


def test_migration_persists_customer_and_inquiry(test_database_url: str) -> None:
    from app.db import make_engine
    from app.inquiries.models import Customer, Inquiry

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", test_database_url)
    command.upgrade(config, "head")

    engine = make_engine(test_database_url)
    customer_id = uuid4()
    inquiry_id = uuid4()
    try:
        with Session(engine) as session:
            session.add(Customer(id=customer_id, display_name="Demo Customer"))
            session.add(
                Inquiry(
                    id=inquiry_id,
                    customer_id=customer_id,
                    body="Where is my order?",
                    idempotency_key=str(uuid4()),
                )
            )
            session.commit()

        with Session(engine) as session:
            customer = session.get(Customer, customer_id)
            inquiry = session.get(Inquiry, inquiry_id)
            assert customer is not None
            assert customer.display_name == "Demo Customer"
            assert inquiry is not None
            assert inquiry.body == "Where is my order?"
            assert inquiry.status == "RECEIVED"
            assert inquiry.created_at.tzinfo is not None
    finally:
        with Session(engine) as session:
            session.execute(delete(Inquiry).where(Inquiry.id == inquiry_id))
            session.execute(delete(Customer).where(Customer.id == customer_id))
            session.commit()
        engine.dispose()


def test_unavailable_database_raises_operational_error() -> None:
    from app.db import make_engine

    engine = make_engine(
        "postgresql+psycopg://app:app@127.0.0.1:1/unavailable?connect_timeout=1"
    )
    try:
        with pytest.raises(OperationalError):
            with engine.connect():
                pass
    finally:
        engine.dispose()
