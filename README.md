# BhojanXpress

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

5. Run the application:
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

### git push
git init
git add .
git commit -am "initial commit"
git remote add origin https://github.com/omkargouda1204/BhojanXpress.git
git remote -v
git push origin master