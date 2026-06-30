alter table orders
add constraint fk_orders_customer
foreign key (customer_id) references customers(customer_id);

alter table order_items
add constraint fk_order_items_order
foreign key (order_id) references orders(order_id);

alter table order_items
add constraint fk_order_items_product
foreign key (product_id) references products(product_id);

alter table order_items
add constraint fk_order_items_seller
foreign key (seller_id) references sellers(seller_id);

alter table order_payments
add constraint fk_order_payments_order
foreign key (order_id) references orders(order_id);

alter table order_reviews
add constraint fk_order_reviews_order
foreign key (order_id) references orders(order_id);

alter table products
add constraint fk_products_category
foreign key (product_category_name) references product_category_name_translation(product_category_name);