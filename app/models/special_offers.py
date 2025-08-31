from app import db
from datetime import datetime

class SpecialOffer(db.Model):
    __tablename__ = 'special_offers'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed, or coupon
    discount_value = db.Column(db.Float, nullable=False)
    min_order_value = db.Column(db.Float, default=0)
    max_discount_value = db.Column(db.Float)
    coupon_code = db.Column(db.String(20))
    image_path = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    applies_to_category = db.Column(db.String(50))  # specific category or None for all
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<SpecialOffer {self.title}>'
    
    @property
    def is_valid(self):
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True
