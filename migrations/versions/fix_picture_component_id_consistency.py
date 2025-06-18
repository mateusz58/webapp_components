"""Fix picture component_id consistency

Revision ID: fix_picture_component_id
Revises: add_picture_naming_system
Create Date: 2025-06-16 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_picture_component_id_consistency'
down_revision = 'add_picture_naming_001'
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix picture table to ensure component_id is always populated.
    This ensures database consistency where every picture has a component_id,
    either directly (for component pictures) or derived from variant_id (for variant pictures).
    """
    
    # Step 1: Drop conflicting constraints that prevent both component_id and variant_id
    op.drop_constraint('picture_belongs_to_component_or_variant', 'picture', schema='component_app', type_='check')
    op.drop_constraint('picture_component_id_picture_order_key', 'picture', schema='component_app', type_='unique')
    
    # Step 2: Update all pictures to have component_id populated from variant relationship
    op.execute("""
        UPDATE component_app.picture 
        SET component_id = cv.component_id
        FROM component_app.component_variant cv
        WHERE picture.variant_id = cv.id 
        AND picture.component_id IS NULL;
    """)
    
    # Step 3: Make component_id NOT NULL since it should always be populated
    op.alter_column('picture', 'component_id',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    schema='component_app')
    
    # Step 4: Create trigger function to automatically populate component_id
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.ensure_picture_component_id()
        RETURNS TRIGGER AS $$
        BEGIN
            -- If variant_id is being set, automatically set component_id
            IF NEW.variant_id IS NOT NULL THEN
                SELECT component_id INTO NEW.component_id
                FROM component_app.component_variant
                WHERE id = NEW.variant_id;
                
                IF NEW.component_id IS NULL THEN
                    RAISE EXCEPTION 'Cannot find component for variant_id %', NEW.variant_id;
                END IF;
            END IF;
            
            -- Ensure component_id is never NULL
            IF NEW.component_id IS NULL THEN
                RAISE EXCEPTION 'component_id cannot be NULL for pictures';
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Step 5: Create trigger to automatically maintain component_id consistency
    op.execute("""
        DROP TRIGGER IF EXISTS ensure_picture_component_id_trigger ON component_app.picture;
        CREATE TRIGGER ensure_picture_component_id_trigger
            BEFORE INSERT OR UPDATE ON component_app.picture
            FOR EACH ROW
            EXECUTE FUNCTION component_app.ensure_picture_component_id();
    """)


def downgrade():
    """
    Revert picture table changes - restore old constraint system.
    WARNING: This will make component_id nullable again and may cause data inconsistency.
    """
    
    # Step 1: Drop the trigger and function
    op.execute("DROP TRIGGER IF EXISTS ensure_picture_component_id_trigger ON component_app.picture;")
    op.execute("DROP FUNCTION IF EXISTS component_app.ensure_picture_component_id();")
    
    # Step 2: Make component_id nullable again
    op.alter_column('picture', 'component_id',
                    existing_type=sa.INTEGER(),
                    nullable=True,
                    schema='component_app')
    
    # Step 3: Clear component_id for variant pictures (restore old behavior)
    op.execute("""
        UPDATE component_app.picture 
        SET component_id = NULL
        WHERE variant_id IS NOT NULL;
    """)
    
    # Step 4: Restore old constraints
    op.create_check_constraint(
        'picture_belongs_to_component_or_variant',
        'picture',
        '(component_id IS NOT NULL AND variant_id IS NULL) OR (component_id IS NULL AND variant_id IS NOT NULL)',
        schema='component_app'
    )
    
    op.create_unique_constraint(
        'picture_component_id_picture_order_key', 
        'picture', 
        ['component_id', 'picture_order'], 
        schema='component_app'
    )