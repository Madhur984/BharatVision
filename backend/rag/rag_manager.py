"""
RAG Manager - Orchestrates all RAG components
Main interface for RAG-enhanced OCR and field extraction
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .vector_store import VectorStore
from .knowledge_base_builder import KnowledgeBaseBuilder
from .ocr_corrector import OCRCorrector
from .field_extractor import SemanticFieldExtractor

logger = logging.getLogger(__name__)

class RAGManager:
    """
    Manage RAG system for government-grade Legal Metrology compliance
    Orchestrates knowledge base, vector store, OCR correction, and field extraction
    """
    
    def __init__(self, kb_dir: str = "knowledge_base", index_dir: str = "rag_index"):
        """
        Initialize RAG Manager
        
        Args:
            kb_dir: Knowledge base directory
            index_dir: Directory to save/load vector index
        """
        self.kb_dir = Path(kb_dir)
        self.index_dir = Path(index_dir)
        
        # Components
        self.kb_builder = None
        self.vector_store = None
        self.ocr_corrector = None
        self.field_extractor = None
        
        # Data
        self.knowledge_base = None
        self.is_initialized = False
        
        logger.info("RAGManager initialized")
        
    def initialize(self, force_rebuild: bool = False):
        """
        Initialize RAG system
        
        Args:
            force_rebuild: Force rebuild of vector index
        """
        logger.info("🚀 Initializing RAG system...")
        
        # Step 1: Build knowledge base
        logger.info("📚 Loading knowledge base...")
        self.kb_builder = KnowledgeBaseBuilder(str(self.kb_dir))
        self.knowledge_base = self.kb_builder.build()
        
        # Step 2: Initialize or load vector store
        logger.info("🔍 Setting up vector store...")
        self.vector_store = VectorStore()
        
        if self.index_dir.exists() and not force_rebuild:
            # Load existing index
            try:
                logger.info("Loading existing vector index...")
                self.vector_store.load(str(self.index_dir))
                logger.info("✅ Vector index loaded")
            except Exception as e:
                logger.warning(f"Failed to load index: {e}. Building new index...")
                self._build_vector_index()
        else:
            # Build new index
            self._build_vector_index()
        
        # Step 3: Initialize OCR corrector
        logger.info("🔧 Initializing OCR corrector...")
        self.ocr_corrector = OCRCorrector(
            self.knowledge_base['corrections'],
            self.vector_store
        )
        
        # Step 4: Initialize field extractor
        logger.info("📋 Initializing field extractor...")
        self.field_extractor = SemanticFieldExtractor(
            self.knowledge_base['patterns'],
            self.vector_store
        )
        
        self.is_initialized = True
        logger.info("✅ RAG system initialized successfully")
        
        # Print stats
        self._print_stats()
        
    def _build_vector_index(self):
        """Build vector index from knowledge base"""
        logger.info("🔨 Building vector index...")
        
        documents = self.knowledge_base['documents']
        metadata = self.knowledge_base['metadata']
        
        self.vector_store.build_index(documents, metadata)
        
        # Save index
        self.vector_store.save(str(self.index_dir))
        logger.info(f"✅ Vector index saved to {self.index_dir}")
        
    def process_ocr_text(
        self, 
        ocr_text: str, 
        context: Optional[str] = None
    ) -> Dict:
        """
        Process OCR text with RAG enhancements
        
        Args:
            ocr_text: Raw OCR text
            context: Optional context for better corrections
            
        Returns:
            Dictionary with corrected text, extracted fields, and metadata
        """
        if not self.is_initialized:
            raise RuntimeError("RAG system not initialized. Call initialize() first.")
        
        logger.info("🔄 Processing OCR text with RAG...")
        
        # Step 1: Correct OCR errors
        corrected_text, corrections = self.ocr_corrector.correct_text(ocr_text, context)
        correction_stats = self.ocr_corrector.get_correction_stats(corrections)
        
        logger.info(f"Applied {correction_stats['total_corrections']} OCR corrections")
        
        # Step 2: Extract fields
        extracted_fields = self.field_extractor.extract_all_fields(corrected_text)
        
        found_fields = sum(1 for f in extracted_fields.values() if f['found'])
        logger.info(f"Extracted {found_fields}/{len(extracted_fields)} fields")
        
        # Step 3: Validate extracted fields
        validation_results = {}
        for field_name, field_data in extracted_fields.items():
            if field_data['found']:
                is_valid, errors = self.field_extractor.validate_extracted_field(
                    field_name, 
                    field_data['value']
                )
                validation_results[field_name] = {
                    'valid': is_valid,
                    'errors': errors
                }
        
        # Prepare result
        result = {
            'original_text': ocr_text,
            'corrected_text': corrected_text,
            'corrections': {
                'applied': corrections,
                'stats': correction_stats
            },
            'extracted_fields': extracted_fields,
            'validation': validation_results,
            'summary': {
                'total_corrections': correction_stats['total_corrections'],
                'fields_found': found_fields,
                'fields_total': len(extracted_fields),
                'fields_valid': sum(1 for v in validation_results.values() if v['valid'])
            }
        }
        
        logger.info("✅ OCR processing complete")
        return result
    
    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Tuple]:
        """
        Search knowledge base for relevant information
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of (document, metadata, score) tuples
        """
        if not self.is_initialized:
            raise RuntimeError("RAG system not initialized")
        
        return self.vector_store.search(query, top_k=top_k)
    
    def get_rule_for_field(self, field_name: str) -> Dict:
        """Get compliance rule for a field"""
        if not self.is_initialized:
            raise RuntimeError("RAG system not initialized")
        
        return self.kb_builder.get_rule_by_field(field_name)
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        if not self.is_initialized:
            return {'status': 'not_initialized'}
        
        kb_stats = self.kb_builder.get_stats()
        vs_stats = self.vector_store.get_stats()
        
        return {
            'status': 'initialized',
            'knowledge_base': kb_stats,
            'vector_store': vs_stats
        }
    
    def _print_stats(self):
        """Print system statistics"""
        stats = self.get_stats()
        
        logger.info("📊 RAG System Statistics:")
        logger.info(f"   Knowledge Base:")
        logger.info(f"      - Rules: {stats['knowledge_base']['total_rules']}")
        logger.info(f"      - Patterns: {stats['knowledge_base']['total_patterns']}")
        logger.info(f"      - Documents: {stats['knowledge_base']['total_documents']}")
        logger.info(f"   Vector Store:")
        logger.info(f"      - Vectors: {stats['vector_store']['index_size']}")
        logger.info(f"      - Dimension: {stats['vector_store']['dimension']}")
        logger.info(f"      - Model: {stats['vector_store']['model_name']}")


# Example usage
if __name__ == "__main__":
    # Initialize RAG Manager
    rag = RAGManager()
    rag.initialize()
    
    # Process OCR text
    ocr_text = """
    Product Label
    M8P: Rs. 5O.OO (Incl. of all taxes)
    Mfd by ABC Foods, Delhi-110001
    Net 0ty: 100g
    """
    
    result = rag.process_ocr_text(ocr_text, context="product label")
    
    print("\n" + "="*50)
    print("RAG Processing Result")
    print("="*50)
    print(f"\nOriginal Text:\n{result['original_text']}")
    print(f"\nCorrected Text:\n{result['corrected_text']}")
    print(f"\nCorrections Applied: {result['summary']['total_corrections']}")
    print(f"Fields Found: {result['summary']['fields_found']}/{result['summary']['fields_total']}")
    print(f"Fields Valid: {result['summary']['fields_valid']}")
    
    print("\n" + "="*50)
    print("Extracted Fields")
    print("="*50)
    for field_name, field_data in result['extracted_fields'].items():
        if field_data['found']:
            print(f"\n{field_name}:")
            print(f"  Value: {field_data['value']}")
            print(f"  Confidence: {field_data['confidence']:.2f}")
            
            if field_name in result['validation']:
                val = result['validation'][field_name]
                print(f"  Valid: {val['valid']}")
                if val['errors']:
                    print(f"  Errors: {val['errors']}")
