import pandas as pd
import psycopg

LEAKY_COLUMNS_NOTE = """
Explicitly NOT used, and why:
- order_delivered_customer_date  -> this defines the label itself
- order_delivered_carrier_date   -> happens after the prediction point
- order_reviews.*                -> post-delivery, often caused BY the delay
- seller historical late-rate    -> deferred, needs time-aware aggregation
"""

FEATURE_COLS = [
    "purchase_dayofweek",
    "purchase_month",
    "purchase_hour",
    "promised_window_days",
    "customer_state",
    "seller_state",
    "cross_state_shipping",
    "n_items",
    "n_distinct_sellers",
    "total_price",
    "total_freight",
    "total_weight_g",
    "max_length_cm",
    "max_height_cm",
    "max_width_cm",
]

def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    ts = pd.to_datetime(df["order_purchase_timestamp"])
    df["purchase_dayofweek"] = ts.dt.dayofweek       # 0=Mon .. 6=Sun
    df["purchase_month"] = ts.dt.month
    df["purchase_hour"] = ts.dt.hour
    # Promised delivery window, in days — known upfront, legitimate signal.
    # A tight promised window is inherently riskier than a generous one.
    est = pd.to_datetime(df["order_estimated_delivery_date"])
    df["promised_window_days"] = (est - ts).dt.days
    # Cross-state shipping is a reasonable proxy for logistics complexity.
    df["cross_state_shipping"] = (
        df["customer_state"] != df["seller_state"]
    ).astype(int)
    return df

def load_raw_orders(conn: psycopg.Connection) -> pd.DataFrame:
    query = """
        SELECT
            o.order_id,
            o.customer_id,
            o.order_purchase_timestamp,
            o.order_estimated_delivery_date,
            o.order_delivered_customer_date,  -- used ONLY to build the label
            c.customer_state,
            c.customer_zip_code_prefix
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_status = 'delivered'
        AND o.order_delivered_customer_date IS NOT NULL
    """
    return pd.read_sql(query, conn)

def load_order_items_agg(conn: psycopg.Connection) -> pd.DataFrame:
    query = """
        SELECT
            oi.order_id,
            oi.seller_id,
            oi.price,
            oi.freight_value,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm,
            s.seller_state
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN sellers s ON s.seller_id = oi.seller_id
    """
    items = pd.read_sql(query, conn)
    agg = items.groupby("order_id").agg(
        n_items=("seller_id", "count"),
        n_distinct_sellers=("seller_id", "nunique"),
        total_price=("price", "sum"),
        total_freight=("freight_value", "sum"),
        total_weight_g=("product_weight_g", "sum"),
        max_length_cm=("product_length_cm", "max"),
        max_height_cm=("product_height_cm", "max"),
        max_width_cm=("product_width_cm", "max"),
        seller_state=("seller_state", "first"),
    ).reset_index()
    return agg

def build_features(orders: pd.DataFrame, items_agg: pd.DataFrame) -> pd.DataFrame:
    df = orders.merge(items_agg, on="order_id", how="inner")
    # ---- Label ----
    # Late = actually delivered after the promised estimated date.
    # This is the ONLY place delivered_customer_date is used.
    df["is_late"] = (
        df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    ).astype(int)
    df = _add_derived_features(df)
    return df[["order_id", *FEATURE_COLS, "is_late"]]

def get_training_data(conn: psycopg.Connection) -> pd.DataFrame:
    orders = load_raw_orders(conn)
    items_agg = load_order_items_agg(conn)
    return build_features(orders, items_agg)

def load_single_order_raw(conn: psycopg.Connection, order_id: str) -> pd.DataFrame:
    query = """
        SELECT
            o.order_id,
            o.order_purchase_timestamp,
            o.order_estimated_delivery_date,
            c.customer_state,
            c.customer_zip_code_prefix
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_id = %s
    """
    return pd.read_sql(query, conn, params=(order_id,))

def load_single_order_items_agg(conn: psycopg.Connection, order_id: str) -> pd.DataFrame:
    query = """
        SELECT
            oi.order_id,
            oi.seller_id,
            oi.price,
            oi.freight_value,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm,
            s.seller_state
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        JOIN sellers s ON s.seller_id = oi.seller_id
        WHERE oi.order_id = %s
    """
    items = pd.read_sql(query, conn, params=(order_id,))
    return items.groupby("order_id").agg(
        n_items=("seller_id", "count"),
        n_distinct_sellers=("seller_id", "nunique"),
        total_price=("price", "sum"),
        total_freight=("freight_value", "sum"),
        total_weight_g=("product_weight_g", "sum"),
        max_length_cm=("product_length_cm", "max"),
        max_height_cm=("product_height_cm", "max"),
        max_width_cm=("product_width_cm", "max"),
        seller_state=("seller_state", "first"),
    ).reset_index()

def build_inference_features(order_row: pd.DataFrame, items_agg_row: pd.DataFrame) -> dict | None:
    df = order_row.merge(items_agg_row, on="order_id", how="inner")
    if df.empty:
        return None
    df = _add_derived_features(df)
    return df.iloc[0][FEATURE_COLS].to_dict()