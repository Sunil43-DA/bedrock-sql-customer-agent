
-- Sample customer table for our AI data agent.
-- This script is for the eventual Redshift database.

CREATE TABLE customers (
    customer_id INT,
    customer_name VARCHAR(100),
    city VARCHAR(50),
    total_spend DECIMAL(10, 2),
    customer_status VARCHAR(20)
);

INSERT INTO customers VALUES
(101, 'Alice Brown', 'London', 1250.50, 'Active'),
(102, 'David Smith', 'Manchester', 800.00, 'Active'),
(103, 'Priya Patel', 'Birmingham', 2200.75, 'Active'),
(104, 'James Wilson', 'Leeds', 450.25, 'Inactive'),
(105, 'Sara Khan', 'London', 1750.00, 'Active');

SELECT * FROM customers;