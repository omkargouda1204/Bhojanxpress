"""Add Category model and update FoodItem

Revision ID: 002_add_category_and_update_fooditem
Revises: 001_add_banner_and_site_images
Create Date: 2025-08-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_category_and_update_fooditem'
down_revision = '001_add_banner_and_site_images'
branch_labels = None
depends_on = None

def upgrade():
    # Create category table
    op.create_table(
        'category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100)),
        sa.Column('description', sa.Text()),
        sa.Column('image_url', sa.String(length=255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Add category_id column to food_item table
    with op.batch_alter_table('food_item') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        # Copy data from old category column to new category_id (will need to be handled manually)
        batch_op.create_foreign_key('fk_food_item_category', 'category', ['category_id'], ['id'])
        # Drop old category column
        batch_op.drop_column('category')

def downgrade():
    # Remove foreign key and category_id from food_item
    with op.batch_alter_table('food_item') as batch_op:
        batch_op.drop_constraint('fk_food_item_category', type_='foreignkey')
        batch_op.add_column(sa.Column('category', sa.String(length=50)))
        batch_op.drop_column('category_id')

    # Drop category table
    op.drop_table('category')
