CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

INSERT INTO products (name, price) VALUES
('Hackathon Hoodie', 45.00),
('Cloud Native Coffee Mug', 15.50),
('Sentinel Twin Stickers', 3.00);
