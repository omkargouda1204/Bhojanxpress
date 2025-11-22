"""Add enhanced features: reviews, delivery boys, nutritional info

Revision ID: 006_enhanced_features
Revises: add_display_name_to_category
Create Date: 2025-09-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '006_enhanced_features'
down_revision = 'add_display_name_to_category'  # Fixed to reference the correct parent
branch_labels = None
depends_on = None

def upgrade():
    # Add delivery boy flag to users table
    op.add_column('user', sa.Column('is_delivery_boy', sa.Boolean(), nullable=True, default=False))

    # Add delivery boy assignment to orders table
    op.add_column('order', sa.Column('delivery_boy_id', sa.Integer(), nullable=True))
    op.add_column('order', sa.Column('delivery_started_at', sa.DateTime(), nullable=True))

    # Add missing order fields
    op.add_column('order', sa.Column('payment_received', sa.Boolean(), nullable=True, default=False))
    op.add_column('order', sa.Column('order_date', sa.DateTime(), nullable=True))

    # Add commission tracking fields
    op.add_column('order', sa.Column('commission_amount', sa.Float(), nullable=True, default=0.0))
    op.add_column('order', sa.Column('commission_rate', sa.Float(), nullable=True, default=12.0))
    op.add_column('order', sa.Column('commission_paid', sa.Boolean(), nullable=True, default=False))
    op.add_column('order', sa.Column('commission_paid_at', sa.DateTime(), nullable=True))

    # Add COD (Cash on Delivery) tracking fields
    op.add_column('order', sa.Column('cod_received', sa.Boolean(), nullable=True, default=False))
    op.add_column('order', sa.Column('cod_amount', sa.Float(), nullable=True, default=0.0))
    op.add_column('order', sa.Column('cod_collected', sa.Boolean(), nullable=True, default=False))
    op.add_column('order', sa.Column('cod_collection_time', sa.DateTime(), nullable=True))

    # Add order status tracking fields
    op.add_column('order', sa.Column('cancel_reason', sa.Text(), nullable=True))
    op.add_column('order', sa.Column('return_reason', sa.Text(), nullable=True))

    # Create foreign key for delivery boy
    op.create_foreign_key('fk_order_delivery_boy', 'order', 'user', ['delivery_boy_id'], ['id'])

    # Create nutritional_info table
    op.create_table('nutritional_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('food_item_id', sa.Integer(), nullable=False),
        sa.Column('calories_per_serving', sa.Float(), nullable=True),
        sa.Column('protein_g', sa.Float(), nullable=True),
        sa.Column('carbohydrates_g', sa.Float(), nullable=True),
        sa.Column('fat_g', sa.Float(), nullable=True),
        sa.Column('fiber_g', sa.Float(), nullable=True),
        sa.Column('sugar_g', sa.Float(), nullable=True),
        sa.Column('sodium_mg', sa.Float(), nullable=True),
        sa.Column('cholesterol_mg', sa.Float(), nullable=True),
        sa.Column('serving_size', sa.String(length=50), nullable=True),
        sa.Column('allergens', sa.Text(), nullable=True),
        sa.Column('ingredients', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['food_item_id'], ['food_item.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('food_item_id')
    )

    # Create review table
    op.create_table('review',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('food_item_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['food_item_id'], ['food_item.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create review_image table
    op.create_table('review_image',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_id', sa.Integer(), nullable=False),
        sa.Column('image_data', sa.LargeBinary(), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('image_filename', sa.String(length=255), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['review_id'], ['review.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Update existing data
    op.execute("UPDATE user SET is_delivery_boy = FALSE WHERE is_delivery_boy IS NULL")
    op.alter_column('user', 'is_delivery_boy', nullable=False, default=False)

    # Update existing orders with default values for new fields
    op.execute("UPDATE `order` SET payment_received = FALSE WHERE payment_received IS NULL")
    op.execute("UPDATE `order` SET order_date = created_at WHERE order_date IS NULL")
    op.execute("UPDATE `order` SET commission_amount = 0.0 WHERE commission_amount IS NULL")
    op.execute("UPDATE `order` SET commission_rate = 12.0 WHERE commission_rate IS NULL")
    op.execute("UPDATE `order` SET commission_paid = FALSE WHERE commission_paid IS NULL")
    op.execute("UPDATE `order` SET cod_received = FALSE WHERE cod_received IS NULL")
    op.execute("UPDATE `order` SET cod_amount = 0.0 WHERE cod_amount IS NULL")
    op.execute("UPDATE `order` SET cod_collected = FALSE WHERE cod_collected IS NULL")

def downgrade():
    # Remove tables in reverse order
    op.drop_table('review_image')
    op.drop_table('review')
    op.drop_table('nutritional_info')

    # Remove foreign key and columns from order table
    op.drop_constraint('fk_order_delivery_boy', 'order', type_='foreignkey')

    # Remove COD and commission fields
    op.drop_column('order', 'return_reason')
    op.drop_column('order', 'cancel_reason')
    op.drop_column('order', 'cod_collection_time')
    op.drop_column('order', 'cod_collected')
    op.drop_column('order', 'cod_amount')
    op.drop_column('order', 'cod_received')
    op.drop_column('order', 'commission_paid_at')
    op.drop_column('order', 'commission_paid')
    op.drop_column('order', 'commission_rate')
    op.drop_column('order', 'commission_amount')
    op.drop_column('order', 'order_date')
    op.drop_column('order', 'payment_received')
    op.drop_column('order', 'delivery_started_at')
    op.drop_column('order', 'delivery_boy_id')

    # Remove delivery boy flag from users
    op.drop_column('user', 'is_delivery_boy')
