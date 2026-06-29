create table if not exists customers (
    customer_id varchar(50) primary key,
    customer_unique_id varchar(50),
    customer_zip_code_prefix varchar(10),
    customer_city varchar(100),
    customer_state varchar(10)
);

create table if not exists sellers (
    seller_id varchar(50) primary key,
    seller_zip_code_prefix varchar(10),
    seller_city varchar(100),
    seller_state varchar(10)
);

create table if not exists products (
    product_id varchar(50) primary key,
    product_category_name varchar(100),
    product_name_length integer,
    product_description_length integer,
    product_photos_qty integer,
    product_weight_g integer,
    product_length_cm integer,
    product_height_cm integer,
    product_width_cm integer
);

create table if not exists orders (
    order_id varchar(100) primary key,
    customer_id varchar(100),
    order_status varchar(20),
    order_purchase_timestamp timestamp,
    order_approved_at timestamp,
    order_delivered_carrier_date timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date timestamp
);

create table if not exists order_items (
    order_id varchar(50),
    order_item_id integer,
    product_id varchar(50),
    seller_id varchar(50),
    shipping_limit_date timestamp,
    price decimal(10,2),
    freight_value decimal(10,2),
    primary key (order_id, order_item_id)
);

create table if not exists order_payments (
    order_id varchar(50),
    payment_sequential integer,
    payment_type varchar(20),
    payment_installments integer,
    payment_value decimal(10,2),
    primary key (order_id, payment_sequential)
);

create table if not exists order_reviews (
    review_id varchar(50),
    order_id varchar(50),
    review_score integer,
    review_comment_title varchar(100),
    review_comment_message text,
    review_creation_date timestamp,
    review_answer_timestamp timestamp,
    primary key (review_id, order_id)
);

create table if not exists geolocation (
    geolocation_zip_code_prefix varchar(10),
    geolocation_lat decimal(10,8),
    geolocation_lng decimal(11,8),
    geolocation_city varchar(100),
    geolocation_state varchar(5)
);

create table if not exists product_category_name_translation (
    product_category_name varchar(100) primary key,
    product_category_name_english varchar(100)
);