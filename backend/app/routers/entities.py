from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, database

router = APIRouter()

# Regions
@router.post("/regions", response_model=schemas.Region, status_code=status.HTTP_201_CREATED)
def create_region(region: schemas.RegionCreate, db: Session = Depends(database.get_db)):
    db_region = crud.get_region_by_name(db, name=region.name)
    if db_region:
        raise HTTPException(status_code=400, detail="Region already registered")
    return crud.create_region(db=db, region=region)

@router.get("/regions", response_model=List[schemas.Region])
def read_regions(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_regions(db, skip=skip, limit=limit)

@router.get("/regions/{region_id}", response_model=schemas.Region)
def read_region(region_id: int, db: Session = Depends(database.get_db)):
    db_region = crud.get_region(db, region_id=region_id)
    if not db_region:
        raise HTTPException(status_code=404, detail="Region not found")
    return db_region


# Products
@router.post("/products", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    db_product = crud.get_product_by_sku(db, sku=product.sku)
    if db_product:
        raise HTTPException(status_code=400, detail="Product SKU already registered")
    return crud.create_product(db=db, product=product)

@router.get("/products", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_products(db, skip=skip, limit=limit)

@router.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(database.get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


# Customers
@router.post("/customers", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(database.get_db)):
    db_customer = crud.get_customer_by_email(db, email=customer.email)
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_region = crud.get_region(db, region_id=customer.region_id)
    if not db_region:
        raise HTTPException(status_code=400, detail="Invalid region_id")
    return crud.create_customer(db=db, customer=customer)

@router.get("/customers", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_customers(db, skip=skip, limit=limit)

@router.get("/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(customer_id: int, db: Session = Depends(database.get_db)):
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer


# Orders
@router.post("/orders", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(order: schemas.OrderCreate, db: Session = Depends(database.get_db)):
    db_customer = crud.get_customer(db, customer_id=order.customer_id)
    if not db_customer:
        raise HTTPException(status_code=400, detail="Invalid customer_id")
    for item in order.items:
        db_product = crud.get_product(db, product_id=item.product_id)
        if not db_product:
            raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} not found")
    return crud.create_order(db=db, order=order)

@router.get("/orders", response_model=List[schemas.Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_orders(db, skip=skip, limit=limit)

@router.get("/orders/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(database.get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
