"""Add automatic picture naming system

Revision ID: add_picture_naming_001
Revises: add_variant_sku_001
Create Date: 2024-06-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_picture_naming_001'
down_revision = 'add_variant_sku_001'
branch_labels = None
depends_on = None


def upgrade():
    """Add automatic picture naming with database functions and triggers"""
    
    # Create the picture name generation function
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.generate_picture_name(
            p_component_id INTEGER DEFAULT NULL,
            p_variant_id INTEGER DEFAULT NULL,
            p_picture_order INTEGER DEFAULT 1
        ) RETURNS VARCHAR(255) AS $function$
        DECLARE
            v_supplier_code VARCHAR(50);
            v_product_number VARCHAR(50);
            v_color_name VARCHAR(50);
            v_picture_name VARCHAR(255);
        BEGIN
            -- Determine if this is a component or variant picture
            IF p_variant_id IS NOT NULL THEN
                -- Variant picture: get component info through variant
                SELECT 
                    COALESCE(s.supplier_code, '') as supplier_code,
                    c.product_number,
                    co.name as color_name
                INTO v_supplier_code, v_product_number, v_color_name
                FROM component_app.component_variant cv
                JOIN component_app.component c ON cv.component_id = c.id
                JOIN component_app.color co ON cv.color_id = co.id
                LEFT JOIN component_app.supplier s ON c.supplier_id = s.id
                WHERE cv.id = p_variant_id;
            ELSIF p_component_id IS NOT NULL THEN
                -- Component picture: get component info directly
                SELECT 
                    COALESCE(s.supplier_code, '') as supplier_code,
                    c.product_number,
                    'main' as color_name  -- Use 'main' for component pictures
                INTO v_supplier_code, v_product_number, v_color_name
                FROM component_app.component c
                LEFT JOIN component_app.supplier s ON c.supplier_id = s.id
                WHERE c.id = p_component_id;
            ELSE
                RAISE EXCEPTION 'Either component_id or variant_id must be provided';
            END IF;
            
            -- Check if we found the data
            IF v_product_number IS NULL THEN
                RAISE EXCEPTION 'Component or variant not found';
            END IF;
            
            -- Normalize strings: lowercase and replace spaces with underscores
            v_product_number := LOWER(REPLACE(v_product_number, ' ', '_'));
            v_color_name := LOWER(REPLACE(v_color_name, ' ', '_'));
            
            -- Generate picture name based on whether supplier exists
            IF v_supplier_code IS NOT NULL AND v_supplier_code != '' THEN
                -- Pattern: <supplier_code>_<product_number>_<color_name>_<picture_order>
                v_picture_name := LOWER(v_supplier_code) || '_' || v_product_number || '_' || v_color_name || '_' || p_picture_order::text;
            ELSE
                -- Pattern: <product_number>_<color_name>_<picture_order>
                v_picture_name := v_product_number || '_' || v_color_name || '_' || p_picture_order::text;
            END IF;
            
            RETURN v_picture_name;
        END;
        $function$ LANGUAGE plpgsql;
    """)
    
    # Create trigger function for picture name updates
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_picture_name() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update the picture_name when insert or update occurs
            IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                NEW.picture_name := component_app.generate_picture_name(NEW.component_id, NEW.variant_id, NEW.picture_order);
                RETURN NEW;
            END IF;
            
            RETURN NULL;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for picture table
    op.execute("""
        CREATE TRIGGER trigger_update_picture_name
            BEFORE INSERT OR UPDATE ON component_app.picture
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_picture_name();
    """)
    
    # Create trigger function for component changes
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_picture_names_on_component_change() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update all picture names when component product_number or supplier changes
            IF TG_OP = 'UPDATE' THEN
                -- Check if product_number or supplier_id changed
                IF OLD.product_number != NEW.product_number OR 
                   COALESCE(OLD.supplier_id, -1) != COALESCE(NEW.supplier_id, -1) THEN
                    
                    -- Update component pictures for this component
                    UPDATE component_app.picture 
                    SET picture_name = component_app.generate_picture_name(component_id, variant_id, picture_order)
                    WHERE component_id = NEW.id;
                    
                    -- Update variant pictures for variants of this component
                    UPDATE component_app.picture p
                    SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                    FROM component_app.component_variant cv
                    WHERE p.variant_id = cv.id 
                    AND cv.component_id = NEW.id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for component changes
    op.execute("""
        CREATE TRIGGER trigger_update_picture_names_on_component_change
            AFTER UPDATE ON component_app.component
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_picture_names_on_component_change();
    """)
    
    # Create trigger function for supplier changes
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_picture_names_on_supplier_change() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update all picture names when supplier code changes
            IF TG_OP = 'UPDATE' THEN
                IF OLD.supplier_code != NEW.supplier_code THEN
                    -- Update component pictures for components using this supplier
                    UPDATE component_app.picture p
                    SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                    FROM component_app.component c
                    WHERE p.component_id = c.id 
                    AND c.supplier_id = NEW.id;
                    
                    -- Update variant pictures for components using this supplier
                    UPDATE component_app.picture p
                    SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                    FROM component_app.component_variant cv
                    JOIN component_app.component c ON cv.component_id = c.id
                    WHERE p.variant_id = cv.id 
                    AND c.supplier_id = NEW.id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for supplier changes
    op.execute("""
        CREATE TRIGGER trigger_update_picture_names_on_supplier_change
            AFTER UPDATE ON component_app.supplier
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_picture_names_on_supplier_change();
    """)
    
    # Create trigger function for color changes
    op.execute("""
        CREATE OR REPLACE FUNCTION component_app.update_picture_names_on_color_change() RETURNS TRIGGER AS $trigger$
        BEGIN
            -- Update all picture names when color name changes
            IF TG_OP = 'UPDATE' THEN
                IF OLD.name != NEW.name THEN
                    -- Update variant pictures using this color
                    UPDATE component_app.picture p
                    SET picture_name = component_app.generate_picture_name(p.component_id, p.variant_id, p.picture_order)
                    FROM component_app.component_variant cv
                    WHERE p.variant_id = cv.id 
                    AND cv.color_id = NEW.id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for color changes
    op.execute("""
        CREATE TRIGGER trigger_update_picture_names_on_color_change
            AFTER UPDATE ON component_app.color
            FOR EACH ROW
            EXECUTE FUNCTION component_app.update_picture_names_on_color_change();
    """)
    
    # Populate existing records with generated picture names
    op.execute("""
        UPDATE component_app.picture 
        SET picture_name = component_app.generate_picture_name(component_id, variant_id, picture_order);
    """)
    
    # Add unique constraint on picture_name
    op.create_unique_constraint('picture_name_unique', 'picture', ['picture_name'])
    
    # Add index for performance
    op.create_index('idx_picture_name', 'picture', ['picture_name'])


def downgrade():
    """Remove automatic picture naming system"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_update_picture_name ON component_app.picture;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_picture_names_on_component_change ON component_app.component;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_picture_names_on_supplier_change ON component_app.supplier;")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_picture_names_on_color_change ON component_app.color;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS component_app.update_picture_name();")
    op.execute("DROP FUNCTION IF EXISTS component_app.update_picture_names_on_component_change();")
    op.execute("DROP FUNCTION IF EXISTS component_app.update_picture_names_on_supplier_change();")
    op.execute("DROP FUNCTION IF EXISTS component_app.update_picture_names_on_color_change();")
    op.execute("DROP FUNCTION IF EXISTS component_app.generate_picture_name(INTEGER, INTEGER, INTEGER);")
    
    # Drop index and constraint
    op.drop_index('idx_picture_name', 'picture')
    op.drop_constraint('picture_name_unique', 'picture', type_='unique')