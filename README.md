# BhojanXpress 🍽️

BhojanXpress is a comprehensive food delivery management system featuring modern UI design, enhanced security, and robust notification systems. The platform includes specialized dashboards for administrators, restaurants, delivery agents, and customers.

## 🚀 Latest Features & Enhancements

### ✨ Modern UI & Theme System
- **Global Theme System**: Consistent, attractive design across all pages with CSS variables
- **Gradient Design**: Professional gradient backgrounds and modern card layouts
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5 integration
- **Clean Navigation**: Improved user experience with consistent styling

### 🔐 Enhanced Security Features
- **OTP Verification**: Email-based 6-digit OTP verification for new registrations
- **Session Management**: Secure OTP storage with expiry handling
- **Email Integration**: Professional email templates for verification codes
- **Password Security**: Enhanced password hashing and validation
- **Account Protection**: Duplicate email/username prevention

### 🔔 Advanced Notification System
- **Real-time Notifications**: Comprehensive notification service for all user types
- **Automatic Triggers**: Order status updates and delivery notifications
- **Admin Notifications**: New user registrations and order management alerts
- **Delivery Agent Alerts**: Assignment notifications and status updates
- **Customer Updates**: Order confirmations and delivery tracking

### 🛡️ Security Improvements
- **CSRF Protection**: Enhanced form security across all pages
- **Input Validation**: Server-side validation for all user inputs
- **SQL Injection Prevention**: Parameterized queries and ORM usage
- **XSS Protection**: Output sanitization and secure templating

## � Latest Updates (October 2025)

### 🎨 UI/UX Improvements
- **Consistent Theme**: Updated all authentication pages (login, signup, forgot password, verify OTP) with solid backgrounds instead of transparent overlays
- **Professional Design**: Enhanced login and registration forms with clean white backgrounds and gradient page backgrounds
- **Color Scheme**: Implemented consistent purple-to-blue gradient theme across authentication pages
- **Enhanced Slider**: Updated home page carousel with 4 new food-focused slides featuring different meal categories

### 🔧 Technical Fixes
- **Email Configuration**: Updated SMTP settings with correct Gmail app password for BhojanXpress (bhojanaxpress@gmail.com)
- **Template Errors**: Fixed Order model relationship issues in admin delivery agent details page
- **Notification System**: Corrected notification API to use proper model attributes (content/notification_type)
- **Database Relations**: Fixed order-user relationships to prevent template rendering errors

### 📧 Email System
- **Gmail Integration**: Properly configured with app password: kiftwkdlakdxbxqe
- **Professional Templates**: Clean, responsive OTP email templates with BhojanXpress branding
- **SMTP Settings**: TLS encryption on port 587 for secure email delivery

### 🖼️ Image Updates
- **Food Slider**: Updated carousel to showcase 4 categories:
  1. Pizza and Fast Food
  2. Healthy Breakfast Options  
  3. Desserts and Ice Cream
  4. Mixed Food Varieties
- **Image Optimization**: 350px height with proper object-fit for consistent display

## �📋 System Requirements

### Database
- **MySQL 8.0+** (Required - SQLite not supported)
- Database: `bhojanxpress`

### Python Dependencies
- Flask 2.3+
- Flask-Login
- Flask-WTF
- Flask-Mail
- SQLAlchemy
- MySQL Connector Python
- Werkzeug

## 🛠️ Installation & Setup

### 1. Database Setup
```bash
# Install MySQL Server if not already installed
# Start MySQL Server
mysql -u root -p

# Create database
CREATE DATABASE bhojanxpress;
CREATE USER 'bhojan_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bhojanxpress.* TO 'bhojan_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Application Configuration
Update `config_new.py` with your settings:
```python
# Database Configuration
SQLALCHEMY_DATABASE_URI = 'mysql://bhojan_user:your_password@localhost/bhojanxpress'

# Email Configuration (for OTP)
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_app_password'

# Security
SECRET_KEY = 'your-secret-key-here'
WTF_CSRF_ENABLED = True
```

### 3. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Verify dependencies
python scripts/check_dependencies.py

# Run database migrations
python scripts/run_migrations.py

# Test system functionality
python scripts/test_fixes.py
```

### 4. Launch Application
```bash
# Development mode
python run.py

# Production mode
flask run --host=0.0.0.0 --port=5000
```

## 👥 User Roles & Access

### 🔧 Administrator Dashboard
- **Email**: admin@bhojanxpress.com
- **Password**: admin123
- **Features**: Complete system management, user oversight, order analytics, restaurant operations

