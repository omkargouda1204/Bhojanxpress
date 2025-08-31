import pymysql

# Database connection
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='system',
    database='bhojanxpress'
)

try:
    cursor = connection.cursor()
    
    # Add helpful_count column
    try:
        cursor.execute("ALTER TABLE rating ADD COLUMN helpful_count INT DEFAULT 0")
        print("✓ Added helpful_count column")
    except pymysql.Error as e:
        if "Duplicate column name" in str(e):
            print("✓ helpful_count column already exists")
        else:
            print(f"Error adding helpful_count: {e}")
    
    # Add updated_at column
    try:
        cursor.execute("ALTER TABLE rating ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        print("✓ Added updated_at column")
    except pymysql.Error as e:
        if "Duplicate column name" in str(e):
            print("✓ updated_at column already exists")
        else:
            print(f"Error adding updated_at: {e}")
    
    # Create review_image table
    try:
        cursor.execute("""
            CREATE TABLE review_image (
                id INT AUTO_INCREMENT PRIMARY KEY,
                rating_id INT NOT NULL,
                image_url VARCHAR(255),
                image_filename VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rating_id) REFERENCES rating(id) ON DELETE CASCADE
            )
        """)
        print("✓ Created review_image table")
    except pymysql.Error as e:
        if "already exists" in str(e):
            print("✓ review_image table already exists")
        else:
            print(f"Error creating review_image table: {e}")
    
    connection.commit()
    print("All database changes committed successfully!")

except Exception as e:
    print(f"Error: {e}")
    connection.rollback()

finally:
    cursor.close()
    connection.close()
