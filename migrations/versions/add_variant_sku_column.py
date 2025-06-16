"""Add variant_sku column to component_variant table

Revision ID: add_variant_sku_001
Revises: 5c7270d93828
Create Date: 2024-06-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_variant_sku_001'
down_revision = '5c7270d93828'
branch_labels = None
depends_on = None


def upgrade():
    """Add variant_sku column with automatic generation and triggers"""
    
    # Add the variant_sku column
    op.add_column('component_variant', sa.Column('variant_sku', sa.String(255), nullable=True))
    
    # Create the SKU generation function
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.generate_variant_sku(
            p_component_id INTEGER,
            p_color_id INTEGER
        ) RETURNS VARCHAR(255) AS $function$
        DECLARE
            v_supplier_code VARCHAR(50);
            v_product_number VARCHAR(50);
            v_color_name VARCHAR(50);
            v_sku VARCHAR(255);
        BEGIN
            -- Get component details with supplier code
            SELECT 
                COALESCE(s.supplier_code, '') as supplier_code,
                c.product_number
            INTO v_supplier_code, v_product_number
            FROM component_app.component c
            LEFT JOIN component_app.supplier s ON c.supplier_id = s.id
            WHERE c.id = p_component_id;
            
            -- Get color name
            SELECT name INTO v_color_name
            FROM component_app.color
            WHERE id = p_color_id;
            
            -- Normalize product number: lowercase and replace spaces with underscores
            v_product_number := LOWER(REPLACE(v_product_number, ' ', '_'));
            
            -- Normalize color name: lowercase and replace spaces with underscores
            v_color_name := LOWER(REPLACE(v_color_name, ' ', '_'));
            
            -- Generate SKU based on whether supplier exists
            IF v_supplier_code IS NOT NULL AND v_supplier_code != '' THEN
                -- Pattern: <supplier_code>_<product_number>_<color_name>
                v_sku := v_supplier_code || '_' || v_product_number || '_' || v_color_name;
            ELSE
                -- Pattern: <product_number>_<color_name>
                v_sku := v_product_number || '_' || v_color_name;
            END IF;
            
            RETURN v_sku;
        END;
        $function$ LANGUAGE plpgsql;
    """)
    
    # Create trigger function for variant SKU updates
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_variant_sku() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update the variant_sku when insert or update occurs
            IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                NEW.variant_sku := component_app.generate_variant_sku(NEW.component_id, NEW.color_id);
                NEW.updated_at := CURRENT_TIMESTAMP;
                RETURN NEW;
            END IF;
            
            RETURN NULL;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for variant table
    op.execute("""
        CREATE TRIGGER trigger_update_variant_sku
            BEFORE INSERT OR UPDATE ON component_app.component_variant
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_variant_sku();
    """)
    
    # Create trigger function for component changes
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_variant_skus_on_component_change() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update all variant SKUs when component product_number or supplier changes
            IF TG_OP = 'UPDATE' THEN
                -- Check if product_number or supplier_id changed
                IF OLD.product_number != NEW.product_number OR 
                   COALESCE(OLD.supplier_id, -1) != COALESCE(NEW.supplier_id, -1) THEN
                    
                    -- Update all variants for this component
                    UPDATE component_app.component_variant 
                    SET variant_sku = component_app.generate_variant_sku(component_id, color_id),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE component_id = NEW.id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for component changes
    op.execute("""
        CREATE TRIGGER trigger_update_variant_skus_on_component_change
            AFTER UPDATE ON component_app.component
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_variant_skus_on_component_change();
    """)
    
    # Create trigger function for supplier changes
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_variant_skus_on_supplier_change() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update all variant SKUs when supplier code changes
            IF TG_OP = 'UPDATE' THEN
                IF OLD.supplier_code != NEW.supplier_code THEN
                    -- Update all variants for components using this supplier
                    UPDATE component_app.component_variant cv
                    SET variant_sku = component_app.generate_variant_sku(cv.component_id, cv.color_id),
                        updated_at = CURRENT_TIMESTAMP
                    FROM component_app.component c
                    WHERE cv.component_id = c.id 
                    AND c.supplier_id = NEW.id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for supplier changes
    op.execute("""
        CREATE TRIGGER trigger_update_variant_skus_on_supplier_change
            AFTER UPDATE ON component_app.supplier
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_variant_skus_on_supplier_change();
    """)
    
    # Create trigger function for color changes
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_variant_skus_on_color_change() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update all variant SKUs when color name changes
            IF TG_OP = 'UPDATE' THEN
                IF OLD.name != NEW.name THEN
                    -- Update all variants using this color
                    UPDATE component_app.component_variant 
                    SET variant_sku = component_app.generate_variant_sku(component_id, color_id),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE color_id = NEW.id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for color changes
    op.execute("""
        CREATE TRIGGER trigger_update_variant_skus_on_color_change
            AFTER UPDATE ON component_app.color
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_variant_skus_on_color_change();
    """)
    
    # Populate existing records with generated SKUs
    op.execute("""
        UPDATE component_app.component_variant 
        SET variant_sku = component_app.generate_variant_sku(component_id, color_id),
            updated_at = CURRENT_TIMESTAMP;
    """)
    
    # Add unique constraint
    op.create_unique_constraint('component_variant_sku_unique', 'component_variant', ['variant_sku'])
    
    # Add index for performance
    op.create_index('idx_component_variant_sku', 'component_variant', ['variant_sku'])


def downgrade():
    """Remove variant_sku column and related functions/triggers"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_update_variant_sku ON component_app.component_variant;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_variant_skus_on_component_change ON component_app.component;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_variant_skus_on_supplier_change ON component_app.supplier;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_variant_skus_on_color_change ON component_app.color;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS component_app.update_variant_sku();")
    op.execute("DROP FUNCTION IF EXISTS component_app.update_variant_skus_on_component_change();")
    op.execute("DROP FUNCTION IF EXISTS component_app.update_variant_skus_on_supplier_change();")
    op.execute("DROP FUNCTION IF EXISTS component_app.update_variant_skus_on_color_change();")
    op.execute("DROP FUNCTION IF EXISTS component_app.generate_variant_sku(INTEGER, INTEGER);")
    
    # Drop index and constraint
    op.drop_index('idx_component_variant_sku', 'component_variant')
    op.drop_constraint('component_variant_sku_unique', 'component_variant', type_='unique')
    
    # Drop column
    op.drop_column('component_variant', 'variant_sku')