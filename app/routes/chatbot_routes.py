from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import current_user
from app import csrf, db
from app.models import Order, FoodItem, Category, Coupon
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

            # Order Cancellation FAQs
            'can i cancel my order|cancel order|cancellation': [
                "📋 **Order Cancellation Policy:**\n\n✅ **Yes, you can cancel your order within 5 minutes of placing it.**\n\n⏰ **After 5 minutes:** Cancellation is not allowed, except in emergencies.\n\n💰 **Cancellation Charges:**\n• Customer cancellation: 5% of order amount deducted\n• BhojanXpress cancellation: 100% refund\n• Emergency/mistake: No charges\n\n📞 **Cancel via:** App/Website or call +91 84317 29319\n\n💳 **Refund:** 3-5 working days for online payments"
            ],

            'cancellation fee|cancel charge': [
                "💰 **Cancellation Charges:**\n\n• **Personal reasons:** 5% of order amount deducted\n• **Emergencies/Genuine mistakes:** No charges\n• **BhojanXpress cancellation:** 100% refund\n\nOnly applies if you cancel within 5 minutes of placing order!"
            ],

            'refund|when will i get refund|refund time': [
                "💳 **Refund Information:**\n\n⏰ **Processing Time:** 3-5 working days for online payments\n\n📧 **If refund delayed:** Contact us with:\n• Order reference number\n• Account holder name\n• Email: bhojanaxpress@gmail.com\n• Call/WhatsApp: +91 84317 29319\n\n✅ **Return orders:** Special cases (wrong/mistaken order) - 3-5 working days"
            ],

            # Delivery Information
            'delivery charge|delivery fee|shipping cost': [
                "🚚 **Delivery Charges:**\n\n💰 Orders below ₹200 → ₹30 delivery charge\n🆓 Orders ₹200 and above → Free delivery\n\n📍 We deliver in selected regions only. Check your pin code at checkout!"
            ],

            'delivery time|how long|when will food arrive': [
                "⏰ **Delivery Information:**\n\n🕐 **Average delivery time:** 30-45 minutes\n📱 **Real-time tracking:** Available in app\n⚠️ **Delayed orders:** You'll be notified + can request cancellation\n\n📞 Share your order number for exact ETA: +91 84317 29319"
            ],

            'track order|order status|where is my order': [
                "📍 **Order Tracking:**\n\n🔍 **To track your order, please provide your order ID**\n\n📱 **Real-time status:**\n• Order Placed → Confirmed → Preparing → Out for Delivery → Delivered\n\n📞 **Need help?** Call/WhatsApp +91 84317 29319"
            ],

            # Payment Information
            'payment|pay|payment methods|cod|cash on delivery': [
                "💳 **Payment Options:**\n\n✅ **Available methods:**\n• Cash on Delivery (COD)\n• UPI (Google Pay, Paytm, PhonePe)\n• Credit/Debit Cards\n• Net Banking\n• Digital Wallets\n\n🔒 **Safe & Secure** - We use encrypted payment gateways\n\n💰 **COD orders** can also be cancelled within 5 minutes"
            ],

            # Menu and Food Information
            'menu|food|items|what do you have|dishes|cuisine': [
                "🍴 **Browse Our Delicious Menu:**\n\n🏷️ **Categories Available:**\n• Appetizers & Starters\n• Main Courses & Curries\n• Biryani & Rice Items\n• Chinese & Continental\n• Desserts & Sweets\n• Beverages & Drinks\n• Special Combos\n\n🔍 **Search by:** Category, dish name, or restaurant\n📱 **Pro tip:** Use filters to find exactly what you're craving!"
            ],

            # Coupon and Offers
            'coupon|promo|discount|offer|deals': [
                "🎉 **Active Coupons & Offers:**\n\n💸 **Current Deals:**\n• First time users: Special discount\n• Weekend specials\n• Festival offers\n\n🏷️ **How to use:**\n1. Add items to cart\n2. Apply promo code at checkout\n3. Enjoy savings!\n\n📱 **Check app for latest active coupons!**"
            ],

            # Contact and Support
            'contact|support|help|phone number|email': [
                "📞 **Contact BhojanXpress Support:**\n\n🔥 **24/7 Support Available:**\n📱 **Call/WhatsApp:** +91 84317 29319\n📧 **Email:** bhojanaxpress@gmail.com\n\n🆘 **For urgent issues:** Call directly\n📝 **For detailed queries:** Email us\n\n⚡ **Fast response guaranteed!**"
            ],

            # General Ordering Questions
            'minimum order|min order|order limit': [
                "📦 **Order Information:**\n\n💰 **No minimum order value!**\n🚚 **But:** Orders below ₹200 have ₹30 delivery charge\n🆓 **Free delivery:** Orders ₹200+\n\n⏰ **Order scheduling:** Available (subject to restaurant timings)\n🏪 **Multiple restaurants:** One order per restaurant at a time"
            ],

            'schedule order|book for later|advance booking': [
                "⏰ **Schedule Your Order:**\n\n✅ **Yes! You can schedule orders for later**\n🕐 **How:** Select preferred delivery time at checkout\n📅 **Available:** Subject to restaurant timings\n\n📱 **Perfect for:** Parties, meetings, special occasions!"
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
            ]
        }

    def get_order_status(self, order_id):
        """Get real order status from database"""
        try:
            order = Order.query.filter_by(id=order_id).first()
            if order:
                status_messages = {
                    'pending': '⏳ Your order is pending confirmation',
                    'confirmed': '✅ Order confirmed! Kitchen is preparing your food',
                    'preparing': '👨‍🍳 Your delicious food is being prepared',
                    'ready': '🍽️ Order is ready for pickup',
                    'out_for_delivery': '🚚 Your order is out for delivery!',
                    'delivered': '✅ Order delivered! Hope you enjoyed it!',
                    'cancelled': '❌ Order was cancelled'
                }
                
                return f"📋 **Order #{order.id} Status:**\n\n{status_messages.get(order.status, 'Unknown status')}\n\n📅 **Placed:** {order.created_at.strftime('%d %b %Y at %I:%M %p')}\n💰 **Total:** ₹{order.total_amount}\n\n📞 **Need help?** Call +91 84317 29319"
            else:
                return f"❌ Order #{order_id} not found. Please check your order number and try again."
        except:
            return "⚠️ Unable to fetch order status right now. Please try again or contact support at +91 84317 29319"

    def get_food_info(self, food_name):
        """Get information about specific food items"""
        try:
            foods = FoodItem.query.filter(
                FoodItem.name.contains(food_name.lower()),
                FoodItem.is_available == True
            ).limit(5).all()
            
            if foods:
                result = f"🍽️ **Found {len(foods)} item(s) matching '{food_name}':**\n\n"
                for food in foods:
                    result += f"**{food.name}**\n"
                    result += f"💰 ₹{food.price}\n"
                    if food.description:
                        result += f"📝 {food.description[:100]}...\n"
                    result += f"⭐ Rating: {food.average_rating or 'New'}\n\n"
                return result
            else:
                return f"❌ No items found matching '{food_name}'. Try browsing our categories or contact us for recommendations!"
        except:
            return "⚠️ Unable to fetch food information right now. Please browse our menu or contact support."

    def get_categories(self):
        """Get available food categories"""
        try:
            categories = Category.query.filter_by(is_active=True).all()
            if categories:
                result = "🏷️ **Available Food Categories:**\n\n"
                for cat in categories:
                    result += f"• {cat.name}\n"
                result += "\n💡 **Browse by category to find your favorite dishes!**"
                return result
            else:
                return "🍽️ **Popular Categories:** Appetizers, Main Course, Biryani, Chinese, Desserts, Beverages"
        except:
            return "🏷️ **Popular Categories:** Appetizers, Main Course, Biryani, Chinese, Desserts, Beverages"

    def get_active_coupons(self):
        """Get currently active coupons"""
        try:
            active_coupons = Coupon.query.filter(
                Coupon.is_active == True,
                Coupon.expiry_date >= datetime.utcnow()
            ).limit(5).all()
            
            if active_coupons:
                result = "🎉 **Active Coupons & Offers:**\n\n"
                for coupon in active_coupons:
                    result += f"🏷️ **{coupon.code}**\n"
                    result += f"💸 {coupon.discount_percentage}% OFF "
                    if coupon.min_order_amount:
                        result += f"(Min order ₹{coupon.min_order_amount})"
                    result += f"\n📅 Valid till: {coupon.expiry_date.strftime('%d %b %Y')}\n\n"
                result += "💡 **Apply at checkout to save money!**"
                return result
            else:
                return "🎉 **No active coupons right now, but check back soon for exciting offers!**"
        except:
            return "🎉 **Check our app for latest coupons and offers!**"

    def get_response(self, user_input):
        user_input_lower = user_input.lower().strip()
        
        # Check if user is asking for order status with order ID
        order_id_match = re.search(r'(?:order\s*(?:id|number)?\s*[#:]?\s*)?(\d+)', user_input_lower)
        if any(keyword in user_input_lower for keyword in ['status', 'track', 'where', 'order']) and order_id_match:
            order_id = order_id_match.group(1)
            return self.get_order_status(order_id)
        
        # Check for food information requests
        food_match = re.search(r'(?:tell me about|info about|details of|what is)\s+(.+)', user_input_lower)
        if food_match and any(keyword in user_input_lower for keyword in ['food', 'dish', 'item']):
            food_name = food_match.group(1)
            return self.get_food_info(food_name)
        
        # Check for category requests
        if any(keyword in user_input_lower for keyword in ['categories', 'browse', 'types of food']):
            return self.get_categories()
        
        # Check for coupon requests
        if any(keyword in user_input_lower for keyword in ['coupon', 'offer', 'discount', 'promo']):
            return self.get_active_coupons()
        
        # Pattern matching for predefined responses
        for pattern, responses in self.responses.items():
            if re.search(pattern, user_input_lower):
                return random.choice(responses)
        
        # Enhanced default response with quick help
        return "🤔 I'm not sure about that! Here's what I can help you with:\n\n" \
               "📋 **Order Status:** Share your order number\n" \
               "🍽️ **Menu Info:** Ask about specific dishes\n" \
               "🏷️ **Categories:** Browse food types\n" \
               "🎉 **Coupons:** Get active offers\n" \
               "📞 **Support:** Call +91 84317 29319\n\n" \
               "Just ask me anything! 😊"

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