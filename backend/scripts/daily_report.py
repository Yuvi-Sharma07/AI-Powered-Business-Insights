import sys
import os
import argparse
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app import models, schemas, crud
from app.services import anomaly, llm

def compute_and_save_daily_report(db: Session, target_date: date) -> models.DailyRevenueKPI:
    """
    Computes sales KPIs, detects outliers, calls the LLM to write a paragraph summary,
    saves it to the database daily_revenue_kpis table, and exports a markdown report.
    """
    print(f"Generating Daily Report for: {target_date}")
    
    # 1. Fetch completed orders within the target date boundary
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    orders = db.query(models.Order).filter(
        models.Order.status == "Completed",
        models.Order.order_date >= start_dt,
        models.Order.order_date <= end_dt
    ).all()
    
    total_revenue = sum(o.total_amount for o in orders)
    order_count = len(orders)
    aov = float(total_revenue / order_count) if order_count > 0 else 0.0
    
    # 2. Run anomaly detector to find where this target_date falls statistically
    detected_anomalies = anomaly.detect_anomalies_for_dates(db)
    
    # Find Z-score for target date
    target_anomaly = None
    for item in detected_anomalies:
        if item["date"] == target_date:
            target_anomaly = item
            break
            
    if target_anomaly:
        z_score = float(target_anomaly["z_score"])
        is_anomaly = bool(target_anomaly["is_anomaly"])
    else:
        z_score = 0.0
        is_anomaly = False
        
    # 3. Generate GenAI Executive Insight Summary
    kpis = {
        "date": target_date.isoformat(),
        "total_revenue": float(total_revenue),
        "order_count": order_count,
        "aov": aov
    }
    
    try:
        summary_insight = llm.generate_daily_summary(kpis, detected_anomalies)
    except Exception as e:
        print(f"Error generating GenAI insight: {e}")
        summary_insight = "Demo Mode: Configure API Key to generate business narrative reports."
        
    # 4. Save/Cache report into database
    kpi_schema = schemas.DailyRevenueKPICreate(
        date=target_date,
        total_revenue=Decimal(str(total_revenue)),
        order_count=order_count,
        anomaly_detected=is_anomaly,
        anomaly_score=z_score,
        summary_report=summary_insight
    )
    
    db_kpi = crud.create_or_update_daily_kpi(db, kpi_schema)
    
    # 5. Export Markdown Report
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    report_path = os.path.join(reports_dir, f"daily_report_{target_date.isoformat()}.md")
    
    report_content = f"""# Daily Business Insights Report - {target_date.isoformat()}

## Executive Summary
{summary_insight}

## Key Performance Indicators
* **Total Revenue**: ${float(total_revenue):,.2f}
* **Total Orders**: {order_count}
* **Average Order Value (AOV)**: ${aov:,.2f}

## Statistical Anomaly Detection
* **Z-Score**: {z_score:.4f}
* **Outlier Status**: {"⚠️ ANOMALY DETECTED (Revenue outlier)" if is_anomaly else "Normal (Within standard parameters)"}

*Report generated automatically on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Report saved to markdown: {report_path}")
    return db_kpi

def main():
    parser = argparse.ArgumentParser(description="Daily sales analytics & insights reporter.")
    parser.add_argument("--run-now", action="store_true", help="Compile and save a report for yesterday immediately.")
    parser.add_argument("--date", type=str, help="Specific target date format YYYY-MM-DD (defaults to yesterday)")
    parser.add_argument("--scheduler", action="store_true", help="Start the daily background execution daemon.")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        # Determine target date (default to yesterday)
        target_date = date.today() - timedelta(days=1)
        if args.date:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            
        if args.run_now or not args.scheduler:
            compute_and_save_daily_report(db, target_date)
            
        if args.scheduler:
            try:
                from apscheduler.schedulers.blocking import BlockingScheduler
                scheduler = BlockingScheduler()
                
                # Setup scheduler job to run daily at 01:00 AM
                def job():
                    with SessionLocal() as session:
                        yesterday = date.today() - timedelta(days=1)
                        compute_and_save_daily_report(session, yesterday)
                        
                scheduler.add_job(job, "cron", hour=1, minute=0, id="daily_kpi_job")
                print("Daily report scheduler started. Press Ctrl+C to exit.")
                scheduler.start()
            except ImportError:
                print("APScheduler package is required to run in daemon/scheduler mode.")
                sys.exit(1)
                
    finally:
        db.close()

if __name__ == "__main__":
    main()
