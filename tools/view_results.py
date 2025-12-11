import sqlite3
import pandas as pd
from pathlib import Path

# Path to the database
db_path = Path("app_data.db")

def inspect_image_uploads():
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        
        # Query image_uploads table
        query = "SELECT * FROM image_uploads ORDER BY uploaded_at DESC"
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        if df.empty:
            print("⚠️ No upload records found in the database. (Table 'image_uploads' is empty)")
        else:
            print(f"✅ Found {len(df)} upload records in '{db_path}':\n")
            # Display relevant columns
            cols = ['id', 'username', 'filename', 'uploaded_at', 'confidence', 'compliance_status'] 
            # Note: compliance_status might not be in the table based on database.py schema, let's check headers first
            
            print(df.to_string())
            print(f"\nExample Extracted Text (Latest):")
            print("-" * 40)
            print(df.iloc[0]['extracted_text'][:500] + "...")
            print("-" * 40)

    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    inspect_image_uploads()
