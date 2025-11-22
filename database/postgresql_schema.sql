-- PostgreSQL Schema for BhojanXpress
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    reset_token VARCHAR(255),
    reset_token_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS food_item (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    category_id INT,
    category VARCHAR(50),
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    preparation_time INT DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS "order" (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    subtotal FLOAT NOT NULL,
    delivery_charge FLOAT DEFAULT 0.0,
    total_amount FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    delivery_address TEXT NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estimated_delivery TIMESTAMP,
    delivery_date TIMESTAMP,
    special_instructions TEXT,
    FOREIGN KEY (user_id) REFERENCES "user"(id)
);

CREATE TABLE IF NOT EXISTS order_item (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES "order"(id),
    FOREIGN KEY (food_item_id) REFERENCES food_item(id)
);

CREATE TABLE IF NOT EXISTS cart_item (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id),
    FOREIGN KEY (food_item_id) REFERENCES food_item(id)
);

CREATE TABLE IF NOT EXISTS review (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    food_item_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id),
    FOREIGN KEY (food_item_id) REFERENCES food_item(id)
);

CREATE TABLE IF NOT EXISTS slider_image (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    subtitle VARCHAR(200),
    image_filename VARCHAR(255) NOT NULL,
    image_url VARCHAR(500),
    button_text VARCHAR(50) DEFAULT 'ORDER NOW',
    button_link VARCHAR(200) DEFAULT '/menu',
    button_color VARCHAR(20) DEFAULT 'warning',
    offer_text VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default categories
INSERT INTO category (name) VALUES
    ('Appetizer'),
    ('Main Course'),
    ('Dessert'),
    ('Beverage'),
    ('Snacks')
ON CONFLICT (name) DO NOTHING;

-- Create admin user
-- Password: admin123 (hashed with pbkdf2:sha256)
INSERT INTO "user" (username, email, password_hash, is_admin) 
VALUES ('admin', 'admin@bhojanxpress.com', 'pbkdf2:sha256:600000$1XMvJmZfMwRzh6YE$a32ae757bf398bb4ae1fd9b88c32bda3c0b1c1ba450473fbec10cd335e3d1d11', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_food_item_category ON food_item(category_id);
CREATE INDEX IF NOT EXISTS idx_order_user ON "order"(user_id);
CREATE INDEX IF NOT EXISTS idx_order_status ON "order"(status);
CREATE INDEX IF NOT EXISTS idx_cart_user ON cart_item(user_id);
CREATE INDEX IF NOT EXISTS idx_review_food ON review(food_item_id);
