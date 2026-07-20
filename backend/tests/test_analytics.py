import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

from app.main import app
from app.database import Base, get_db
from app import models

# File-based SQLite for isolated testing (avoids multi-connection isolation issues)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    # Setup test DB
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # 1. Seed base data for testing
    region_north = models.Region(id=1, name="North")
    region_south = models.Region(id=2, name="South")
    db.add_all([region_north, region_south])
    db.commit()
    
    prod_widget = models.Product(id=1, name="Standard Widget", category="Office Supplies", price=Decimal("10.00"), sku="SKU-OFF-1001")
    prod_gadget = models.Product(id=2, name="Premium Gadget", category="Electronics", price=Decimal("100.00"), sku="SKU-ELE-1002")
    db.add_all([prod_widget, prod_gadget])
    db.commit()
    
    cust_john = models.Customer(id=1, first_name="John", last_name="Doe", email="john@example.com", region_id=1)
    cust_jane = models.Customer(id=2, first_name="Jane", last_name="Smith", email="jane@example.com", region_id=2)
    db.add_all([cust_john, cust_jane])
    db.commit()
    
    # Create orders across 3 distinct dates (with a huge spike on day 3)
    o1 = models.Order(id=1, customer_id=1, order_date=datetime(2026, 6, 1, 12, 0), status="Completed", total_amount=Decimal("20.00"))
    o2 = models.Order(id=2, customer_id=2, order_date=datetime(2026, 6, 2, 14, 0), status="Completed", total_amount=Decimal("100.00"))
    o3 = models.Order(id=3, customer_id=1, order_date=datetime(2026, 6, 3, 10, 0), status="Completed", total_amount=Decimal("1000.00")) # Anomaly day!
    db.add_all([o1, o2, o3])
    db.commit()
    
    oi1 = models.OrderItem(id=1, order_id=1, product_id=1, quantity=2, unit_price=Decimal("10.00"), total_price=Decimal("20.00"))
    oi2 = models.OrderItem(id=2, order_id=2, product_id=2, quantity=1, unit_price=Decimal("100.00"), total_price=Decimal("100.00"))
    oi3 = models.OrderItem(id=3, order_id=3, product_id=2, quantity=10, unit_price=Decimal("100.00"), total_price=Decimal("1000.00"))
    db.add_all([oi1, oi2, oi3])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_revenue_by_region(client):
    response = client.get("/api/analytics/revenue-by-region")
    assert response.status_code == 200
    data = response.json()
    
    # We should have revenue for North (o1=20, o3=1000 => 1020) and South (o2=100)
    regions = {item["region"]: item["revenue"] for item in data}
    assert "North" in regions
    assert "South" in regions
    assert regions["North"] == 1020.0
    assert regions["South"] == 100.0


def test_top_products(client):
    response = client.get("/api/analytics/top-products?limit=2")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert data[0]["name"] == "Premium Gadget"
    assert data[0]["revenue"] == 1100.0 # oi2 (100) + oi3 (1000)
    assert data[1]["name"] == "Standard Widget"
    assert data[1]["revenue"] == 20.0


def test_revenue_anomalies(client):
    # threshold = 1.0 (so o3's massive revenue of 1000 on June 3rd is flagged)
    response = client.get("/api/analytics/anomalies?threshold=1.0")
    assert response.status_code == 200
    data = response.json()
    
    # Verify anomaly flagging
    anomaly_days = {item["date"]: item["is_anomaly"] for item in data}
    assert "2026-06-03" in anomaly_days
    assert anomaly_days["2026-06-03"] is True  # Flags spiked revenue day
    assert anomaly_days["2026-06-01"] is False # Standard day remains normal


def test_text_to_sql_security(client):
    from unittest.mock import patch
    
    # Unsafe query check: drop database attempts
    with patch("app.services.llm.generate_sql", return_value="DROP TABLE orders;"):
        response = client.post(
            "/api/analytics/text-to-sql",
            json={"question": "Drop the database table orders and wipe everything"}
        )
        assert response.status_code == 400
        assert "security check failed" in response.json()["detail"].lower()
    
    # Unsafe query check: delete statements
    with patch("app.services.llm.generate_sql", return_value="DELETE FROM customers WHERE region_id = 2;"):
        response = client.post(
            "/api/analytics/text-to-sql",
            json={"question": "Delete all rows from customers where region is South"}
        )
        assert response.status_code == 400
        assert "security check failed" in response.json()["detail"].lower()


def test_text_to_sql_valid(client):
    # Valid query using default mock loader
    response = client.post(
        "/api/analytics/text-to-sql",
        json={"question": "Give me the monthly sales revenue trends"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "sql" in data
    assert "results" in data
    assert "insight" in data
    assert len(data["results"]) > 0
