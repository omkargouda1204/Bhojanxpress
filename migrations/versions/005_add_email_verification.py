"""add_email_verification_fields

Revision ID: 005_add_email_verification
Revises: 003_add_order_date_to_order
Create Date: 2025-08-21 21:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_email_verification'
down_revision = '003_add_order_date_to_order'  # Fixed to reference existing migration
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('user', sa.Column('verification_otp', sa.String(length=6), nullable=True))
    op.add_column('user', sa.Column('otp_expiry', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('password_reset_otp', sa.String(length=6), nullable=True))
    op.add_column('user', sa.Column('password_reset_otp_expiry', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('user', 'password_reset_otp_expiry')
    op.drop_column('user', 'password_reset_otp')
    op.drop_column('user', 'otp_expiry')
    op.drop_column('user', 'verification_otp')
    op.drop_column('user', 'is_verified')
