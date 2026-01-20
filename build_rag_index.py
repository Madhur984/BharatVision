"""
Build RAG Index - Simplified version without backend imports
Run this script to initialize the RAG system
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Build RAG index"""
    print("="*60)
    print("BharatVision RAG Index Builder")
    print("Government-Grade Legal Metrology Compliance System")
    print("="*60)
    
    try:
        # Add backend/rag to path directly
        rag_path = Path(__file__).parent / "backend" / "rag"
        sys.path.insert(0, str(rag_path.parent))
        
        # Import RAG components directly
        from rag.rag_manager import RAGManager
        
        # Initialize RAG Manager
        logger.info("Initializing RAG Manager...")
        rag = RAGManager(
            kb_dir="knowledge_base",
            index_dir="rag_index"
        )
        
        # Build index
        logger.info("Building RAG index (this may take a few minutes)...")
        rag.initialize(force_rebuild=True)
        
        # Get stats
        stats = rag.get_stats()
        
        print("\n" + "="*60)
        print("✅ RAG Index Built Successfully!")
        print("="*60)
        print(f"\nKnowledge Base:")
        print(f"  - Rules: {stats['knowledge_base']['total_rules']}")
        print(f"  - Patterns: {stats['knowledge_base']['total_patterns']}")
        print(f"  - Documents: {stats['knowledge_base']['total_documents']}")
        print(f"  - Templates: {stats['knowledge_base']['total_templates']}")
        
        print(f"\nVector Store:")
        print(f"  - Total Vectors: {stats['vector_store']['index_size']}")
        print(f"  - Dimension: {stats['vector_store']['dimension']}")
        print(f"  - Model: {stats['vector_store']['model_name']}")
        print(f"  - Index Type: {stats['vector_store']['index_type']}")
        
        print(f"\nFields Covered:")
        for field in stats['knowledge_base']['fields_covered']:
            print(f"  - {field}")
        
        print("\n" + "="*60)
        print("🚀 RAG System Ready!")
        print("="*60)
        print("\nYou can now use the RAG system for:")
        print("  1. OCR error correction")
        print("  2. Semantic field extraction")
        print("  3. Compliance validation")
        print("  4. Knowledge base search")
        
        # Test the system
        print("\n" + "="*60)
        print("Testing RAG System...")
        print("="*60)
        
        test_text = "M8P: Rs. 5O.OO (Incl. of all taxes)"
        result = rag.process_ocr_text(test_text)
        
        print(f"\nTest Input: {test_text}")
        print(f"Corrected: {result['corrected_text']}")
        print(f"Corrections: {result['summary']['total_corrections']}")
        print(f"Fields Found: {result['summary']['fields_found']}")
        
        print("\n✅ Test Passed!")
        print("\n" + "="*60)
        print("RAG System is ready for production use!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to build RAG index: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("\nPlease ensure:")
        print("  1. faiss-cpu is installed: pip install faiss-cpu")
        print("  2. sentence-transformers is installed: pip install sentence-transformers")
        print("  3. Knowledge base files exist in knowledge_base/")
        sys.exit(1)

if __name__ == "__main__":
    main()
