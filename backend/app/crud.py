from sqlalchemy.orm import Session
from app import models, schemas
from decimal import Decimal
from datetime import datetime, date

# Regions
def get_region(db: Session, region_id: int):
    return db.query(models.Region).filter(models.Region.id == region_id).first()

def get_region_by_name(db: Session, name: str):
    return db.query(models.Region).filter(models.Region.name == name).first()

def get_regions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Region).offset(skip).limit(limit).all()

def create_region(db: Session, region: schemas.RegionCreate):
    db_region = models.Region(name=region.name)
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


# Products
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(models.Product.sku == sku).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# Customers
def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


# Orders
def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).order_by(models.Order.order_date.desc()).offset(skip).limit(limit).all()

def create_order(db: Session, order: schemas.OrderCreate):
    db_order = models.Order(
        customer_id=order.customer_id,
        status=order.status,
        order_date=order.order_date or datetime.utcnow()
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    total_amount = Decimal("0.00")
    for item in order.items:
        item_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        total_amount += item_total
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item_total
        )
        db.add(db_item)

    db_order.total_amount = total_amount
    db.commit()
    db.refresh(db_order)
    return db_order


# Daily KPIs
def get_daily_kpi(db: Session, kpi_date: date):
    return db.query(models.DailyRevenueKPI).filter(models.DailyRevenueKPI.date == kpi_date).first()

def get_daily_kpis(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DailyRevenueKPI).order_by(models.DailyRevenueKPI.date.desc()).offset(skip).limit(limit).all()

def create_or_update_daily_kpi(db: Session, kpi: schemas.DailyRevenueKPICreate):
    db_kpi = db.query(models.DailyRevenueKPI).filter(models.DailyRevenueKPI.date == kpi.date).first()
    if db_kpi:
        db_kpi.total_revenue = kpi.total_revenue
        db_kpi.order_count = kpi.order_count
        db_kpi.anomaly_detected = kpi.anomaly_detected
        db_kpi.anomaly_score = kpi.anomaly_score
        if kpi.summary_report is not None:
            db_kpi.summary_report = kpi.summary_report
    else:
        db_kpi = models.DailyRevenueKPI(**kpi.model_dump())
        db.add(db_kpi)
    
    db.commit()
    db.refresh(db_kpi)
    return db_kpi
