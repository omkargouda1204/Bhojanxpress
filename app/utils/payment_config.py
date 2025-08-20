# PayPal API Configuration
PAYPAL_CLIENT_ID = "Aa7QSyi4UITTmbADn7O1t6IO_LuR65xWD7pCxLEjCnIZR_oKtwXmHv2BkCmygz-CSzc77gxo-2Y-ZIbP"
PAYPAL_SECRET = "EF1cuY4BGNyr6S8fl2LA6z8gCsUhj09qGDTh36tS_JwtOjin4gu_qa6Qgb_oj4wArimK5_4RQSkJD8ls"
PAYPAL_MODE = "sandbox"  # Change to "live" for production

# URLs for PayPal API endpoints
PAYPAL_API_BASE_URL = "https://api-m.sandbox.paypal.com"  # Change to https://api-m.paypal.com for production

# Payment configuration
CURRENCY = "INR"  # For display purposes in your app
PAYPAL_CURRENCY = "USD"  # PayPal transactions will use USD
CONVERSION_RATE = 0.012  # Approximate INR to USD conversion rate (1 INR = 0.012 USD)
