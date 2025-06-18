"""Convert component-category relationship to many-to-many

Revision ID: category_many_to_many
Revises: add_properties_table
Create Date: 2025-06-18 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'category_many_to_many'
down_revision = 'add_properties_table'
branch_labels = None
depends_on = None


def upgrade():
    """
    Convert the component-category relationship from one-to-many to many-to-many.
    This allows components to belong to multiple categories following the open/close principle.
    """
    
    # Step 1: Create the component_category association table
    op.create_table('component_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['component_app.category.id'], ),
        sa.ForeignKeyConstraint(['component_id'], ['component_app.component.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('component_id', 'category_id'),
        schema='component_app'
    )
    
    # Step 2: Migrate existing category data from component.category_id to the association table
    op.execute("""
        INSERT INTO component_app.component_category (component_id, category_id)
        SELECT id, category_id 
        FROM component_app.component 
        WHERE category_id IS NOT NULL;
    """)
    
    # Step 3: Remove the old category_id foreign key column from component table
    op.drop_constraint('component_category_id_fkey', 'component', schema='component_app', type_='foreignkey')
    op.drop_column('component', 'category_id', schema='component_app')
    
    # Step 4: Update indexes to remove category_id references
    op.drop_index('component_category_idx', table_name='component', schema='component_app')
    op.drop_index('idx_component_category', table_name='component', schema='component_app')
    
    # Step 5: Create indexes for the new association table
    op.create_index('component_category_component_idx', 'component_category', ['component_id'], schema='component_app')
    op.create_index('component_category_category_idx', 'component_category', ['category_id'], schema='component_app')


def downgrade():
    """
    Revert back to one-to-many relationship.
    WARNING: This will only preserve the first category for components that have multiple categories.
    """
    
    # Step 1: Add back the category_id column to component table
    op.add_column('component', sa.Column('category_id', sa.INTEGER(), nullable=True), schema='component_app')
    
    # Step 2: Migrate data back (taking only the first category for each component)
    op.execute("""
        UPDATE component_app.component 
        SET category_id = (
            SELECT category_id 
            FROM component_app.component_category cc 
            WHERE cc.component_id = component.id 
            ORDER BY cc.id 
            LIMIT 1
        );
    """)
    
    # Step 3: Make category_id NOT NULL again
    op.alter_column('component', 'category_id',
                   existing_type=sa.INTEGER(),
                   nullable=False,
                   schema='component_app')
    
    # Step 4: Add back the foreign key constraint
    op.create_foreign_key('component_category_id_fkey', 'component', 'category', 
                         ['category_id'], ['id'], source_schema='component_app', 
                         referent_schema='component_app')
    
    # Step 5: Recreate the old indexes
    op.create_index('component_category_idx', 'component', ['category_id'], schema='component_app')
    op.create_index('idx_component_category', 'component', ['category_id'], schema='component_app')
    
    # Step 6: Drop the association table and its indexes
    op.drop_index('component_category_category_idx', table_name='component_category', schema='component_app')
    op.drop_index('component_category_component_idx', table_name='component_category', schema='component_app')
    op.drop_table('component_category', schema='component_app')