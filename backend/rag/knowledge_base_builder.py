"""
Knowledge Base Builder for Legal Metrology Rules
Loads and structures all knowledge base files
"""

import yaml
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseBuilder:
    """
    Build and maintain the Legal Metrology knowledge base
    Loads rules, patterns, corrections, and templates
    """
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        """
        Initialize knowledge base builder
        
        Args:
            kb_dir: Path to knowledge base directory
        """
        self.kb_dir = Path(kb_dir)
        self.rules = []
        self.patterns = {}
        self.corrections = {}
        self.templates = {}
        self.documents = []
        self.metadata = []
        
        logger.info(f"Initializing KnowledgeBaseBuilder with dir: {kb_dir}")
        
    def build(self) -> Dict[str, Any]:
        """
        Build complete knowledge base
        
        Returns:
            Dictionary with all knowledge base components
        """
        logger.info("🔧 Building Legal Metrology knowledge base...")
        
        # Load rules
        self.rules = self._load_rules()
        logger.info(f"✅ Loaded {len(self.rules)} compliance rules")
        
        # Load patterns
        self.patterns = self._load_patterns()
        logger.info(f"✅ Loaded patterns for {len(self.patterns)} fields")
        
        # Load OCR corrections
        self.corrections = self._load_corrections()
        logger.info(f"✅ Loaded OCR corrections database")
        
        # Load templates (if available)
        self.templates = self._load_templates()
        logger.info(f"✅ Loaded {len(self.templates)} validation templates")
        
        # Prepare documents for vector store
        self._prepare_documents()
        logger.info(f"✅ Prepared {len(self.documents)} documents for indexing")
        
        return {
            'rules': self.rules,
            'patterns': self.patterns,
            'corrections': self.corrections,
            'templates': self.templates,
            'documents': self.documents,
            'metadata': self.metadata
        }
    
    def _load_rules(self) -> List[Dict]:
        """Load compliance rules from YAML files"""
        rules = []
        rules_dir = self.kb_dir / "lmpc_rules"
        
        if not rules_dir.exists():
            logger.warning(f"Rules directory not found: {rules_dir}")
            return rules
        
        for yaml_file in rules_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'rules' in data:
                        rules.extend(data['rules'])
                        logger.debug(f"Loaded {len(data['rules'])} rules from {yaml_file.name}")
            except Exception as e:
                logger.error(f"Error loading {yaml_file}: {e}")
        
        return rules
    
    def _load_patterns(self) -> Dict:
        """Load field extraction patterns"""
        patterns_file = self.kb_dir / "patterns" / "field_patterns.json"
        
        if not patterns_file.exists():
            logger.warning(f"Patterns file not found: {patterns_file}")
            return {}
        
        try:
            with open(patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('field_patterns', {})
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            return {}
    
    def _load_corrections(self) -> Dict:
        """Load OCR error corrections"""
        corrections_file = self.kb_dir / "corrections" / "ocr_errors.json"
        
        if not corrections_file.exists():
            logger.warning(f"Corrections file not found: {corrections_file}")
            return {}
        
        try:
            with open(corrections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading corrections: {e}")
            return {}
    
    def _load_templates(self) -> Dict:
        """Load validation templates"""
        templates = {}
        templates_dir = self.kb_dir / "validation_templates"
        
        if not templates_dir.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            return templates
        
        for yaml_file in templates_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'product_category' in data:
                        templates[data['product_category']] = data
                        logger.debug(f"Loaded template for {data['product_category']}")
            except Exception as e:
                logger.error(f"Error loading template {yaml_file}: {e}")
        
        return templates
    
    def _prepare_documents(self):
        """Prepare documents for vector store indexing"""
        self.documents = []
        self.metadata = []
        
        # Add rules as documents
        for rule in self.rules:
            # Rule description
            doc = f"{rule['field']}: {rule['description']}"
            self.documents.append(doc)
            self.metadata.append({
                'type': 'rule',
                'field': rule['field'],
                'rule_id': rule['rule_id'],
                'severity': rule.get('severity', 'medium')
            })
            
            # Rule examples
            for example in rule.get('examples', []):
                self.documents.append(example)
                self.metadata.append({
                    'type': 'example',
                    'field': rule['field'],
                    'rule_id': rule['rule_id']
                })
            
            # Rule patterns
            for pattern in rule.get('patterns', []):
                doc = f"{rule['field']} pattern: {pattern}"
                self.documents.append(doc)
                self.metadata.append({
                    'type': 'pattern',
                    'field': rule['field'],
                    'pattern': pattern
                })
        
        # Add semantic queries from patterns
        for field, pattern_data in self.patterns.items():
            for query in pattern_data.get('semantic_queries', []):
                self.documents.append(query)
                self.metadata.append({
                    'type': 'semantic_query',
                    'field': field
                })
        
        logger.info(f"Prepared {len(self.documents)} documents for vector indexing")
    
    def get_rule_by_field(self, field: str) -> Dict:
        """Get rule for a specific field"""
        for rule in self.rules:
            if rule['field'] == field:
                return rule
        return {}
    
    def get_pattern_for_field(self, field: str) -> Dict:
        """Get extraction pattern for a field"""
        return self.patterns.get(field, {})
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return {
            'total_rules': len(self.rules),
            'total_patterns': len(self.patterns),
            'total_documents': len(self.documents),
            'total_templates': len(self.templates),
            'fields_covered': list(self.patterns.keys())
        }


# Example usage
if __name__ == "__main__":
    # Build knowledge base
    kb = KnowledgeBaseBuilder()
    data = kb.build()
    
    # Print stats
    stats = kb.get_stats()
    print("\n📊 Knowledge Base Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get rule for MRP
    mrp_rule = kb.get_rule_by_field("mrp")
    print(f"\n📋 MRP Rule:")
    print(f"   Description: {mrp_rule.get('description')}")
    print(f"   Mandatory: {mrp_rule.get('mandatory')}")
    print(f"   Patterns: {mrp_rule.get('patterns')}")
