-- =============================================================================
-- QuerySage: Hospital Pharmaceutical Inventory & Procurement Dataset
-- AlloyDB for PostgreSQL — Schema + Seed Data
-- Use Case: "Querying hospital pharmaceutical inventory and procurement data
--            to surface supply-chain insights via natural language."
-- =============================================================================

-- Step 1: Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE;

-- Step 2: Grant Vertex AI access to AlloyDB SA
-- Run this in Cloud Shell before executing SQL:
-- gcloud projects add-iam-policy-binding PROJECT_ID \
--   --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-alloydb.iam.gserviceaccount.com" \
--   --role="roles/aiplatform.user"

-- =============================================================================
-- SCHEMA: Pharmaceutical Inventory
-- =============================================================================

DROP TABLE IF EXISTS procurement_orders CASCADE;
DROP TABLE IF EXISTS inventory_transactions CASCADE;
DROP TABLE IF EXISTS drug_inventory CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS wards CASCADE;

-- Suppliers master table
CREATE TABLE suppliers (
    supplier_id     SERIAL PRIMARY KEY,
    supplier_name   VARCHAR(200) NOT NULL,
    country         VARCHAR(100) NOT NULL,
    lead_time_days  INT          NOT NULL DEFAULT 7,
    reliability_pct DECIMAL(5,2) NOT NULL DEFAULT 95.0,
    contact_email   VARCHAR(255),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Hospital wards reference
CREATE TABLE wards (
    ward_id     SERIAL PRIMARY KEY,
    ward_name   VARCHAR(100) NOT NULL,
    ward_type   VARCHAR(50)  NOT NULL,  -- ICU, General, Pediatric, Emergency, OT
    bed_count   INT          NOT NULL,
    floor_number INT         NOT NULL
);

-- Drug inventory master — the core table, custom schema per problem statement
CREATE TABLE drug_inventory (
    drug_id          SERIAL PRIMARY KEY,
    drug_name        VARCHAR(255)   NOT NULL,
    generic_name     VARCHAR(255)   NOT NULL,
    drug_category    VARCHAR(100)   NOT NULL,  -- Antibiotic, Analgesic, Cardiac, etc.
    unit_of_measure  VARCHAR(20)    NOT NULL,  -- tablets, vials, ml, mg
    current_stock    INT            NOT NULL   DEFAULT 0,
    reorder_level    INT            NOT NULL   DEFAULT 100,
    max_stock_level  INT            NOT NULL   DEFAULT 1000,
    unit_cost_usd    DECIMAL(10,4)  NOT NULL,
    supplier_id      INT            REFERENCES suppliers(supplier_id),
    expiry_date      DATE,
    is_controlled    BOOLEAN        NOT NULL   DEFAULT FALSE,  -- narcotic / controlled substance
    storage_temp     VARCHAR(50),   -- Room temp / Refrigerated / Frozen
    ward_id          INT            REFERENCES wards(ward_id),
    last_updated     TIMESTAMPTZ    NOT NULL   DEFAULT NOW(),
    -- AlloyDB AI: semantic search embedding column
    description_embedding VECTOR(768)
);

-- Procurement orders
CREATE TABLE procurement_orders (
    order_id        SERIAL PRIMARY KEY,
    drug_id         INT           NOT NULL REFERENCES drug_inventory(drug_id),
    supplier_id     INT           NOT NULL REFERENCES suppliers(supplier_id),
    order_date      DATE          NOT NULL,
    expected_date   DATE          NOT NULL,
    received_date   DATE,
    quantity_ordered INT          NOT NULL,
    quantity_received INT,
    unit_price_usd  DECIMAL(10,4) NOT NULL,
    total_cost_usd  DECIMAL(12,4) GENERATED ALWAYS AS (quantity_ordered * unit_price_usd) STORED,
    status          VARCHAR(30)   NOT NULL DEFAULT 'PENDING',  -- PENDING, DELIVERED, PARTIAL, CANCELLED
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Inventory transactions (dispensing / restocking log)
CREATE TABLE inventory_transactions (
    txn_id          SERIAL PRIMARY KEY,
    drug_id         INT          NOT NULL REFERENCES drug_inventory(drug_id),
    ward_id         INT          REFERENCES wards(ward_id),
    txn_type        VARCHAR(20)  NOT NULL,  -- DISPENSE, RESTOCK, WASTE, RETURN
    quantity        INT          NOT NULL,
    txn_date        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    performed_by    VARCHAR(100) NOT NULL,  -- staff ID / name
    notes           TEXT
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX idx_drug_inventory_category   ON drug_inventory(drug_category);
CREATE INDEX idx_drug_inventory_supplier   ON drug_inventory(supplier_id);
CREATE INDEX idx_drug_inventory_ward       ON drug_inventory(ward_id);
CREATE INDEX idx_drug_inventory_expiry     ON drug_inventory(expiry_date);
CREATE INDEX idx_procurement_drug          ON procurement_orders(drug_id);
CREATE INDEX idx_procurement_status       ON procurement_orders(status);
CREATE INDEX idx_txn_drug_date            ON inventory_transactions(drug_id, txn_date);
CREATE INDEX idx_txn_ward                 ON inventory_transactions(ward_id);

-- Vector index for semantic search (AlloyDB pgvector)
CREATE INDEX idx_drug_embedding
    ON drug_inventory USING ivfflat (description_embedding vector_cosine_ops)
    WITH (lists = 50);

-- =============================================================================
-- SEED DATA — Suppliers
-- =============================================================================
INSERT INTO suppliers (supplier_name, country, lead_time_days, reliability_pct, contact_email) VALUES
    ('PharmaCo India Ltd',       'India',         5,  98.5, 'orders@pharmacoindia.com'),
    ('MediGlobal Singapore',     'Singapore',     7,  97.2, 'supply@mediglobal.sg'),
    ('EuroPharma GmbH',         'Germany',       14, 99.1, 'orders@europharma.de'),
    ('QuickMed Distributors',    'India',          3, 94.8, 'sales@quickmed.in'),
    ('BioNova Solutions',        'USA',           21, 99.8, 'procurement@bionova.com'),
    ('AsiaHealth Supplies',      'Malaysia',       8, 95.5, 'orders@asiahealth.my');

-- =============================================================================
-- SEED DATA — Wards
-- =============================================================================
INSERT INTO wards (ward_name, ward_type, bed_count, floor_number) VALUES
    ('ICU Alpha',          'ICU',       20, 3),
    ('ICU Beta',           'ICU',       15, 4),
    ('General Ward A',     'General',   50, 1),
    ('General Ward B',     'General',   45, 2),
    ('Pediatric Care',     'Pediatric', 30, 2),
    ('Emergency Dept',     'Emergency', 25, 0),
    ('Operation Theatre',  'OT',         8, 5),
    ('Cardiac Care Unit',  'CCU',       18, 4);

-- =============================================================================
-- SEED DATA — Drug Inventory (custom dataset — not from lab)
-- =============================================================================
INSERT INTO drug_inventory
    (drug_name, generic_name, drug_category, unit_of_measure,
     current_stock, reorder_level, max_stock_level, unit_cost_usd,
     supplier_id, expiry_date, is_controlled, storage_temp, ward_id) VALUES
    -- Antibiotics
    ('Augmentin 625mg',      'Amoxicillin+Clavulanate', 'Antibiotic',  'tablets', 850,  200, 2000, 0.85,  1, '2026-12-31', FALSE, 'Room temp',    3),
    ('Meropenem 1g Vial',    'Meropenem',               'Antibiotic',  'vials',   120,   50,  500, 12.50, 2, '2026-06-30', FALSE, 'Refrigerated', 1),
    ('Vancomycin 500mg',     'Vancomycin',              'Antibiotic',  'vials',    80,   40,  400, 18.75, 3, '2026-09-15', FALSE, 'Refrigerated', 1),
    ('Azithromycin 500mg',   'Azithromycin',            'Antibiotic',  'tablets', 600,  150, 1500,  0.60, 4, '2027-03-31', FALSE, 'Room temp',    3),
    -- Analgesics
    ('Morphine 10mg/ml',     'Morphine Sulfate',        'Analgesic',   'vials',    45,   20,  200, 22.00, 5, '2026-11-30', TRUE,  'Refrigerated', 1),
    ('Paracetamol 500mg',    'Acetaminophen',           'Analgesic',   'tablets',1200,  300, 3000,  0.05, 4, '2027-06-30', FALSE, 'Room temp',    3),
    ('Tramadol 50mg',        'Tramadol HCl',            'Analgesic',   'tablets', 300,  100, 1000,  0.45, 1, '2026-08-31', TRUE,  'Room temp',    2),
    ('Ketorolac 30mg/ml',    'Ketorolac Tromethamine',  'Analgesic',   'vials',   150,   50,  500,  3.20, 2, '2026-05-31', FALSE, 'Room temp',    7),
    -- Cardiac
    ('Digoxin 0.25mg',       'Digoxin',                 'Cardiac',     'tablets', 400,  100, 1000,  0.30, 3, '2027-01-31', FALSE, 'Room temp',    8),
    ('Amiodarone 200mg',     'Amiodarone HCl',          'Cardiac',     'tablets', 200,   80,  800,  1.20, 1, '2026-10-31', FALSE, 'Room temp',    8),
    ('Heparin 5000IU/ml',    'Heparin Sodium',          'Anticoagulant','vials',  220,   60,  600,  8.50, 5, '2026-07-31', FALSE, 'Refrigerated', 1),
    ('Warfarin 5mg',         'Warfarin Sodium',         'Anticoagulant','tablets', 350, 100, 1000,  0.25, 4, '2027-02-28', FALSE, 'Room temp',    8),
    -- Anaesthesia / OT
    ('Propofol 200mg/20ml',  'Propofol',                'Anaesthetic', 'vials',    60,   20,  200, 28.00, 5, '2026-04-30', FALSE, 'Refrigerated', 7),
    ('Ketamine 500mg/10ml',  'Ketamine HCl',            'Anaesthetic', 'vials',    35,   15,  150, 35.00, 3, '2026-11-15', TRUE,  'Room temp',    7),
    ('Fentanyl 100mcg/2ml',  'Fentanyl Citrate',        'Analgesic',   'vials',    40,   15,  150, 45.00, 5, '2026-09-30', TRUE,  'Refrigerated', 7),
    -- Insulin / Endocrine
    ('Insulin Glargine 100U','Insulin Glargine',        'Endocrine',   'vials',   180,   60, 600, 24.00, 2, '2026-06-15', FALSE, 'Refrigerated', 3),
    ('Metformin 500mg',      'Metformin HCl',           'Endocrine',   'tablets', 900,  200, 2000,  0.08, 4, '2027-04-30', FALSE, 'Room temp',    3),
    -- IV Fluids
    ('Normal Saline 1L',     'Sodium Chloride 0.9%',    'IV Fluid',    'bags',    500,  150, 2000,  1.50, 6, '2027-12-31', FALSE, 'Room temp',    6),
    ('Ringer Lactate 1L',    'Lactated Ringer Solution','IV Fluid',    'bags',    380,  120, 1500,  1.80, 6, '2027-12-31', FALSE, 'Room temp',    6),
    -- Low stock items (for alert demo)
    ('Adenosine 6mg/2ml',    'Adenosine',               'Cardiac',     'vials',    12,   25,  250, 55.00, 5, '2026-05-31', FALSE, 'Refrigerated', 8),
    ('Protamine 10mg/ml',    'Protamine Sulfate',       'Anticoagulant','vials',    8,   20,  200, 40.00, 3, '2026-08-31', FALSE, 'Refrigerated', 7),
    ('Oxytocin 10IU/ml',     'Oxytocin',                'Hormone',     'vials',    18,   30,  300, 12.00, 2, '2026-04-15', FALSE, 'Refrigerated', 6);

-- =============================================================================
-- SEED DATA — Procurement Orders
-- =============================================================================
INSERT INTO procurement_orders
    (drug_id, supplier_id, order_date, expected_date, received_date,
     quantity_ordered, quantity_received, unit_price_usd, status) VALUES
    (1,  1, '2026-03-01', '2026-03-06', '2026-03-06',  500, 500, 0.85, 'DELIVERED'),
    (2,  2, '2026-03-10', '2026-03-17', '2026-03-18',  100,  95, 12.50,'DELIVERED'),
    (3,  3, '2026-03-05', '2026-03-19', NULL,           200, NULL,18.75,'PENDING'),
    (5,  5, '2026-03-15', '2026-04-05', NULL,            50, NULL,22.00,'PENDING'),
    (11, 5, '2026-03-20', '2026-04-10', NULL,           150, NULL, 8.50,'PENDING'),
    (13, 5, '2026-03-22', '2026-04-12', NULL,            80, NULL,28.00,'PENDING'),
    (16, 2, '2026-03-12', '2026-03-19', '2026-03-20',  120, 120,24.00,'DELIVERED'),
    (20, 5, '2026-03-25', '2026-04-15', NULL,           100, NULL,55.00,'PENDING'),
    (21, 3, '2026-03-28', '2026-04-11', NULL,            60, NULL,40.00,'PENDING'),
    (6,  4, '2026-02-15', '2026-02-18', '2026-02-18', 1000,1000, 0.05,'DELIVERED'),
    (18, 6, '2026-03-01', '2026-03-09', '2026-03-10',  300, 300, 1.50,'DELIVERED'),
    (19, 6, '2026-03-01', '2026-03-09', '2026-03-10',  200, 200, 1.80,'DELIVERED');

-- =============================================================================
-- SEED DATA — Inventory Transactions (recent 30-day sample)
-- =============================================================================
INSERT INTO inventory_transactions (drug_id, ward_id, txn_type, quantity, txn_date, performed_by, notes) VALUES
    (1,  3, 'DISPENSE', 50, NOW() - INTERVAL '2 days',    'Nurse Priya',    'Ward A morning round'),
    (1,  4, 'DISPENSE', 30, NOW() - INTERVAL '1 day',     'Nurse Rahul',    'Ward B afternoon round'),
    (2,  1, 'DISPENSE', 10, NOW() - INTERVAL '3 days',    'Dr Sharma',      'ICU critical patient'),
    (5,  1, 'DISPENSE',  5, NOW() - INTERVAL '1 day',     'Dr Meera',       'Post-op pain management'),
    (6,  3, 'DISPENSE',100, NOW() - INTERVAL '4 hours',   'Pharmacist Jay', 'Bulk dispense gen ward'),
    (11, 1, 'DISPENSE', 20, NOW() - INTERVAL '6 hours',   'Dr Kumar',       'ICU anticoagulation'),
    (13, 7, 'DISPENSE',  5, NOW() - INTERVAL '1 day',     'Dr Nair',        'OT - elective surgery'),
    (18, 6, 'DISPENSE', 40, NOW() - INTERVAL '2 hours',   'Nurse Divya',    'Emergency IV fluid'),
    (19, 6, 'DISPENSE', 35, NOW() - INTERVAL '2 hours',   'Nurse Divya',    'Emergency IV fluid'),
    (20, 8, 'DISPENSE',  2, NOW() - INTERVAL '5 hours',   'Dr Krishnan',    'Cardiac emergency'),
    (1,  3, 'RESTOCK', 200, NOW() - INTERVAL '5 days',    'Pharmacist Jay', 'Weekly restock'),
    (6,  3, 'RESTOCK', 500, NOW() - INTERVAL '7 days',    'Pharmacist Jay', 'Bulk restock from delivery'),
    (16, 3, 'RESTOCK', 100, NOW() - INTERVAL '10 days',   'Pharmacist Jay', 'Insulin delivery received'),
    (7,  2, 'WASTE',    10, NOW() - INTERVAL '15 days',   'Nurse Radha',    'Expired batch disposal'),
    (22, 6, 'DISPENSE',  3, NOW() - INTERVAL '3 hours',   'Dr Mehta',       'OB emergency');

-- =============================================================================
-- Step 3: Register Vertex AI embedding model (run after AlloyDB AI is enabled)
-- =============================================================================
-- CALL google_ml.create_model(
--     'text-embedding-005',
--     'publishers/google/models/text-embedding-005',
--     json_build_object('model_type', 'text_embedding')
-- );

-- Step 4: Generate embeddings for drug descriptions
-- UPDATE drug_inventory
-- SET description_embedding = google_ml.embedding(
--     'text-embedding-005',
--     drug_name || ' ' || generic_name || ' ' || drug_category || ' ' ||
--     unit_of_measure || COALESCE(' ' || storage_temp, '')
-- )::vector(768);
