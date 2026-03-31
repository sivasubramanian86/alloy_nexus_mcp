import os

def create_database():
    alloy_url = os.getenv("ALLOY_INIT_URL", "postgresql://postgres:REDACTED_PASSWORD@10.49.0.5:5432/postgres")
    try:
        conn = psycopg2.connect(alloy_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Starting Database Initialization...")
        
        # 1. Create pharma_inventory database
        try:
            cur.execute("CREATE DATABASE pharma_inventory;")
            print("SUCCESS: Database 'pharma_inventory' created.")
        except Exception as e:
            if "already exists" in str(e):
                print("INFO: Database 'pharma_inventory' already exists.")
            else:
                print(f"ERROR creating database: {e}")
                sys.exit(1)
        
        # 2. Re-connect to the new database to run scripts
        conn.close()
        new_conn_str = os.getenv("ALLOY_DB_URL", "postgresql://postgres:REDACTED_PASSWORD@10.49.0.5:5432/pharma_inventory")
        conn = psycopg2.connect(new_conn_str)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Loading Pharma Inventory Schema and Data...")
        # (Simplified schema injection or we can read the files)
        with open("01_setup_alloydb.sql", "r") as f:
            cur.execute(f.read())
        
        print("Enabling AlloyDB AI extensions...")
        with open("02_enable_alloydb_ai.sql", "r") as f:
            cur.execute(f.read())
            
        print("DATABASE INITIALIZATION COMPLETE.")
        conn.close()
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_database()
