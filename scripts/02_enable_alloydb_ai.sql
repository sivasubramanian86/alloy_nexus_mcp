-- =============================================================================
-- QuerySage: AlloyDB AI Natural Language Configuration
-- Run this AFTER AlloyDB AI is enabled in the GCP console for your cluster
-- Reference: https://cloud.google.com/alloydb/docs/ai/configure-natural-language
-- =============================================================================

-- Step 1: Verify AlloyDB AI extension is active
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('google_ml_integration', 'vector', 'alloydb_ai_nl');

-- =============================================================================
-- Step 2: Register the Vertex AI text-to-SQL model
-- AlloyDB AI uses gemini-1.5-pro or gemini-2.0-flash for NL→SQL
-- =============================================================================
-- CALL google_ml.create_model(
--     'gemini-nl-querysage',
--     'publishers/google/models/gemini-2.0-flash-001',
--     json_build_object('model_type', 'text_generation')
-- );

-- =============================================================================
-- Step 3: Create AlloyDB AI Natural Language Configuration
-- This tells AlloyDB AI which tables are in scope and adds schema context
-- =============================================================================
-- SELECT alloydb_ai_nl.create_configuration(
--     'querysage_pharma_config',
--     json_build_object(
--         'tables', ARRAY[
--             'drug_inventory',
--             'suppliers',
--             'wards',
--             'procurement_orders',
--             'inventory_transactions'
--         ],
--         'description', 'Hospital pharmaceutical inventory management system. Track drug stock levels, suppliers, procurement orders, and dispensing transactions across hospital wards.',
--         'column_descriptions', json_build_object(
--             'drug_inventory.current_stock',    'Current quantity in stock at the hospital pharmacy',
--             'drug_inventory.reorder_level',    'Minimum stock threshold that triggers a new procurement order',
--             'drug_inventory.is_controlled',    'TRUE if this is a Schedule H/H1 controlled/narcotic substance',
--             'drug_inventory.drug_category',    'Therapeutic category: Antibiotic, Analgesic, Cardiac, Anticoagulant, Anaesthetic, Endocrine, IV Fluid, Hormone',
--             'procurement_orders.status',       'Order lifecycle: PENDING, DELIVERED, PARTIAL, CANCELLED',
--             'inventory_transactions.txn_type', 'Transaction type: DISPENSE (given to patient), RESTOCK (received from store), WASTE (expired/damaged), RETURN'
--         )
--     )
-- );

-- =============================================================================
-- Step 4: Validate the configuration with a test NL query
-- =============================================================================
-- SELECT alloydb_ai_nl.translate(
--     'querysage_pharma_config',
--     'Which drugs are below their reorder level?'
-- );

-- =============================================================================
-- SAMPLE NL→SQL Translations (for demo purposes — run via Python API)
-- These are the 5 required natural language queries for the submission
-- =============================================================================

-- Query 1: Drugs below reorder level (procurement alerts)
-- NL: "Which drugs are below their reorder level and need urgent reordering?"
SELECT
    d.drug_name,
    d.generic_name,
    d.drug_category,
    d.current_stock,
    d.reorder_level,
    (d.reorder_level - d.current_stock) AS shortage_quantity,
    s.supplier_name,
    s.lead_time_days
FROM drug_inventory d
JOIN suppliers s ON d.supplier_id = s.supplier_id
WHERE d.current_stock < d.reorder_level
ORDER BY (d.reorder_level - d.current_stock) DESC;

-- Query 2: Controlled substances inventory (compliance check)
-- NL: "Show me all controlled substances with their current stock and expiry dates"
SELECT
    d.drug_name,
    d.generic_name,
    d.current_stock,
    d.unit_of_measure,
    d.expiry_date,
    d.storage_temp,
    w.ward_name
FROM drug_inventory d
LEFT JOIN wards w ON d.ward_id = w.ward_id
WHERE d.is_controlled = TRUE
ORDER BY d.expiry_date;

-- Query 3: Pending procurement value
-- NL: "What is the total value of all pending procurement orders?"
SELECT
    s.supplier_name,
    COUNT(po.order_id)          AS pending_orders,
    SUM(po.quantity_ordered)    AS total_units_ordered,
    SUM(po.total_cost_usd)      AS total_value_usd
FROM procurement_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id
WHERE po.status = 'PENDING'
GROUP BY s.supplier_name
ORDER BY total_value_usd DESC;

-- Query 4: Top dispensed drugs in last 7 days
-- NL: "What are the most frequently dispensed drugs in the last 7 days?"
SELECT
    d.drug_name,
    d.drug_category,
    SUM(it.quantity)            AS total_dispensed,
    COUNT(it.txn_id)            AS dispense_events
FROM inventory_transactions it
JOIN drug_inventory d ON it.drug_id = d.drug_id
WHERE it.txn_type = 'DISPENSE'
  AND it.txn_date >= NOW() - INTERVAL '7 days'
GROUP BY d.drug_name, d.drug_category
ORDER BY total_dispensed DESC
LIMIT 10;

-- Query 5: Drugs expiring in next 60 days
-- NL: "Which drugs will expire within the next 60 days and what is their remaining stock value?"
SELECT
    d.drug_name,
    d.drug_category,
    d.current_stock,
    d.unit_of_measure,
    d.expiry_date,
    ROUND((d.expiry_date - CURRENT_DATE)::NUMERIC, 0)   AS days_to_expiry,
    ROUND(d.current_stock * d.unit_cost_usd, 2)          AS stock_value_at_risk_usd
FROM drug_inventory d
WHERE d.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days'
  AND d.current_stock > 0
ORDER BY d.expiry_date;
