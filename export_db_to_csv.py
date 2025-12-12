"""
Export Database to CSV
=======================
Simple script to export the scraped products database to a readable CSV file.

Usage:
    python export_db_to_csv.py
    
Output:
    exported_products.csv - Contains all scraped products in readable format
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import DatabaseManager

def main():
    # Initialize database manager
    db = DatabaseManager(db_path="scraped_results.db")
    
    # Export to CSV
    output_file = "exported_products.csv"
    result = db.export_to_csv(output_file)
    
    if result:
        print(f"✅ Successfully exported database to: {output_file}")
        print(f"📂 You can now open this file in Excel or any text editor")
        
        # Show count
        products = db.get_all_products()
        print(f"📊 Total products exported: {len(products)}")
    else:
        print("❌ Failed to export database")

if __name__ == "__main__":
    main()
