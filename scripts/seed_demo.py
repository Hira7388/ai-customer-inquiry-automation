from uuid import UUID

from sqlalchemy.orm import Session

from app.db import get_engine
from app.inquiries.models import Customer

DEMO_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")


def seed_demo_customer(session: Session) -> UUID:
    if session.get(Customer, DEMO_CUSTOMER_ID) is None:
        session.add(Customer(id=DEMO_CUSTOMER_ID, display_name="Demo Customer"))
        session.commit()
    return DEMO_CUSTOMER_ID


def main() -> None:
    with Session(get_engine()) as session:
        print(seed_demo_customer(session))


if __name__ == "__main__":
    main()
