CREATE TYPE "example-dataset".order_status AS ENUM ('approved','canceled','created','delivered','invoiced','processing','shipped','unavailable');
ALTER TYPE "example-dataset".order_status OWNER TO postgres;
COMMENT ON TYPE "example-dataset".order_status IS E'Defines the current status of the order';
CREATE TABLE "example-dataset".orders (
	id char(32) NOT NULL,
	customer_id char(32) NOT NULL,
	status "example-dataset".order_status NOT NULL,
	purchase_timestamp timestamp NOT NULL,
	approved_at timestamp,
	delivered_carrier_date timestamp,
	delivered_customer_date timestamp,
	estimated_delivery_date timestamp
);
COMMENT ON TABLE "example-dataset".orders IS E'Contains all orders';
COMMENT ON COLUMN "example-dataset".orders.id IS E'ID of the order';
COMMENT ON COLUMN "example-dataset".orders.customer_id IS E'ID of the customer who ordered';
COMMENT ON COLUMN "example-dataset".orders.status IS E'Status of the order';
COMMENT ON COLUMN "example-dataset".orders.purchase_timestamp IS E'Timestamp when the order was placed';
COMMENT ON COLUMN "example-dataset".orders.approved_at IS E'Date when the order was approved';
COMMENT ON COLUMN "example-dataset".orders.delivered_carrier_date IS E'Date when the order was delivered to the carrier';
COMMENT ON COLUMN "example-dataset".orders.delivered_customer_date IS E'Date when the order was delivered to the customer';
COMMENT ON COLUMN "example-dataset".orders.estimated_delivery_date IS E'Date of the estimated delivery';
ALTER TABLE "example-dataset".orders OWNER TO postgres;
CREATE TABLE "example-dataset".customers (
	id char(32) NOT NULL,
	zip_code_prefix varchar(5) NOT NULL,
	city varchar NOT NULL,
	state char(2) NOT NULL
);
COMMENT ON COLUMN "example-dataset".customers.id IS E'ID of the customer';
COMMENT ON COLUMN "example-dataset".customers.zip_code_prefix IS E'Prefix of the customers ZIP Code';
COMMENT ON COLUMN "example-dataset".customers.city IS E'City where the customer lives';
COMMENT ON COLUMN "example-dataset".customers.state IS E'State where the customers lives';
ALTER TABLE "example-dataset".customers OWNER TO postgres;
CREATE TABLE "example-dataset".order_items (
	order_id char(32) NOT NULL,
	item_id smallint NOT NULL,
	product_id char(32) NOT NULL,
	seller_id char(32) NOT NULL,
	price decimal NOT NULL
);
COMMENT ON COLUMN "example-dataset".order_items.order_id IS E'ID of the order';
COMMENT ON COLUMN "example-dataset".order_items.product_id IS E'ID of the orderd product';
COMMENT ON COLUMN "example-dataset".order_items.seller_id IS E'ID of the seller';
COMMENT ON COLUMN "example-dataset".order_items.price IS E'Price of the orederd item';
ALTER TABLE "example-dataset".order_items OWNER TO postgres;
CREATE TABLE "example-dataset".products (
	id char(32) NOT NULL,
	category varchar(100),
	name_length smallint,
	description_length smallint,
	photos_count smallint,
	weight bigint
);
COMMENT ON TABLE "example-dataset".products IS E'All available products';
COMMENT ON COLUMN "example-dataset".products.id IS E'ID of the product';
COMMENT ON COLUMN "example-dataset".products.category IS E'Category where the product is in';
COMMENT ON COLUMN "example-dataset".products.name_length IS E'Length of the name in characters';
COMMENT ON COLUMN "example-dataset".products.description_length IS E'Length of the description in characters';
COMMENT ON COLUMN "example-dataset".products.photos_count IS E'Count of how many photos were posted for this product';
COMMENT ON COLUMN "example-dataset".products.weight IS E'Weight of the product in gram';
ALTER TABLE "example-dataset".products OWNER TO postgres;
CREATE TABLE "example-dataset".sellers (
	id char(32) NOT NULL,
	zip_code_prefix varchar(5) NOT NULL,
	city varchar(50) NOT NULL,
	state char(2) NOT NULL
);
COMMENT ON TABLE "example-dataset".sellers IS E'All sellers';
COMMENT ON COLUMN "example-dataset".sellers.id IS E'ID of the seller';
COMMENT ON COLUMN "example-dataset".sellers.zip_code_prefix IS E'First five digits of sellers zip code';
COMMENT ON COLUMN "example-dataset".sellers.city IS E'City where the seller is located';
COMMENT ON COLUMN "example-dataset".sellers.state IS E'State where the seller is located';
ALTER TABLE "example-dataset".sellers OWNER TO postgres;
ALTER TABLE "example-dataset".orders ADD CONSTRAINT customer_id FOREIGN KEY (customer_id) REFERENCES "example-dataset".customers (id) MATCH SIMPLE ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "example-dataset".order_items ADD CONSTRAINT order_id FOREIGN KEY (order_id) REFERENCES "example-dataset".orders (id) MATCH SIMPLE ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "example-dataset".order_items ADD CONSTRAINT product_id FOREIGN KEY (product_id) REFERENCES "example-dataset".products (id) MATCH SIMPLE ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "example-dataset".order_items ADD CONSTRAINT seller_id FOREIGN KEY (seller_id) REFERENCES "example-dataset".sellers (id) MATCH SIMPLE ON DELETE NO ACTION ON UPDATE NO ACTION;
