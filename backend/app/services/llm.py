import re
import logging
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger("app.services.llm")

# Initialize clients if keys exist
gemini_available = False
openai_available = False

if settings.gemini_api_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        gemini_available = True
        logger.info("Gemini LLM service initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")

if settings.openai_api_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=settings.openai_api_key)
        openai_available = True
        logger.info("OpenAI LLM service initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")


def clean_sql_query(sql: str) -> str:
    """
    Cleans markdown formatting and leading/trailing whitespace from LLM SQL output.
    """
    # Remove markdown code block fences if present
    sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```\s*", "", sql)
    # Remove surrounding whitespace
    return sql.strip()


def validate_sql_safety(sql: str) -> tuple[bool, Optional[str]]:
    """
    Validates if the generated SQL query is safe to execute.
    Returns (is_safe, error_reason).
    """
    cleaned = clean_sql_query(sql)
    
    # Must start with SELECT (ignoring leading comments/whitespace)
    # Strip single line comments -- and multi-line comments /* */
    normalized = re.sub(r"--.*", "", cleaned)
    normalized = re.sub(r"/\*.*?\*/", "", normalized, flags=re.DOTALL)
    normalized = normalized.strip()
    
    if not normalized.upper().startswith("SELECT"):
        return False, "Query must start with SELECT (only read-only operations allowed)"
        
    # Forbidden keywords that mutate state or access catalog tables metadata
    forbidden_keywords = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", 
        r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bREPLACE\b", 
        r"\bGRANT\b", r"\bREVOKE\b", r"\bINTO\b", r"\bEXEC\b", 
        r"\bEXECUTE\b", r"\bCOPY\b", r"\bMERGE\b", r"\bDATABASE\b"
    ]
    
    for kw in forbidden_keywords:
        if re.search(kw, normalized, re.IGNORECASE):
            return False, f"Query contains forbidden keyword: {kw.strip(r'\\b')}"
            
    return True, None


def call_llm(prompt: str, system_instruction: Optional[str] = None) -> str:
    """
    Generic LLM call helper supporting Gemini and OpenAI, falling back if keys are missing.
    """
    # Use selected provider
    provider = settings.llm_provider.lower()
    
    if provider == "gemini" and gemini_available:
        try:
            import google.generativeai as genai
            model_name = "gemini-1.5-flash"
            
            # Combine system instruction into the configuration if supported, or prepended to prompt
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            if openai_available:
                provider = "openai"  # Fallback to OpenAI
            else:
                raise e

    if provider == "openai" and openai_available:
        try:
            sys_instruct = system_instruction or "You are a helpful business analytics assistant."
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sys_instruct},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise e

    # Fallback when no API keys are available
    logger.warning("No functional LLM provider available. Returning mock response.")
    return get_mock_llm_response(prompt)


def generate_sql(question: str, db_dialect: str) -> str:
    """
    Translates user query into SQL based on the database schema and dialect.
    """
    system_instruction = f"""You are a database expert translating natural language questions into safe, executable {db_dialect} SQL.
The database schema consists of these tables:

1. Table: regions
   Columns:
   - id: INTEGER PRIMARY KEY
   - name: VARCHAR(255) UNIQUE (e.g. 'North', 'South', 'East', 'West', 'Central')

2. Table: products
   Columns:
   - id: INTEGER PRIMARY KEY
   - name: VARCHAR(255)
   - category: VARCHAR(255) (e.g. 'Electronics', 'Clothing', 'Office Supplies', 'Furniture')
   - price: NUMERIC(10, 2)
   - sku: VARCHAR(50) UNIQUE

3. Table: customers
   Columns:
   - id: INTEGER PRIMARY KEY
   - first_name: VARCHAR(255)
   - last_name: VARCHAR(255)
   - email: VARCHAR(255) UNIQUE
   - region_id: INTEGER (FOREIGN KEY -> regions.id)
   - created_at: TIMESTAMP

4. Table: orders
   Columns:
   - id: INTEGER PRIMARY KEY
   - customer_id: INTEGER (FOREIGN KEY -> customers.id)
   - order_date: TIMESTAMP
   - status: VARCHAR(50) (e.g. 'Completed', 'Pending', 'Cancelled')
   - total_amount: NUMERIC(12, 2)

5. Table: order_items
   Columns:
   - id: INTEGER PRIMARY KEY
   - order_id: INTEGER (FOREIGN KEY -> orders.id)
   - product_id: INTEGER (FOREIGN KEY -> products.id)
   - quantity: INTEGER
   - unit_price: NUMERIC(10, 2)
   - total_price: NUMERIC(12, 2)

6. Table: daily_revenue_kpis (Stores daily summarized KPIs)
   Columns:
   - date: DATE PRIMARY KEY
   - total_revenue: NUMERIC(12, 2)
   - order_count: INTEGER
   - anomaly_detected: BOOLEAN
   - anomaly_score: FLOAT
   - summary_report: TEXT

Rules:
1. ONLY return the raw, plain SQL query. Do NOT wrap the query in code fences like ```sql. No comments, no explanations, just SQL.
2. The query MUST be a SELECT statement. Writing or editing data is strictly forbidden.
3. Write clean {db_dialect}-compatible SQL. 
   - For formatting dates (e.g. Year-Month 'YYYY-MM'):
     * If PostgreSQL: use TO_CHAR(order_date, 'YYYY-MM')
     * If SQLite: use strftime('%Y-%m', order_date)
   - For extracting date parts:
     * If PostgreSQL: EXTRACT(QUARTER FROM order_date) or EXTRACT(MONTH FROM order_date)
     * If SQLite: (CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3 for quarter
4. Limit the result set to a maximum of 100 rows unless explicitly specified.
"""

    prompt = f"Convert this question into a {db_dialect} SQL query: '{question}'"
    raw_sql = call_llm(prompt, system_instruction)
    return clean_sql_query(raw_sql)


def generate_insight(data: Any, question: str) -> str:
    """
    Generates a brief business insight explaining the tabular data query results.
    """
    system_instruction = "You are a senior data analyst and business intelligence consultant."
    prompt = f"""Given the following question asked by a business user:
"{question}"

And the resulting dataset returned from the database:
{str(data)}

Write a professional, plain-English summary of these findings. Highlight key trends, important observations, or business recommendations. Keep it under 4 sentences, focusing on actionable business insights."""

    return call_llm(prompt, system_instruction).strip()


def generate_daily_summary(kpis: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> str:
    """
    Generates a daily GenAI summary of business metrics, anomalies, and trends.
    """
    system_instruction = "You are an executive business writer specialized in daily sales reports."
    prompt = f"""Generate a daily business summary report. Here is the metadata for yesterday's KPIs:
- Date: {kpis.get('date')}
- Revenue: ${kpis.get('total_revenue'):,.2f}
- Orders: {kpis.get('order_count')}
- Average Order Value (AOV): ${kpis.get('aov', 0):,.2f}

Anomalies detected in recent history:
{str(anomalies[-5:]) if anomalies else "None"}

Write a concise, executive sales report. Describe how sales did yesterday, note if any anomalies or outliers were detected, and offer a business recommendation for inventory or regional focus. Format the output with clear professional structure (under 150 words)."""

    return call_llm(prompt, system_instruction).strip()


def get_mock_llm_response(prompt: str) -> str:
    """
    Returns mock responses for testing and local running when API keys are absent.
    """
    p_lower = prompt.lower()
    
    # Check if this is a SQL generation request
    if "convert this question" in p_lower:
        # Match typical questions to mock working SQL
        if "region" in p_lower:
            return """SELECT r.name as region_name, SUM(oi.total_price) as revenue 
                      FROM regions r 
                      JOIN customers c ON c.region_id = r.id 
                      JOIN orders o ON o.customer_id = c.id 
                      JOIN order_items oi ON oi.order_id = o.id 
                      WHERE o.status = 'Completed' 
                      GROUP BY r.name 
                      ORDER BY revenue DESC;"""
        elif "product" in p_lower:
            return """SELECT p.name, SUM(oi.quantity) as total_sold, SUM(oi.total_price) as revenue 
                      FROM products p 
                      JOIN order_items oi ON oi.product_id = p.id 
                      GROUP BY p.name 
                      ORDER BY revenue DESC 
                      LIMIT 5;"""
        elif "monthly" in p_lower or "trend" in p_lower:
            # Dialect sensitive mock
            if "sqlite" in p_lower:
                return """SELECT strftime('%Y-%m', o.order_date) as month, SUM(o.total_amount) as revenue 
                          FROM orders o 
                          WHERE o.status = 'Completed' 
                          GROUP BY month 
                          ORDER BY month;"""
            else:
                return """SELECT TO_CHAR(o.order_date, 'YYYY-MM') as month, SUM(o.total_amount) as revenue 
                          FROM orders o 
                          WHERE o.status = 'Completed' 
                          GROUP BY month 
                          ORDER BY month;"""
        # Default fallback query
        return "SELECT * FROM products LIMIT 5;"
        
    # Check if this is a general insight request
    if "question asked by a business user" in p_lower:
        return "Our sales analysis shows stable performance. The products listed represent our key drivers. We recommend optimizing inventory levels to meet sustained demand across all active product categories."

    # Check if this is a daily summary request
    if "daily business summary report" in p_lower:
        return "Daily Sales Report: Yesterday saw steady performance with stable transaction volumes. Average Order Value remains healthy. No significant statistical revenue anomalies were detected in the recent period. We recommend focusing marketing outreach on products with higher profit margins to boost total overall yield."
        
    return "Demo Mode: Set GEMINI_API_KEY or OPENAI_API_KEY environment variable to generate live insights."
