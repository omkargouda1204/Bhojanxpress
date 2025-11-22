"""add_display_name_to_category

Revision ID: add_display_name_to_category
Revises: 005_add_email_verification
Create Date: 2025-08-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_display_name_to_category'
down_revision = '005_add_email_verification'  # Fixed to reference existing migration
branch_labels = None
depends_on = None

def upgrade():
    # Add display_name column to category table if it doesn't exist
    op.execute("ALTER TABLE category ADD COLUMN IF NOT EXISTS display_name VARCHAR(50) NOT NULL DEFAULT ''")

def downgrade():
    # Drop display_name column from category table
    op.drop_column('category', 'display_name')
