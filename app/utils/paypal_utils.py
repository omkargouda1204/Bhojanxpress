import requests
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from app.utils.payment_config import (
    PAYPAL_CLIENT_ID,
    PAYPAL_SECRET,
    PAYPAL_API_BASE_URL,
    CURRENCY,
    PAYPAL_CURRENCY,
    CONVERSION_RATE
)

class PayPalClient:
    def __init__(self):
        # Use configuration values instead of hardcoded credentials
        self.client_id = "Aa7QSyi4UITTmbADn7O1t6IO_LuR65xWD7pCxLEjCnIZR_oKtwXmHv2BkCmygz-CSzc77gxo-2Y-ZIbP"
        self.client_secret = "EF1cuY4BGNyr6S8fl2LA6z8gCsUhj09qGDTh36tS_JwtOjin4gu_qa6Qgb_oj4wArimK5_4RQSkJD8ls"
        self.api_base_url = "https://api.sandbox.paypal.com"
        self.currency = CURRENCY
        self.paypal_currency = PAYPAL_CURRENCY
        self.conversion_rate = CONVERSION_RATE

    def _convert_to_paypal_currency(self, inr_amount):
        """Convert INR amount to USD for PayPal"""
        if inr_amount is None:
            return "0.00"
        usd_amount = float(inr_amount) * self.conversion_rate
        return self._format_amount(usd_amount)

    def _format_amount(self, amount):
        """Format amount to 2 decimal places as required by PayPal"""
        if amount is None:
            return "0.00"
        # Convert to Decimal for precise formatting
        decimal_amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return str(decimal_amount)

    def get_access_token(self):
        """Get PayPal OAuth access token"""
        url = f"{self.api_base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        auth = (self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(url, auth=auth, data=data, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                print(f"Error getting access token: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error getting access token: {e}")
            return None

    def create_order(self, order_data):
        """Create a PayPal order with currency conversion from INR to USD"""
        access_token = self.get_access_token()
        if not access_token:
            return {"success": False, "error": "Failed to get PayPal access token"}

        url = f"{self.api_base_url}/v2/checkout/orders"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": f"order-{order_data.get('order_id')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

        # Format order items for PayPal with currency conversion
        items = []
        item_total_usd = Decimal('0')

        for item in order_data.get('items', []):
            # Convert INR price to USD
            unit_price_usd = self._convert_to_paypal_currency(item.get('price'))
            quantity = str(item.get('quantity'))

            items.append({
                "name": item.get('name')[:127],  # PayPal name limit
                "quantity": quantity,
                "unit_amount": {
                    "currency_code": self.paypal_currency,
                    "value": unit_price_usd
                }
            })

            # Calculate item total in USD
            item_total_usd += Decimal(unit_price_usd) * Decimal(quantity)

        # Convert amounts and calculate total in USD based on breakdown
        subtotal_usd = Decimal(self._convert_to_paypal_currency(order_data.get('subtotal')))
        delivery_charge_usd = Decimal(self._convert_to_paypal_currency(order_data.get('delivery_charge', 0)))
        gst_amount_usd = Decimal(self._convert_to_paypal_currency(order_data.get('gst_amount', 0)))
        discount_amount_usd = Decimal(self._convert_to_paypal_currency(
            (order_data.get('discount_amount', 0) or 0) +
            (order_data.get('coupon_discount', 0) or 0)
        ))
        # Calculate and format all breakdown values
        calculated_total_usd = subtotal_usd + delivery_charge_usd + gst_amount_usd - discount_amount_usd
        subtotal_usd = subtotal_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        delivery_charge_usd = delivery_charge_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        gst_amount_usd = gst_amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount_amount_usd = discount_amount_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount_usd = calculated_total_usd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        # Convert back to strings
        subtotal_usd = str(subtotal_usd)
        delivery_charge_usd = str(delivery_charge_usd)
        gst_amount_usd = str(gst_amount_usd)
        discount_amount_usd = str(discount_amount_usd)
        total_amount_usd = str(total_amount_usd)

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": self.paypal_currency,
                        "value": total_amount_usd,
                        "breakdown": {
                            "item_total": {"currency_code": self.paypal_currency, "value": subtotal_usd}
                        }
                    },
                    "description": f"BhojanXpress Order #{order_data.get('order_id')} (Converted from INR)",
                    "custom_id": str(order_data.get('order_id')),
                    "items": items
                }
            ],
            "application_context": {
                "return_url": order_data.get('return_url'),
                "cancel_url": order_data.get('cancel_url'),
                "brand_name": "BhojanXpress",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW",
                "landing_page": "BILLING"
            }
        }

        # Add breakdown for additional charges
        if Decimal(delivery_charge_usd) > 0:
            payload["purchase_units"][0]["amount"]["breakdown"]["shipping"] = {"currency_code": self.paypal_currency, "value": delivery_charge_usd}
        if Decimal(gst_amount_usd) > 0:
            payload["purchase_units"][0]["amount"]["breakdown"]["tax_total"] = {"currency_code": self.paypal_currency, "value": gst_amount_usd}
        if Decimal(discount_amount_usd) > 0:
            payload["purchase_units"][0]["amount"]["breakdown"]["discount"] = {"currency_code": self.paypal_currency, "value": discount_amount_usd}

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            response_data = response.json()

            if response.status_code in [200, 201]:
                # Extract approval URL
                approval_url = next((link['href'] for link in response_data['links'] if link['rel'] == 'approve'), None)
                return {
                    "success": True,
                    "order_id": response_data['id'],
                    "approval_url": approval_url,
                    "converted_amount_usd": total_amount_usd,
                    "original_amount_inr": order_data.get('total_amount')
                }
            else:
                print(f"PayPal order creation error: {response.status_code} - {response_data}")
                # Check for currency not supported error
                if isinstance(response_data, dict) and response_data.get('details'):
                    for detail in response_data['details']:
                        if detail.get('issue') == 'CURRENCY_NOT_SUPPORTED':
                            return {"success": False, "error": "CURRENCY_NOT_SUPPORTED", "message": detail.get('description')}
                return {"success": False, "error": response_data}
        except requests.exceptions.RequestException as e:
            print(f"Request error creating PayPal order: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"Error creating PayPal order: {e}")
            return {"success": False, "error": str(e)}

    def capture_payment(self, paypal_order_id):
        """Capture an approved PayPal payment"""
        access_token = self.get_access_token()
        if not access_token:
            return {"success": False, "error": "Failed to get PayPal access token"}

        url = f"{self.api_base_url}/v2/checkout/orders/{paypal_order_id}/capture"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": f"capture-{paypal_order_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

        try:
            response = requests.post(url, headers=headers, timeout=30)
            response_data = response.json()

            if response.status_code in [200, 201]:
                if response_data.get('status') == 'COMPLETED':
                    capture_id = response_data['purchase_units'][0]['payments']['captures'][0]['id']
                    return {
                        "success": True,
                        "capture_id": capture_id,
                        "status": response_data['status'],
                        "details": response_data
                    }
                else:
                    return {"success": False, "error": f"Payment not completed. Status: {response_data.get('status')}"}
            else:
                print(f"PayPal capture error: {response.status_code} - {response_data}")
                return {"success": False, "error": response_data}
        except requests.exceptions.RequestException as e:
            print(f"Request error capturing PayPal payment: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"Error capturing PayPal payment: {e}")
            return {"success": False, "error": str(e)}

    def get_order_details(self, paypal_order_id):
        """Get details of a PayPal order"""
        access_token = self.get_access_token()
        if not access_token:
            return {"success": False, "error": "Failed to get PayPal access token"}

        url = f"{self.api_base_url}/v2/checkout/orders/{paypal_order_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response_data = response.json()

            if response.status_code == 200:
                return {
                    "success": True,
                    "details": response_data
                }
            else:
                print(f"PayPal order details error: {response.status_code} - {response_data}")
                return {"success": False, "error": response_data}
        except requests.exceptions.RequestException as e:
            print(f"Request error getting PayPal order details: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            print(f"Error getting PayPal order details: {e}")
            return {"success": False, "error": str(e)}
