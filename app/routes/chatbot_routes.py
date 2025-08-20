from flask import Blueprint, request, jsonify, render_template
from app import csrf
from datetime import datetime
import re
import random

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

# In-memory storage for chat sessions
chat_sessions = {}

class BhojanXpressChatbot:
    def __init__(self):
        self.responses = {
            # Greetings - Enhanced with more variety
            'hello|hi|hey|good morning|good afternoon|good evening|namaste|hey there': [
                "🍽️ Hello! Welcome to BhojanXpress! I'm your food assistant. How can I make your day delicious? 😊",
                "👋 Hi there! Ready to explore some amazing food? I'm here to help you with anything!",
                "🌟 Welcome to BhojanXpress! Your favorite food is just a click away. What can I help you with?",
                "😊 Hey! Great to see you here. Let's find you something tasty today!"
            ],

            # Menu related - More detailed and appetizing
            'menu|food|items|what do you have|what food|dishes|cuisine|restaurant': [
                "🍴 Our Amazing Menu Includes:\n\n🥗 **Appetizers** - Crispy samosas, fresh salads, spring rolls\n🍛 **Main Courses** - Aromatic biryanis, rich curries, sizzling Chinese\n🍰 **Desserts** - Creamy ice creams, traditional sweets, fresh fruits\n🥤 **Beverages** - Fresh juices, soft drinks, hot beverages\n🍕 **Special Items** - Pizzas, burgers, sandwiches\n\n✨ All made with fresh ingredients and lots of love! Browse our full menu to see mouth-watering photos! 📱"
            ],

            # Order Status Queries - Enhanced with exact requested responses
            'can you tell me the status of my order|status of my order': [
                "Sure! Please provide your order number so I can check the status for you. You can find your order number in the confirmation email or SMS we sent you."
            ],

            'when will my food arrive': [
                "Our average delivery time is 30–45 minutes. Please share your order number for exact tracking. I'll be able to give you a precise ETA once I have your order details."
            ],

            'has my order been picked up by the delivery partner': [
                "Let me check! Please share your order number to confirm pickup status. This will allow me to see exactly where your order is in our delivery process."
            ],

            'track my order|track order number': [
                "Tracking your order: Please provide your order number (e.g. #12345), and I'll check its current status and estimated delivery time for you."
            ],

            'where is my delivery person': [
                "Your delivery partner's live location is available in the app's tracking section. Please share your order number, and I'll check their current location and ETA for you."
            ],

            # Payment & Refund Issues - Using exact requested responses
            'payment failed but money was deducted': [
                "Sorry about that! Usually, refunds are processed automatically within 3–5 business days. If it's delayed, please share your transaction ID so we can check and expedite the process."
            ],

            'change payment method': [
                "If your order hasn't been placed yet, you can change the payment method on the checkout page. If the order is confirmed, payment method cannot be changed. Would you like me to help with anything else?"
            ],

            'how do i use my coupon code': [
                "Enter your coupon code at checkout in the 'Apply Coupon' box before payment. Discounts will be applied instantly. Make sure the coupon is valid for your order value and the items you've selected."
            ],

            'refund not received yet': [
                "Refunds are typically credited within 3–5 business days. If it's been longer, please share your order number and payment receipt so we can escalate this with our finance team."
            ],

            'charged twice for the same order': [
                "We're sorry for the inconvenience. Please share both payment receipts and your order details, and we'll initiate a refund for the duplicate transaction within 24 hours."
            ],

            # Food Quality Complaints - Using exact requested responses
            'food is cold|food I received is cold': [
                "We apologize for the experience. Please share your order number so we can investigate and arrange a replacement or refund. We take food quality very seriously and will address this immediately."
            ],

            'missing items|order is missing items': [
                "Sorry about that! Please share details of the missing items and your order number, and we'll arrange for a refund or replacement. Our team will contact you within the next 30 minutes."
            ],

            'food was stale|food was spoiled': [
                "That's not the standard we aim for. Please share photos of the food and your order details so we can resolve this immediately. Your health and satisfaction are our top priorities."
            ],

            'wrong order|got the wrong order': [
                "We're sorry for the mix-up! Please share your order number and details, and we'll arrange a replacement right away. You can keep the wrong order at no charge while we deliver the correct one."
            ],

            'packaging damaged|packaging was damaged': [
                "We regret this happened. Please share a photo of the packaging and your order details so we can resolve the issue. We'll ensure proper compensation for any affected food items."
            ],

            # App & Technical Problems - Using exact requested responses
            'app not loading|app is not loading my past orders': [
                "Try logging out and logging back in. If the issue persists, please share your device details and app version so our technical team can help resolve this promptly."
            ],

            'cant add items|can\'t add items to my cart': [
                "This may be due to the restaurant being closed or the item being unavailable. Please try again later or choose another dish. You can also try clearing your app cache or reinstalling the app."
            ],

            'payment page is stuck': [
                "Try refreshing the page or switching to a different browser. If still stuck, clear your cache and retry. If the problem persists, try using a different payment method or contact our support team."
            ],

            'coupon not applying|coupon is not applying': [
                "Make sure the coupon is valid for your order value and items. Some coupons have minimum order amounts or category restrictions. Double-check the coupon code and ensure it hasn't expired."
            ],

            'address not saving|delivery address is not saving': [
                "Ensure you've granted location access to the app. If the problem persists, try re-entering the address manually. Make sure you've provided all required fields including PIN code and landmark."
            ],

            # General Help - Using exact requested responses
            'how do I place an order|how to place an order': [
                "Browse the menu, add items to your cart, proceed to checkout, and complete payment. Your food will be on its way! Is there a specific part of the process you need help with?"
            ],

            'can i schedule a delivery for later': [
                "Yes, you can choose a preferred delivery time at checkout. Simply select the 'Schedule for Later' option and pick your desired time slot. We offer time slots throughout the day."
            ],

            'what are your delivery charges': [
                "Orders below ₹200 have a ₹30 delivery charge. Orders of ₹200 or above have free delivery. During peak hours or adverse weather, there might be a small additional surge charge."
            ],

            'do you deliver to my area': [
                "Please share your PIN code, and I'll check if we deliver there. We're constantly expanding our delivery areas to serve more customers."
            ],

            'how can i contact my delivery partner': [
                "Once your order is picked up, you'll see a 'Call Delivery Partner' button in your order tracking screen. This appears after the restaurant has handed over your order to the delivery person."
            ],

            # Enhanced cancellation policy with specific fee information
            'cancel|cancellation|cancel order|stop order|dont want|change mind': [
                "🚨 **Order Cancellation Policy:**\n\n✅ **FREE Cancellation (Within 10 minutes):**\n• No charges applied\n• Full refund guaranteed\n• Processed instantly\n\n⚠️ **After 10 minutes:**\n• 15% cancellation fee of the food amount\n• Remaining amount refunded to original payment method\n• Refund processing time: 3-5 business days\n\n📞 **Need to Cancel?**\nContact us immediately at: bhojanaxpress@gmail.com\n\n💡 **Note:** Once the food preparation begins, cancellation may not be possible. Thanks for understanding!"
            ],

            # Thank you greetings
            'thank you|thanks|thx|thank u|thanx': [
                "You're welcome! 😊 It was a pleasure helping you today. Enjoy your delicious meal from BhojanXpress!",
                "Anytime! 🌟 Thank you for choosing BhojanXpress. Don't hesitate to reach out if you need anything else!",
                "My pleasure! 🙏 We appreciate your business. Have a wonderful dining experience with BhojanXpress!",
                "Glad I could help! 🍽️ Thank you for being a valued BhojanXpress customer. Enjoy your meal!"
            ],

            # Goodbye greetings
            'bye|goodbye|see you|talk later|ttyl': [
                "Goodbye! 👋 Thank you for chatting with BhojanXpress support. Have a wonderful day!",
                "See you soon! 😊 Don't forget to check out our daily specials. Bye for now!",
                "Take care! 🌟 Thank you for connecting with BhojanXpress. We're here 24/7 whenever you need us!",
                "Bye! 🙏 It was great helping you today. Enjoy your BhojanXpress experience!"
            ],

            # Default response for unmatched queries
            'default': [
                "🤔 I didn't quite understand that. But I'm here to help!\n\n🍽️ **I can help you with:**\n• 📋 Menu information & ordering\n• 📦 Order tracking & status\n• 💳 Payment & refund issues\n• 🚚 Delivery information\n• 🔧 Technical support\n• 📞 Contact information\n\n💬 **Try asking:**\n• 'Show me the menu'\n• 'Track my order'\n• 'What are delivery charges?'\n• 'How to place an order?'\n\n😊 **What would you like to know?**"
            ]
        }

    def get_response(self, user_message):
        user_message = user_message.lower().strip()

        # Check each pattern in responses
        for pattern, responses in self.responses.items():
            if pattern != 'default' and re.search(pattern, user_message):
                return random.choice(responses)

        # Return default response if no pattern matches
        return random.choice(self.responses['default'])

    def end_conversation(self, session_id):
        """Add a thank you message at the end of a conversation"""
        thank_you_messages = [
            "Thank you for chatting with BhojanXpress support! 🙏 We hope we were able to assist you today. If you have any more questions, feel free to ask anytime. Enjoy your meal! 🍽️",
            "We appreciate you reaching out to BhojanXpress! 😊 Is there anything else we can help you with? Have a delicious day ahead! ✨",
            "Thanks for using BhojanXpress chat support! Your satisfaction is our priority. Hope to serve you again soon with our delicious food! 🌟"
        ]
        return random.choice(thank_you_messages)

