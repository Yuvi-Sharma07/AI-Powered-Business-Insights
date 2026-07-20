from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Boolean, Numeric, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Relationships
    customers = relationship("Customer", back_populates="region")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    region = relationship("Region", back_populates="customers")
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="Completed", nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class DailyRevenueKPI(Base):
    __tablename__ = "daily_revenue_kpis"

    date = Column(Date, primary_key=True, index=True)
    total_revenue = Column(Numeric(12, 2), nullable=False)
    order_count = Column(Integer, nullable=False)
    anomaly_detected = Column(Boolean, default=False, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    summary_report = Column(Text, nullable=True)
