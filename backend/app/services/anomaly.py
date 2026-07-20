import pandas as pd
from sqlalchemy.orm import Session
from app.models import Order
from datetime import date

def detect_anomalies_for_dates(db: Session, threshold: float = 2.0):
    """
    Retrieves daily revenue statistics from orders, aggregates them using Pandas,
    and flags any date where the daily revenue deviates from the historical mean
    by more than 'threshold' standard deviations (Z-score).
    """
    # Fetch all completed orders to ensure DB compatibility (SQLite / Postgres)
    query = db.query(Order.order_date, Order.total_amount).filter(Order.status == "Completed").all()
    if not query:
        return []

    # Parse and aggregate daily using Pandas
    df = pd.DataFrame(query, columns=["order_date", "total_amount"])
    df["date"] = pd.to_datetime(df["order_date"]).dt.date
    daily_df = df.groupby("date")["total_amount"].sum().reset_index()
    daily_df["total_amount"] = daily_df["total_amount"].astype(float)

    # If we have only 1 day of data, standard deviation is undefined
    if len(daily_df) < 2:
        daily_df["z_score"] = 0.0
        daily_df["is_anomaly"] = False
        return daily_df.to_dict(orient="records")

    mean_val = daily_df["total_amount"].mean()
    std_val = daily_df["total_amount"].std()

    if std_val == 0 or pd.isna(std_val):
        daily_df["z_score"] = 0.0
    else:
        daily_df["z_score"] = (daily_df["total_amount"] - mean_val) / std_val

    daily_df["is_anomaly"] = daily_df["z_score"].abs() > threshold

    return daily_df.to_dict(orient="records")
