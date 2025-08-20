-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS bhojanxpress CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to the database
USE bhojanxpress;

-- Create tables
CREATE TABLE IF NOT EXISTS category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    reset_token VARCHAR(255),
    reset_token_expiry DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS food_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    category_id INT,
    category VARCHAR(50),
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    preparation_time INT DEFAULT 15,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS `order` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subtotal FLOAT NOT NULL,
    delivery_charge FLOAT DEFAULT 0.0,
    total_amount FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    delivery_address TEXT NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    estimated_delivery DATETIME,
    delivery_date DATETIME,
    special_instructions TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS order_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES `order`(id),
    FOREIGN KEY (food_item_id) REFERENCES food_item(id)
);

CREATE TABLE IF NOT EXISTS cart_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    food_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (food_item_id) REFERENCES food_item(id)
);

-- Insert default categories
INSERT INTO category (name) VALUES
    ('Appetizer'),
    ('Main Course'),
    ('Dessert'),
    ('Beverage'),
    ('Snacks');

-- Create admin user if it doesn't exist
INSERT IGNORE INTO user (username, email, password_hash, is_admin) 
VALUES ('admin', 'admin@bhojanxpress.com', 'pbkdf2:sha256:600000$1XMvJmZfMwRzh6YE$a32ae757bf398bb4ae1fd9b88c32bda3c0b1c1ba450473fbec10cd335e3d1d11', 1);