### 🚚 Delivery Agent Dashboard  
- **Email**: delivery@bhojanxpress.com
- **Username**: delivery_boy
- **Password**: delivery123
- **Features**: Order assignments, delivery tracking, earnings management

### 👤 Customer Registration
- **New users**: Register with OTP verification required
- **Features**: Order placement, tracking, reviews, favorites

## 🏪 Restaurant Operations

**Note**: BhojanXpress is designed as a **single restaurant management system**. There is no separate restaurant login - all restaurant operations (menu management, order processing, inventory control) are handled through the **Administrator Dashboard**.

### Admin Restaurant Features:
- **Menu Management**: Add, edit, and manage all food items
- **Order Processing**: Accept, prepare, and manage all restaurant orders  
- **Inventory Control**: Stock management and availability updates
- **Kitchen Operations**: Order queue management and preparation tracking
- **Analytics**: Restaurant sales, performance metrics, and reporting

## 🎯 Key Features

### For Customers
- **Secure Registration**: Email OTP verification
- **Modern Interface**: Clean, responsive design
- **Order Management**: Place, track, and manage orders
- **Real-time Updates**: Notification system for order status
- **User Reviews**: Rate and review food items

### For Delivery Agents
- **Assignment Notifications**: Real-time order assignments
- **Route Optimization**: Efficient delivery planning
- **Earnings Tracking**: Commission and payment management
- **Status Updates**: Real-time delivery status reporting

### For Restaurant (Admin-Managed)
- **Single Restaurant System**: All restaurant operations managed by administrators
- **Menu Management**: Add, edit, and manage food items through admin panel
- **Order Processing**: Accept and prepare orders via admin dashboard  
- **Inventory Control**: Stock management system integrated in admin panel
- **Kitchen Operations**: Order queue and preparation status management
- **Analytics**: Sales and performance metrics accessible to administrators

### For Administrators
- **User Management**: Oversee all system users
- **Order Oversight**: Monitor all platform activities
- **System Analytics**: Comprehensive reporting
- **Notification Management**: System-wide communication

## 🔧 Advanced Configuration

### Email Setup (Required for OTP)
1. Enable 2-factor authentication on Gmail
2. Generate App Password
3. Update `config_new.py` with credentials
4. Test email functionality

### Database Optimization
```sql
-- Recommended MySQL settings
SET GLOBAL innodb_buffer_pool_size = 256M;
SET GLOBAL max_connections = 200;
```

### Performance Monitoring
- Enable Flask debug mode for development
- Use production WSGI server for deployment
- Monitor database query performance
- Implement caching for static content

## 🐛 Troubleshooting

### Common Issues

#### MySQL Connection Problems
```bash
# Check MySQL service
sudo systemctl status mysql

# Verify credentials
mysql -u bhojan_user -p bhojanxpress
```

#### OTP Email Issues
- Verify SMTP settings in config
- Check email credentials
- Ensure app password is used (not regular password)
- Test email connectivity

#### Theme/CSS Issues
- Clear browser cache
- Verify static file serving
- Check CSS file paths in templates

### Database Issues
```bash
# Reset database
python scripts/fix_database.py

# Update schema
python scripts/run_migrations.py

# Verify integrity
python scripts/check_users_schema.py
```

## 🚀 Deployment

### Production Checklist
- [ ] Configure production database
- [ ] Set up email service
- [ ] Enable HTTPS
- [ ] Configure environment variables
- [ ] Set up monitoring
- [ ] Configure backup strategy

### Environment Variables
```bash
export FLASK_ENV=production
export DATABASE_URL="mysql://user:pass@localhost/bhojanxpress"
export MAIL_SERVER="smtp.gmail.com"
export SECRET_KEY="your-production-secret-key"
```

## 📚 Documentation

### Additional Resources
- [FIXES.md](FIXES.md) - Recent bug fixes and improvements
- [TECHNICAL_DETAILS.md](TECHNICAL_DETAILS.md) - Technical implementation details
- [QUICK_START.md](QUICK_START.md) - Quick setup guide
- [API Documentation](docs/api.md) - API endpoints reference

### Development Commands
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/omkargouda1204/BhojanXpress.git
git push origin master

# Development server
flask run --debug --host=0.0.0.0

# Database migrations
flask db upgrade
flask db migrate -m "Description"
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Make changes and test
5. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Include docstrings for functions
- Write unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please contact:
- **Email**: support@bhojanxpress.com
- **Issues**: GitHub Issues page
- **Documentation**: Project Wiki

---

**BhojanXpress** - Delivering Excellence in Food Management 🚀
