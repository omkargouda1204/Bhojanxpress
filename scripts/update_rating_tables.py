#!/usr/bin/env python3
"""
Script to update the Rating table and create ReviewImage table
Run this script to add the new columns and table to your existing database.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from sqlalchemy import text

def update_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if helpful_count column exists in Rating table
            result = db.engine.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'rating' 
                AND COLUMN_NAME = 'helpful_count'
            """))
            
            if not result.fetchone():
                print("Adding helpful_count column to rating table...")
                db.engine.execute(text("ALTER TABLE rating ADD COLUMN helpful_count INT DEFAULT 0"))
            
            # Check if updated_at column exists in Rating table
            result = db.engine.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'rating' 
                AND COLUMN_NAME = 'updated_at'
            """))
            
            if not result.fetchone():
                print("Adding updated_at column to rating table...")
                db.engine.execute(text("ALTER TABLE rating ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
            
            # Check if ReviewImage table exists
            result = db.engine.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'review_image'
            """))
            
            if not result.fetchone():
                print("Creating review_image table...")
                db.engine.execute(text("""
                    CREATE TABLE review_image (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        rating_id INT NOT NULL,
                        image_url VARCHAR(255),
                        image_filename VARCHAR(255),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (rating_id) REFERENCES rating(id) ON DELETE CASCADE
                    )
                """))
            
            print("Database update completed successfully!")
            
        except Exception as e:
            print(f"Error updating database: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    if update_database():
        print("All database updates applied successfully!")
    else:
        print("Failed to update database. Please check the errors above.")
