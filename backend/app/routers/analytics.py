from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Any, Dict, Optional
from decimal import Decimal
from datetime import datetime, date
import json
import io
import pandas as pd

from app import database, models, schemas
from app.services import anomaly, llm

router = APIRouter()

def make_serializable(val: Any) -> Any:
    """Helper to convert database types (Decimal, datetime) into JSON-serializable types."""
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val


@router.get("/revenue-by-region")
def get_revenue_by_region(db: Session = Depends(database.get_db)):
    """Computes total completed revenue aggregated by region."""
    sql = """
        SELECT r.name as region, SUM(oi.total_price) as revenue
        FROM regions r
        JOIN customers c ON c.region_id = r.id
        JOIN orders o ON o.customer_id = c.id
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.status = 'Completed'
        GROUP BY r.name
        ORDER BY revenue DESC
    """
    result = db.execute(text(sql))
    cols = list(result.keys())
    return [
        {col: make_serializable(row[i]) for i, col in enumerate(cols)}
        for row in result.fetchall()
    ]


@router.get("/top-products")
def get_top_products(limit: int = 5, db: Session = Depends(database.get_db)):
    """Retrieves top best-selling products by quantity and generated revenue."""
    sql = """
        SELECT p.name, p.category, SUM(oi.quantity) as quantity_sold, SUM(oi.total_price) as revenue
        FROM products p
        JOIN order_items oi ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'Completed'
        GROUP BY p.name, p.category
        ORDER BY revenue DESC
        LIMIT :limit
    """
    result = db.execute(text(sql), {"limit": limit})
    cols = list(result.keys())
    return [
        {col: make_serializable(row[i]) for i, col in enumerate(cols)}
        for row in result.fetchall()
    ]


@router.get("/monthly-trends")
def get_monthly_trends(db: Session = Depends(database.get_db)):
    """Computes month-over-month sales trends."""
    dialect = db.bind.dialect.name
    if dialect == "sqlite":
        sql = """
            SELECT strftime('%Y-%m', o.order_date) as month, SUM(o.total_amount) as revenue, COUNT(o.id) as order_count
            FROM orders o
            WHERE o.status = 'Completed'
            GROUP BY month
            ORDER BY month
        """
    else:
        sql = """
            SELECT TO_CHAR(o.order_date, 'YYYY-MM') as month, SUM(o.total_amount) as revenue, COUNT(o.id) as order_count
            FROM orders o
            WHERE o.status = 'Completed'
            GROUP BY month
            ORDER BY month
        """
    result = db.execute(text(sql))
    cols = list(result.keys())
    return [
        {col: make_serializable(row[i]) for i, col in enumerate(cols)}
        for row in result.fetchall()
    ]


@router.get("/anomalies")
def get_revenue_anomalies(threshold: float = 2.0, db: Session = Depends(database.get_db)):
    """Analyzes daily sales to flag outlier dates using Z-scores."""
    anomalies_list = anomaly.detect_anomalies_for_dates(db, threshold=threshold)
    # Serialize decimals/dates inside list
    serialized = []
    for item in anomalies_list:
        serialized.append({
            "date": make_serializable(item["date"]),
            "total_revenue": make_serializable(item["total_amount"]),
            "z_score": float(item["z_score"]),
            "is_anomaly": bool(item["is_anomaly"])
        })
    # Sort by date descending
    serialized.sort(key=lambda x: x["date"], reverse=True)
    return serialized


@router.post("/text-to-sql", response_model=schemas.TextToSQLResponse)
def text_to_sql_endpoint(request: schemas.TextToSQLRequest, db: Session = Depends(database.get_db)):
    """
    Accepts a natural language business question, generates the SQL using LLM,
    validates the statement against security rules, executes it safely, 
    and appends a narrative business insight explaining the findings.
    """
    dialect = db.bind.dialect.name
    
    # Step 1: Request LLM to write a SQL query
    try:
        sql_query = llm.generate_sql(request.question, dialect)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM failed to translate question to SQL: {str(e)}"
        )
        
    # Step 2: Security Validation
    is_safe, error_reason = llm.validate_sql_safety(sql_query)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL security check failed: {error_reason}. Generated SQL: {sql_query}"
        )
        
    # Step 3: Safe execution
    try:
        result = db.execute(text(sql_query))
        column_names = list(result.keys())
        rows = result.fetchall()
        
        results_list = []
        for row in rows:
            row_dict = {}
            for idx, col in enumerate(column_names):
                row_dict[col] = make_serializable(row[idx])
            results_list.append(row_dict)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database execution error on generated SQL query: {str(e)}. Query attempted: {sql_query}"
        )
        
    # Step 4: Generate contextual business narrative
    try:
        insight = llm.generate_insight(results_list, request.question)
    except Exception as e:
        insight = f"Failed to generate insight summary: {str(e)}"
        
    return schemas.TextToSQLResponse(
        question=request.question,
        sql=sql_query,
        results=results_list,
        column_names=column_names,
        insight=insight
    )


