"""Add is_helpful column to review_helpful table"""

import pymysql
import sys
import os

def add_is_helpful_column():
    """Add the missing is_helpful column to review_helpful table"""
    try:
        # Connect to database
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='system',  # Add your MySQL password if any
            database='bhojanxpress'
        )

        cursor = connection.cursor()

        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE table_schema = 'bhojanxpress' 
            AND table_name = 'review_helpful' 
            AND column_name = 'is_helpful'
        """)

        column_exists = cursor.fetchone()[0] > 0

        if not column_exists:
            # Add the is_helpful column
            cursor.execute("""
                ALTER TABLE review_helpful 
                ADD COLUMN is_helpful TINYINT(1) NOT NULL DEFAULT 1
            """)

            connection.commit()
            print("✅ Successfully added is_helpful column to review_helpful table")
        else:
            print("ℹ️ Column is_helpful already exists in review_helpful table")

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"❌ Error adding is_helpful column: {e}")

if __name__ == "__main__":
    add_is_helpful_column()
