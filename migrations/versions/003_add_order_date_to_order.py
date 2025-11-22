"""Add order_date to Order model

Revision ID: 003_add_order_date_to_order
Revises: 002_add_category_and_update_fooditem
Create Date: 2025-08-08
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003_add_order_date_to_order'
down_revision = '002_add_category_and_update_fooditem'
branch_labels = None
depends_on = None

def upgrade():
    # Add order_date column to order table
    with op.batch_alter_table('order') as batch_op:
        batch_op.add_column(sa.Column('order_date', sa.DateTime(), nullable=True, server_default=sa.func.current_timestamp()))
    
    # Update existing rows to set order_date equal to created_at
    op.execute("UPDATE `order` SET order_date = created_at WHERE order_date IS NULL")

def downgrade():
    with op.batch_alter_table('order') as batch_op:
        batch_op.drop_column('order_date')
