from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional, Any
from decimal import Decimal

# Region Schemas
class RegionBase(BaseModel):
    name: str

class RegionCreate(RegionBase):
    pass

class Region(RegionBase):
    id: int
    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    name: str
    category: str
    price: Decimal
    sku: str

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    class Config:
        from_attributes = True


# Customer Schemas
class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    region_id: int

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# OrderItem Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    total_price: Decimal
    product: Optional[Product] = None
    class Config:
        from_attributes = True


# Order Schemas
class OrderBase(BaseModel):
    customer_id: int
    status: str = "Completed"
    order_date: datetime

class OrderCreate(BaseModel):
    customer_id: int
    order_date: Optional[datetime] = None
    status: str = "Completed"
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    total_amount: Decimal
    items: List[OrderItem] = []
    class Config:
        from_attributes = True


# Daily Revenue KPI Schemas
class DailyRevenueKPIBase(BaseModel):
    date: date
    total_revenue: Decimal
    order_count: int
    anomaly_detected: bool
    anomaly_score: float
    summary_report: Optional[str] = None

class DailyRevenueKPICreate(DailyRevenueKPIBase):
    pass

class DailyRevenueKPI(DailyRevenueKPIBase):
    class Config:
        from_attributes = True


# LLM / Text-to-SQL Schemas
class TextToSQLRequest(BaseModel):
    question: str

class TextToSQLResponse(BaseModel):
    question: str
    sql: str
    results: List[Any]
    column_names: List[str]
    insight: Optional[str] = None


class GenerateInsightRequest(BaseModel):
    data: Any
    context: Optional[str] = None

class GenerateInsightResponse(BaseModel):
    insight: str
