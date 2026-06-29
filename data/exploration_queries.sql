-- viewing the data
select * from orders limit 10;

-- counting orders by status delivered vs invoiced
select order_status, count(*) as order_count from orders
group by order_status order by order_count desc;

-- joining orders with customers to see where orders come from
select customers.customer_state,
count(orders.order_id) as order_count
from orders join customers on orders.customer_id = customers.customer_id
group by customers.customer_state
order by order_count desc
limit 15;

-- average, min, max order value by payment type
select payment_type, count(*) as total_orders,
round(avg(payment_value),2) as avg_order_value,
round(min(payment_value),2) as min_order_value,
round(max(payment_value),2) as max_order_value 
from order_payments
group by payment_type
order by total_orders desc;

-- top 10 product categories by revenue
select product_category_name_translation.product_category_name_english,
count(order_items.order_id) as total_orders,
round(sum(order_items.price),2) as total_revenue
from order_items join products on
order_items.product_id = products.product_id
join product_category_name_translation on
products.product_category_name = product_category_name_translation.product_category_name
group by product_category_name_translation.product_category_name_english
order by total_revenue desc
limit 15;

-- monthly order volume in 2018
select
date_trunc('month', order_purchase_timestamp) as month,
count(*) as total_orders,
round(avg(payment_value), 2) as avg_payment
from orders
join order_payments on orders.order_id = order_payments.order_id
where order_purchase_timestamp >= '2018-01-01' 
and order_purchase_timestamp < '2019-01-01'
and order_status = 'delivered'
group by date_trunc('month', order_purchase_timestamp)
order by month;

-- delivery delay analysis
select order_id, order_estimated_delivery_date, 
order_delivered_customer_date,
extract(day from(order_delivered_customer_date - order_estimated_delivery_date)) as delay_days
case when order_delivered_customer_date > order_estimated_delivery_date then 'late'
else 'on_time' end as delivery_status
from orders
where order_status = 'delivered' and 
order_delivered_customer_date is not null
limit 20;

-- overall late delivery date
select
case when order_delivered_customer_date > order_estimated_delivery_date then 'late'
else 'on_time' end as delivery_status,
count(*) as total_orders,
round(count(*) * 100.0 / sum(count(*)) over (), 2) as percentage
from orders
where order_status = 'delivered' and 
order_delivered_customer_date is not null
group by delivery_status

-- feature rich dataset for ML model
select 
    o.order_id,
    o.order_status,
    extract(dow from o.order_purchase_timestamp) as purchase_day_of_week,
    extract(month from o.order_purchase_timestamp) as purchase_month,
    count(oi.order_item_id) as item_count,
    round(sum(oi.price), 2) as total_price,
    round(sum(oi.freight_value), 2) as total_freight,
    case 
        when order_delivered_customer_date > order_estimated_delivery_date 
        then 1
        else 0
    end as is_late
from orders o
join order_items oi on o.order_id = oi.order_id
where o.order_status = 'delivered'
and o.order_delivered_customer_date is not null
group by
    o.order_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date
limit 20;

-- top 10 sellers by revenue with their late delivery rate
select 
    s.seller_id,
    s.seller_state,
    count(distinct o.order_id) as total_orders,
    round(sum(oi.price), 2) as total_revenue,
    round(avg(r.review_score), 2) as avg_review_score,
    round(
        sum(case when o.order_delivered_customer_date > o.order_estimated_delivery_date then 1 else 0 end) 
        * 100.0 / count(*), 2
    ) as late_delivery_rate
from sellers s
join order_items oi on s.seller_id = oi.seller_id
join orders o on oi.order_id = o.order_id
join order_reviews r on o.order_id = r.order_id
where o.order_status = 'delivered' and o.order_delivered_customer_date is not null
group by s.seller_id, s.seller_state
order by total_revenue desc
limit 20;