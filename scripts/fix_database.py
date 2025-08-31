#!/usr/bin/env python3
"""
Simple script to update the Rating table with new columns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def main():
    app = create_app()
    
    with app.app_context():
        try:
            print("Checking database structure...")
            
            # Add helpful_count column
            try:
                db.engine.execute(text("ALTER TABLE rating ADD COLUMN helpful_count INT DEFAULT 0"))
                print("✓ Added helpful_count column to rating table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("✓ helpful_count column already exists")
                else:
                    print(f"Error adding helpful_count: {e}")
            
            # Add updated_at column
            try:
                db.engine.execute(text("ALTER TABLE rating ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
                print("✓ Added updated_at column to rating table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("✓ updated_at column already exists")
                else:
                    print(f"Error adding updated_at: {e}")
            
            # Create review_image table
            try:
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
                print("✓ Created review_image table")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ review_image table already exists")
                else:
                    print(f"Error creating review_image table: {e}")
            
            print("Database update completed successfully!")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()
