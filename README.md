# BhojanXpress

BhojanXpress is a food delivery management system that includes dashboards for administrators, restaurants, and delivery agents.

## Recently Fixed Issues

The application had several issues that have been fixed. For details, see:
- [FIXES.md](FIXES.md) - Summary of issues fixed
- [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md) - Technical implementation details
- [QUICK_START.md](QUICK_START.md) - How to quickly get started with the application

## MySQL Setup Instructions

This application requires MySQL as the database. SQLite is not supported.

### Setup Steps:

1. Install MySQL Server if not already installed
2. Start MySQL Server
3. Create the database:
   ```sql
   CREATE DATABASE bhojanxpress;
   ```
4. Update the config_new.py with your MySQL credentials:
   ```python
   SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/bhojanxpress'
   ```
   Replace `username` and `password` with your actual MySQL credentials.

5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

6. Verify all required dependencies:
   ```
   python check_dependencies.py
   ```

7. Run the test script to ensure all fixes are working:
   ```
   python test_fixes.py
   ```
   You should see all tests PASSED. The test script verifies:
   - dateutil.relativedelta import works correctly
   - Order model relationship for items/order_items works
   - No duplicate routes exist in delivery_routes.py

8. Run the application:
   ```
   python run.py
   ```

### Common MySQL Connection Issues:

1. **Access denied error**: Check your MySQL username and password
2. **Database does not exist**: Run `CREATE DATABASE bhojanxpress;` in MySQL
3. **MySQL service not running**: Start your MySQL service

If you need to verify MySQL is running and your credentials, you can use:
```
mysql -u root -p
```
And enter your password when prompted.

## Login Credentials

### Admin Dashboard
- Email: admin@bhojanxpress.com
- Password: admin123

### Delivery Dashboard
- Email: delivery@bhojanxpress.com
- Username: delivery_boy
- Password: delivery123

### Restaurant Dashboard
- Email: restaurant@bhojanxpress.com
- Password: restaurant123

## Development Notes

### Running in Development Mode
```
flask run --host=0.0.0.0
```

### Git Commands Reference
```
git init
git add .
git commit -am "commit message"
git remote add origin https://github.com/omkargouda1204/BhojanXpress.git
git remote -v
git push origin master
```
