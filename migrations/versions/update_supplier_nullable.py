"""Update supplier_id to be nullable

Revision ID: update_supplier_nullable
Revises: 5c7270d93828
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_supplier_nullable'
down_revision = '5c7270d93828'
branch_labels = None
depends_on = None


def upgrade():
    """Make supplier_id nullable in component table"""
    # Drop the existing unique constraint first
    op.drop_constraint('_product_supplier_uc', 'component', schema='component_app')
    
    # Update the column to allow NULL values
    op.alter_column('component', 'supplier_id',
                    existing_type=sa.Integer(),
                    nullable=True,
                    schema='component_app')
    
    # Recreate the unique constraint (PostgreSQL handles NULL values in unique constraints)
    op.create_unique_constraint('_product_supplier_uc', 'component', 
                               ['product_number', 'supplier_id'], 
                               schema='component_app')


def downgrade():
    """Make supplier_id non-nullable again"""
    # Drop the unique constraint
    op.drop_constraint('_product_supplier_uc', 'component', schema='component_app')
    
    # First, ensure no NULL values exist
    op.execute("UPDATE component_app.component SET supplier_id = 1 WHERE supplier_id IS NULL")
    
    # Then make it non-nullable again
    op.alter_column('component', 'supplier_id',
                    existing_type=sa.Integer(),
                    nullable=False,
                    schema='component_app')
    
    # Recreate the unique constraint
    op.create_unique_constraint('_product_supplier_uc', 'component', 
                               ['product_number', 'supplier_id'], 
                               schema='component_app') 