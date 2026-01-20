"""
FAISS Vector Store for Semantic Search
Uses sentence-transformers for offline embeddings
"""

import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manage FAISS vector store for semantic search
    Uses all-MiniLM-L6-v2 for fast, accurate embeddings (offline)
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize vector store
        
        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self.index = None
        self.documents = []
        self.metadata = []
        
        logger.info(f"Initializing VectorStore with model: {model_name}")
        
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence transformer model...")
                self.model = SentenceTransformer(self.model_name)
                logger.info("✅ Model loaded successfully")
            except ImportError:
                logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
        
    def build_index(self, documents: List[str], metadata: List[Dict]):
        """
        Build FAISS index from documents
        
        Args:
            documents: List of text documents to index
            metadata: List of metadata dicts for each document
        """
        if len(documents) != len(metadata):
            raise ValueError("Documents and metadata must have same length")
        
        logger.info(f"Building FAISS index for {len(documents)} documents...")
        
        # Load model
        self._load_model()
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.model.encode(
            documents, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        embeddings = embeddings.astype('float32')
        
        # Create FAISS index (exact search for maximum accuracy)
        logger.info("Creating FAISS index...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        
        self.documents = documents
        self.metadata = metadata
        
        logger.info(f"✅ FAISS index built with {self.index.ntotal} vectors")
        logger.info(f"   Dimension: {self.dimension}")
        logger.info(f"   Index type: Exact search (IndexFlatL2)")
        
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        min_score: Optional[float] = None
    ) -> List[Tuple[str, Dict, float]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score (optional)
            
        Returns:
            List of (document, metadata, distance) tuples
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        # Load model if needed
        self._load_model()
        
        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Return results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                # Convert distance to similarity score (lower distance = higher similarity)
                score = float(dist)
                
                # Filter by minimum score if specified
                if min_score is not None and score > min_score:
                    continue
                
                results.append((
                    self.documents[idx],
                    self.metadata[idx],
                    score
                ))
        
        return results
    
    def save(self, path: str):
        """
        Save index to disk
        
        Args:
            path: Directory path to save index
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        if self.index is None:
            raise ValueError("No index to save. Build index first.")
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # Save documents and metadata
        with open(path / "documents.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'model_name': self.model_name,
                'dimension': self.dimension
            }, f)
        
        logger.info(f"✅ Vector store saved to {path}")
        logger.info(f"   Files: index.faiss, documents.pkl")
        
    def load(self, path: str):
        """
        Load index from disk
        
        Args:
            path: Directory path containing saved index
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Index path not found: {path}")
        
        # Load FAISS index
        index_file = path / "index.faiss"
        if not index_file.exists():
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        self.index = faiss.read_index(str(index_file))
        
        # Load documents and metadata
        docs_file = path / "documents.pkl"
        if not docs_file.exists():
            raise FileNotFoundError(f"Documents file not found: {docs_file}")
        
        with open(docs_file, 'rb') as f:
            data = pickle.load(f)
            self.documents = data['documents']
            self.metadata = data['metadata']
            self.model_name = data.get('model_name', self.model_name)
            self.dimension = data.get('dimension', self.dimension)
        
        logger.info(f"✅ Vector store loaded from {path}")
        logger.info(f"   Vectors: {self.index.ntotal}")
        logger.info(f"   Model: {self.model_name}")
        
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'model_name': self.model_name,
            'index_type': 'IndexFlatL2 (Exact Search)'
        }


# Example usage
if __name__ == "__main__":
    # Create vector store
    vs = VectorStore()
    
    # Sample documents
    documents = [
        "MRP: ₹50.00 (Incl. of all taxes)",
        "Manufactured by ABC Foods Pvt Ltd, Delhi-110001",
        "Net Qty: 100g",
        "Best Before: 6 months from mfg date"
    ]
    
    metadata = [
        {"field": "mrp", "type": "example"},
        {"field": "manufacturer", "type": "example"},
        {"field": "net_quantity", "type": "example"},
        {"field": "best_before", "type": "example"}
    ]
    
    # Build index
    vs.build_index(documents, metadata)
    
    # Search
    results = vs.search("What is the price?", top_k=2)
    for doc, meta, score in results:
        print(f"Score: {score:.3f} | {meta['field']}: {doc}")
    
    # Save
    vs.save("vector_store_test")
    
    # Load
    vs2 = VectorStore()
    vs2.load("vector_store_test")
    print(f"\nLoaded stats: {vs2.get_stats()}")
