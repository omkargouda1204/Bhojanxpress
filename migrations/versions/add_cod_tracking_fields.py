"""Add COD tracking fields to Order model

Revision ID: add_cod_tracking_fields
Revises: 
Create Date: 2025-01-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cod_tracking_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add COD tracking fields to orders table
    op.add_column('orders', sa.Column('payment_received', sa.Boolean(), nullable=True, default=False))
    op.add_column('orders', sa.Column('cod_received', sa.Boolean(), nullable=True, default=False))
    op.add_column('orders', sa.Column('cod_collected', sa.Boolean(), nullable=True, default=False))
    op.add_column('orders', sa.Column('cod_collection_time', sa.DateTime(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE orders SET payment_received = false WHERE payment_received IS NULL")
    op.execute("UPDATE orders SET cod_received = false WHERE cod_received IS NULL")
    op.execute("UPDATE orders SET cod_collected = false WHERE cod_collected IS NULL")


def downgrade():
    # Remove COD tracking fields
    op.drop_column('orders', 'cod_collection_time')
    op.drop_column('orders', 'cod_collected')
    op.drop_column('orders', 'cod_received')
    op.drop_column('orders', 'payment_received')