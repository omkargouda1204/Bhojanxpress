"""Add notification fields to Order and Review

Revision ID: add_notification_tracking_fields
Revises: 006_enhanced_features
Create Date: 2025-09-21 15:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_notification_tracking_fields'
down_revision = '006_enhanced_features'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_viewed_by_admin column to order table
    op.add_column('order', sa.Column('is_viewed_by_admin', sa.Boolean(), nullable=False, server_default='0'))
    
    # Add is_viewed_by_admin column to review table
    op.add_column('review', sa.Column('is_viewed_by_admin', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # Remove is_viewed_by_admin column from order table
    op.drop_column('order', 'is_viewed_by_admin')
    
    # Remove is_viewed_by_admin column from review table
    op.drop_column('review', 'is_viewed_by_admin')