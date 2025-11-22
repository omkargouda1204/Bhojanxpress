"""add banner and site images tables

Revision ID: 001_add_banner_and_site_images
Revises:
Create Date: 2025-08-06
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_add_banner_and_site_images'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create banners table
    op.create_table(
        'banners',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_path', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('subtitle', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create site_images table
    op.create_table(
        'site_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_path', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('site_images')
    op.drop_table('banners')
