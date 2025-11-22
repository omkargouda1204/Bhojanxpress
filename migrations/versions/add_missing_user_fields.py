"""Add delivery agent fields and update user model

Revision ID: add_missing_user_fields
Revises: add_notification_tracking_fields
Create Date: 2025-09-21 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_missing_user_fields'
down_revision = 'add_notification_tracking_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add verification fields if they don't exist
    try:
        op.add_column('user', sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='0'))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('verification_otp', sa.String(length=6), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('otp_expiry', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('password_reset_otp', sa.String(length=6), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('password_reset_otp_expiry', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist
    
    # Add delivery agent account fields
    try:
        op.add_column('user', sa.Column('bank_name', sa.String(length=100), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('account_number', sa.String(length=20), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('ifsc_code', sa.String(length=15), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('account_holder_name', sa.String(length=100), nullable=True))
    except Exception:
        pass  # Column might already exist
        
    try:
        op.add_column('user', sa.Column('upi_id', sa.String(length=50), nullable=True))
    except Exception:
        pass  # Column might already exist

    # Add is_active column if it doesn't exist
    try:
        op.add_column('user', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'))
    except Exception:
        pass  # Column might already exist


def downgrade():
    # We don't want to drop these columns in a downgrade since they contain important data
    pass