@router.post("/generate-insight", response_model=schemas.GenerateInsightResponse)
def generate_insight_endpoint(request: schemas.GenerateInsightRequest):
    """Generates plain English narrative insights based on arbitrary data provided in the request body."""
    try:
        context_str = request.context or "custom metrics dataset"
        insight = llm.generate_insight(request.data, f"Analyze this data relating to {context_str}")
        return schemas.GenerateInsightResponse(insight=insight)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom business insight: {str(e)}"
        )


@router.get("/daily-insights/latest", response_model=schemas.DailyRevenueKPI)
def get_latest_daily_insight(db: Session = Depends(database.get_db)):
    """Retrieves the most recent record containing daily KPIs and automated reports."""
    latest_kpi = db.query(models.DailyRevenueKPI).order_by(models.DailyRevenueKPI.date.desc()).first()
    if not latest_kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No daily insights available. Run the daily automation report script first."
        )
    return latest_kpi


@router.post("/upload-csv")
async def upload_csv_data(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    """
    Accepts a flat sales CSV file, parses it using Pandas, normalizes the data,
    and inserts records into regions, products, customers, orders, and order_items tables.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
        
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required_cols = [
            "order_date", "customer_first_name", "customer_last_name", 
            "customer_email", "region", "product_name", "category", 
            "price", "quantity"
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"CSV is missing required columns: {', '.join(missing_cols)}"
            )
            
        rows_added = 0
        
        for _, row in df.iterrows():
            # Region
            region_name = str(row["region"]).strip()
            db_region = db.query(models.Region).filter(models.Region.name == region_name).first()
            if not db_region:
                db_region = models.Region(name=region_name)
                db.add(db_region)
                db.commit()
                db.refresh(db_region)
                
            # Product
            prod_name = str(row["product_name"]).strip()
            prod_cat = str(row["category"]).strip()
            prod_price = Decimal(str(row["price"]))
            
            db_product = db.query(models.Product).filter(models.Product.name == prod_name).first()
            if not db_product:
                sku_hash = abs(hash(prod_name)) % 10000
                db_product = models.Product(
                    name=prod_name,
                    category=prod_cat,
                    price=prod_price,
                    sku=f"SKU-{prod_cat[:3].upper()}-{sku_hash}"
                )
                db.add(db_product)
                db.commit()
                db.refresh(db_product)
                
            # Customer
            cust_email = str(row["customer_email"]).strip()
            cust_first = str(row["customer_first_name"]).strip()
            cust_last = str(row["customer_last_name"]).strip()
            
            db_customer = db.query(models.Customer).filter(models.Customer.email == cust_email).first()
            if not db_customer:
                db_customer = models.Customer(
                    first_name=cust_first,
                    last_name=cust_last,
                    email=cust_email,
                    region_id=db_region.id
                )
                db.add(db_customer)
                db.commit()
                db.refresh(db_customer)
                
            # Order
            order_date_str = str(row["order_date"]).strip()
            try:
                order_date = datetime.strptime(order_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    order_date = datetime.strptime(order_date_str, "%Y-%m-%d")
                except ValueError:
                    order_date = datetime.utcnow()
                    
            status_val = str(row.get("status", "Completed")).strip()
            qty = int(row["quantity"])
            
            db_order = db.query(models.Order).filter(
                models.Order.customer_id == db_customer.id,
                models.Order.order_date == order_date
            ).first()
            
            if not db_order:
                db_order = models.Order(
                    customer_id=db_customer.id,
                    order_date=order_date,
                    status=status_val,
                    total_amount=Decimal("0.00")
                )
                db.add(db_order)
                db.commit()
                db.refresh(db_order)
                
            # OrderItem
            item_total = Decimal(str(qty)) * db_product.price
            db_item = models.OrderItem(
                order_id=db_order.id,
                product_id=db_product.id,
                quantity=qty,
                unit_price=db_product.price,
                total_price=item_total
            )
            db.add(db_item)
            
            db_order.total_amount += item_total
            db.commit()
            rows_added += 1
            
        return {"status": "success", "rows_imported": rows_added, "message": "CSV data successfully imported and normalized."}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to parse and load CSV file: {str(e)}")
