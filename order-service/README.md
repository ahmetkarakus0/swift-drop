# tables

## baskets
- id: uuid, primary key
- user_id: uuid (no foreign, users exists in another service)
- restaurant_id: uuid (no foreign, restaurants exists in another service)
- created_at: timestamp
- updated_at: timestamp

## basket_items
- id: uuid, primary key
- basket_id: uuid, foreign key to baskets.id
- item.id: uuid (no foreign, items exists in another service)
- item_name: string 
- quantity: integer
- price: decimal
- created_at: timestamp
- updated_at: timestamp

## orders
- id: uuid, primary key
- user_id: uuid (no foreign, users exists in another service)
- restaurant_id: uuid (no foreign, restaurants exists in another service)
- courier_id: uuid | null (no foreign, couriers exists in another service)
- status: enum (pending, confirmed, preparing, ready_for_pickup, on_the_way, delivered, cancelled)
- total_price: decimal
- delivery_address: string
- created_at: timestamp
- updated_at: timestamp

## order_items
- id: uuid, primary key
- order_id: uuid, foreign key to orders.id
- item_id: uuid (no foreign, items exists in another service)
- item_name: string
- quantity: integer
- price: decimal