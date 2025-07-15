# Database Triggers Backup

This file contains backup definitions of database triggers that were removed during development.

## Picture Naming Triggers (Removed)

### generate_picture_name Function
```sql
CREATE OR REPLACE FUNCTION component_app.generate_picture_name(p_component_id integer DEFAULT NULL::integer, p_variant_id integer DEFAULT NULL::integer, p_picture_order integer DEFAULT 1) 
RETURNS character varying
LANGUAGE plpgsql
AS $$
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
$$;
```

### update_picture_name Trigger Function
```sql
CREATE OR REPLACE FUNCTION component_app.update_picture_name() 
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update the picture_name when insert or update occurs
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        NEW.picture_name := component_app.generate_picture_name(NEW.component_id, NEW.variant_id, NEW.picture_order);
        RETURN NEW;
    END IF;
    
    RETURN NULL;
END;
$$;
```

### Picture Naming Triggers
```sql
-- Trigger on picture table
CREATE TRIGGER trigger_update_picture_name
    BEFORE INSERT OR UPDATE
    ON component_app.picture
    FOR EACH ROW
    EXECUTE PROCEDURE component_app.update_picture_name();

-- Trigger on component table changes
CREATE TRIGGER trigger_update_picture_names_on_component_change
    AFTER UPDATE
    ON component_app.component
    FOR EACH ROW
    EXECUTE PROCEDURE component_app.update_picture_names_on_component_change();

-- Trigger on supplier table changes
CREATE TRIGGER trigger_update_picture_names_on_supplier_change
    AFTER UPDATE
    ON component_app.supplier
    FOR EACH ROW
    EXECUTE PROCEDURE component_app.update_picture_names_on_supplier_change();

-- Trigger on color table changes
CREATE TRIGGER trigger_update_picture_names_on_color_change
    AFTER UPDATE
    ON component_app.color
    FOR EACH ROW
    EXECUTE PROCEDURE component_app.update_picture_names_on_color_change();
```

## Reason for Removal

The picture naming triggers were removed because:

1. **Naming Pattern Inconsistency**: The trigger used `'main'` for component pictures (e.g., `supplier_product_main_1`) but our WebDAV files and tests expected `supplier_product_1` pattern.

2. **Test Complexity**: The automatic naming made tests hard to predict and debug, especially when testing picture renaming scenarios.

3. **Manual Control Needed**: For comprehensive testing of picture renaming during component updates, manual control over picture names provides better test reliability.

## Alternative Approach

Instead of database triggers, picture names are now managed by:

1. **Application Logic**: ComponentService handles picture naming consistently
2. **Manual Test Setup**: Tests can set predictable picture names for verification
3. **Consistent Patterns**: Single naming pattern without "_main_" suffix

## Pattern Used After Removal

**Component Pictures (variant_id = NULL):**
- With supplier: `{supplier_code}_{product_number}_{order}`
- Without supplier: `{product_number}_{order}`

**Variant Pictures (variant_id = NOT NULL):**
- With supplier: `{supplier_code}_{product_number}_{color_name}_{order}`
- Without supplier: `{product_number}_{color_name}_{order}`

All strings are normalized: lowercase, dashes replaced with underscores.