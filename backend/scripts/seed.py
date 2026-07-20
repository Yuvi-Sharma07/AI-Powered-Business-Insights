import sys
import os
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faker import Faker
from app.database import engine, SessionLocal, Base
from app import models

fake = Faker()

REGIONS = ["North", "South", "East", "West", "Central"]

PRODUCTS_POOL = [
    {"name": "Pro Wireless Headset", "category": "Electronics", "price": 149.99},
    {"name": "UltraView 27-inch Monitor", "category": "Electronics", "price": 289.99},
    {"name": "Mechanical Gaming Keyboard", "category": "Electronics", "price": 89.99},
    {"name": "Ergonomic Office Chair", "category": "Furniture", "price": 199.99},
    {"name": "Standing Desk (Dual Motor)", "category": "Furniture", "price": 450.00},
    {"name": "Slim Leather Wallet", "category": "Clothing", "price": 45.00},
    {"name": "Waterproof Windbreaker Jacket", "category": "Clothing", "price": 120.00},
    {"name": "Cotton Crewneck T-Shirt", "category": "Clothing", "price": 24.99},
    {"name": "Executive Notebook & Pen Set", "category": "Office Supplies", "price": 29.99},
    {"name": "Heavy-Duty Paper Shredder", "category": "Office Supplies", "price": 79.99},
    {"name": "Cork Desk Pad (Large)", "category": "Office Supplies", "price": 19.99},
    {"name": "Smart Fitness Watch", "category": "Electronics", "price": 179.99}
]

def seed_database():
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Seeding Regions...")
        db_regions = []
        for name in REGIONS:
            region = models.Region(name=name)
            db.add(region)
            db_regions.append(region)
        db.commit()

        print("Seeding Products...")
        db_products = []
        for index, item in enumerate(PRODUCTS_POOL):
            product = models.Product(
                name=item["name"],
                category=item["category"],
                price=Decimal(str(item["price"])),
                sku=f"SKU-{item['category'][:3].upper()}-{index + 1001}"
            )
            db.add(product)
            db_products.append(product)
        db.commit()

        print("Seeding Customers...")
        db_customers = []
        for _ in range(100):
            customer = models.Customer(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                region_id=random.choice(db_regions).id,
                created_at=fake.date_time_between(start_date="-1y", end_date="now")
            )
            db.add(customer)
            db_customers.append(customer)
        db.commit()

        print("Seeding Orders and Order Items...")
        # Generate orders over the past 365 days
        start_date = datetime.now() - timedelta(days=365)
        
        # Inject explicit high sales volume anomalies on specific historical dates
        anomaly_dates = [
            (datetime.now() - timedelta(days=45)).date(),
            (datetime.now() - timedelta(days=120)).date(),
            (datetime.now() - timedelta(days=250)).date(),
        ]

        # Generate orders day by day
        for i in range(365):
            current_day = start_date + timedelta(days=i)
            current_date = current_day.date()
            
            # Determine order count and scale multiplier
            if current_date in anomaly_dates:
                order_count = random.randint(15, 25)
            else:
                order_count = random.randint(1, 5)
                if random.random() < 0.15:  # Some days have no orders
                    order_count = 0

            for _ in range(order_count):
                cust = random.choice(db_customers)
                
                # Spread out order times
                order_time = datetime.combine(
                    current_date, 
                    datetime.min.time()
                ) + timedelta(
                    hours=random.randint(8, 20), 
                    minutes=random.randint(0, 59)
                )
                
                status = "Completed"
                if random.random() < 0.05:
                    status = "Cancelled"
                elif random.random() < 0.1:
                    status = "Pending"
                    
                order = models.Order(
                    customer_id=cust.id,
                    order_date=order_time,
                    status=status,
                    total_amount=Decimal("0.00")
                )
                db.add(order)
                db.commit()
                db.refresh(order)
                
                # Pick 1 to 4 random products
                item_count = random.randint(1, 4)
                selected_products = random.sample(db_products, item_count)
                order_total = Decimal("0.00")
                
                for prod in selected_products:
                    if current_date in anomaly_dates:
                        # Anomaly spike: high quantities
                        qty = random.randint(5, 15)
                    else:
                        qty = random.randint(1, 2)
                        
                    unit_price = prod.price
                    total_price = Decimal(str(qty)) * unit_price
                    order_total += total_price
                    
                    item = models.OrderItem(
                        order_id=order.id,
                        product_id=prod.id,
                        quantity=qty,
                        unit_price=unit_price,
                        total_price=total_price
                    )
                    db.add(item)
                
                order.total_amount = order_total
                db.commit()
                
        print("Database seeded successfully with retail mock data.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