# Initialize chatbot
chatbot = BhojanXpressChatbot()

@chatbot_bp.route('/')
def chatbot_interface():
    """Render the chatbot interface"""
    return render_template('chatbot/chat.html')

@chatbot_bp.route('/chat', methods=['POST'])
@csrf.exempt
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        end_chat = data.get('end_chat', False)

        if not user_message and not end_chat:
            return jsonify({'error': 'Message is required'}), 400

        # Get response from chatbot
        if end_chat:
            bot_response = chatbot.end_conversation(session_id)
        else:
            bot_response = chatbot.get_response(user_message)

        # Store conversation in session (optional)
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        chat_sessions[session_id].append({
            'user': user_message if not end_chat else "End of conversation",
            'bot': bot_response,
            'timestamp': datetime.now().isoformat()
        })

        # Limit session history to last 50 messages to prevent memory issues
        if len(chat_sessions[session_id]) > 50:
            chat_sessions[session_id] = chat_sessions[session_id][-50:]

        return jsonify({
            'response': bot_response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': 'An error occurred processing your message'}), 500

@chatbot_bp.route('/history/<session_id>')
def get_chat_history(session_id):
    """Get chat history for a session"""
    history = chat_sessions.get(session_id, [])
    return jsonify({'history': history})

@chatbot_bp.route('/clear/<session_id>', methods=['POST'])
@csrf.exempt
def clear_chat_history(session_id):
    """Clear chat history for a session"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return jsonify({'message': 'Chat history cleared'})
