"""
Intelligent Chatbot for Legal Metrology Compliance Checker
Provides contextual suggestions and guidance based on validation/extraction results
"""

import streamlit as st
import json
import openai
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from .schemas import ValidationResult, ExtractedFields
from .rules_engine import load_rules
from .json_utils import safe_json_dumps


class ChatMessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    type: ChatMessageType
    content: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None


class ComplianceChatbot:
    """Intelligent chatbot for Legal Metrology compliance assistance"""
    
    def __init__(self):
        try:
            self.rules = load_rules()
        except Exception as e:
            # Fallback if rules not available
            self.rules = {}
        self.conversation_history: List[ChatMessage] = []
        self.session_context = {}
        
        # Initialize OpenAI client
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
        openai.api_key = self.openai_api_key
        self.client = True  # Flag to indicate OpenAI is available
    
    def add_message(self, message_type: ChatMessageType, content: str, context: Optional[Dict] = None):
        """Add a message to the conversation history"""
        message = ChatMessage(
            type=message_type,
            content=content,
            timestamp=datetime.now(),
            context=context
        )
        self.conversation_history.append(message)
        
        # Keep only last 20 messages to prevent memory issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def analyze_validation_result(self, result: ValidationResult, fields: ExtractedFields) -> List[str]:
        """Analyze validation result and generate intelligent suggestions using OpenAI"""
        try:
            # Use OpenAI for intelligent analysis
            return self._get_openai_validation_analysis(result, fields)
        except Exception as e:
            # Fallback to rule-based analysis
            return self._get_fallback_validation_analysis(result, fields)
    
    def _get_openai_validation_analysis(self, result: ValidationResult, fields: ExtractedFields) -> List[str]:
        """Generate validation analysis using OpenAI"""
        
        # Prepare context for OpenAI
        validation_context = {
            "compliance_score": result.score,
            "is_compliant": result.is_compliant,
            "issues": [{"level": issue.level, "field": issue.field, "message": issue.message} for issue in result.issues],
            "extracted_fields": fields.model_dump()
        }
        
        prompt = f"""
        As an expert in Automated Compliance Checker for Legal Metrology Declarations on E-Commerce Platforms, analyze this validation result for an e-commerce product listing and provide 3-5 specific, actionable compliance suggestions.
        
        E-COMMERCE PRODUCT VALIDATION CONTEXT:
        - Compliance Score: {result.score}/100
        - Listing Status: {'✅ COMPLIANT for E-commerce' if result.is_compliant else '❌ NON-COMPLIANT - Cannot list on e-commerce platform'}
        - Legal Metrology Issues: {len(result.issues)} violations detected
        
        COMPLIANCE VIOLATIONS DETECTED:
        {safe_json_dumps([{"severity": issue.level, "field": issue.field, "violation": issue.message} for issue in result.issues], indent=2)}
        
        EXTRACTED PRODUCT DATA:
        {safe_json_dumps(fields.model_dump(), indent=2)}
        
        PROVIDE E-COMMERCE COMPLIANCE SUGGESTIONS:
        Format: [PRIORITY] [EMOJI] [ACTION] - [Legal Metrology Rule Reference & Implementation]
        
        Focus on E-COMMERCE SPECIFIC REQUIREMENTS:
        🛒 Platform listing compliance for marketplaces like Amazon, Flipkart
        ⚖️ Legal Metrology Act 2009 mandatory declarations
        📋 Packaged Commodities Rules 2011 requirements  
        💰 MRP display and pricing compliance
        📦 Net quantity declaration standards
        🏭 Manufacturer/Importer information completeness
        🌐 Country of origin for imported products
        📱 Mobile-friendly compliance display
        🔍 Search visibility and consumer protection
        ⚠️ Penalty avoidance (up to ₹25,000 fines)
        
        Include specific Legal Metrology rule sections where applicable.
        Prioritize issues that prevent e-commerce listing.
        """
        
        try:
            if not self.client:
                raise Exception("OpenAI client not available")
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            # Parse the response into individual suggestions
            suggestions_text = response.choices[0].message.content.strip()
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and s.strip()[0].isdigit()]
            
            # If parsing fails, return the full response as a single suggestion
            if not suggestions:
                suggestions = [suggestions_text]
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            raise e
    
    def _get_fallback_validation_analysis(self, result: ValidationResult, fields: ExtractedFields) -> List[str]:
        """Fallback validation analysis when OpenAI is unavailable"""
        suggestions = []
        
        # Analyze compliance score
        if result.score >= 90:
            suggestions.append("🎉 Excellent compliance! Your product data meets all Legal Metrology requirements. Consider this a model for future products.")
        elif result.score >= 80:
            suggestions.append("✅ Good compliance with minor issues. Review the warnings below and make small adjustments.")
        elif result.score >= 60:
            suggestions.append("⚠️ Moderate compliance issues detected. Focus on the critical errors first, then address warnings.")
        else:
            suggestions.append("🚨 Significant compliance issues found. This product requires substantial corrections before it can meet Legal Metrology standards.")
        
        # Analyze specific issues
        critical_issues = [issue for issue in result.issues if issue.level == "error"]
        warning_issues = [issue for issue in result.issues if issue.level == "warning"]
        
        if critical_issues:
            suggestions.append(f"🔴 {len(critical_issues)} critical issues must be resolved immediately. These are mandatory for compliance.")
            
            # Specific suggestions for common critical issues
            for issue in critical_issues[:3]:  # Limit to top 3
                if "MRP" in issue.field:
                    suggestions.append("💰 MRP Issue: Ensure the Maximum Retail Price is clearly stated and matches the actual selling price.")
                elif "quantity" in issue.field.lower():
                    suggestions.append("📦 Quantity Issue: Net quantity must be prominently displayed with proper units (g, kg, ml, l, etc.).")
                elif "manufacturer" in issue.field.lower():
                    suggestions.append("🏭 Manufacturer Issue: Include complete manufacturer name and address as required by law.")
        
        if warning_issues:
            suggestions.append(f"🟡 {len(warning_issues)} warnings should be addressed to improve compliance and avoid potential issues.")
        
        # Analyze missing fields
        missing_fields = self._analyze_missing_fields(fields)
        if missing_fields:
            suggestions.append(f"📝 Missing Information: Consider adding {', '.join(missing_fields[:3])} to improve compliance.")
        
        # Industry-specific suggestions
        suggestions.extend(self._get_industry_suggestions(fields))
        
        return suggestions
    
    def analyze_extraction_result(self, fields: ExtractedFields, confidence_score: float) -> List[str]:
        """Analyze extraction result and provide suggestions using OpenAI"""
        try:
            # Use OpenAI for intelligent analysis
            return self._get_openai_extraction_analysis(fields, confidence_score)
        except Exception as e:
            # Fallback to rule-based analysis
            return self._get_fallback_extraction_analysis(fields, confidence_score)
    
    def _get_openai_extraction_analysis(self, fields: ExtractedFields, confidence_score: float) -> List[str]:
        """Generate extraction analysis using OpenAI"""
        
        prompt = f"""
        As an expert in Automated Compliance Checker for Legal Metrology Declarations on E-Commerce Platforms, analyze this OCR text extraction result from an e-commerce product listing and provide 3-5 specific suggestions for improving automated compliance detection.
        
        E-COMMERCE PRODUCT EXTRACTION ANALYSIS:
        - OCR Confidence Score: {confidence_score}/100
        - Automated Extraction Quality: {'🟢 EXCELLENT - Ready for e-commerce compliance' if confidence_score >= 85 else '🟡 GOOD - Suitable for platform listing' if confidence_score >= 70 else '🟠 MODERATE - Needs improvement for compliance' if confidence_score >= 50 else '🔴 POOR - Cannot reliably validate compliance'}
        
        EXTRACTED E-COMMERCE PRODUCT DATA:
        {safe_json_dumps(fields.model_dump(), indent=2)}
        
        PROVIDE E-COMMERCE EXTRACTION IMPROVEMENT SUGGESTIONS:
        Format: [PRIORITY] [EMOJI] [TECHNICAL ACTION] - [E-commerce Compliance Impact]
        
        Focus on E-COMMERCE PLATFORM REQUIREMENTS:
        🛒 Marketplace listing automation (Amazon, Flipkart, etc.)
        🔍 OCR accuracy for Legal Metrology mandatory fields
        📱 Mobile product image optimization
        ⚖️ Automated compliance validation pipeline
        💰 MRP extraction accuracy for pricing compliance
        📦 Net quantity detection for consumer protection
        🏭 Manufacturer data extraction completeness
        🌐 Country of origin identification for imports
        📊 Bulk processing optimization for large catalogs
        🤖 Machine learning model training data quality
        📸 Image preprocessing for better text recognition
        ⚡ Real-time compliance scoring integration
        
        CRITICAL E-COMMERCE FIELDS TO EXTRACT:
        - MRP (Maximum Retail Price) - Mandatory display
        - Net Quantity with units - Consumer protection requirement
        - Manufacturer/Packer/Importer with address - Legal requirement
        - Country of Origin - Import compliance
        - Product dimensions - Where applicable
        - Manufacturing/Expiry dates - Food/pharma products
        - Certification marks (ISI/BIS/AGMARK) - Where mandatory
        
        Prioritize suggestions that improve automated compliance validation for e-commerce platforms.
        Include technical implementation recommendations.
        """
        
        try:
            if not self.client:
                raise Exception("OpenAI client not available")
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            # Parse the response into individual suggestions
            suggestions_text = response.choices[0].message.content.strip()
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and s.strip()[0].isdigit()]
            
            # If parsing fails, return the full response as a single suggestion
            if not suggestions:
                suggestions = [suggestions_text]
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            raise e
    
    def _get_fallback_extraction_analysis(self, fields: ExtractedFields, confidence_score: float) -> List[str]:
        """Fallback extraction analysis when OpenAI is unavailable"""
        suggestions = []
        
        # Confidence-based suggestions
        if confidence_score >= 85:
            suggestions.append("🔍 Excellent text extraction! All major fields were successfully identified.")
        elif confidence_score >= 70:
            suggestions.append("📊 Good extraction with some fields identified. Review the extracted data for accuracy.")
        elif confidence_score >= 50:
            suggestions.append("⚠️ Moderate extraction quality. Consider uploading a clearer image or checking the text quality.")
        else:
            suggestions.append("🚨 Low extraction quality detected. The image may be blurry or the text may be unclear. Try uploading a higher quality image.")
        
        # Field-specific suggestions
        if not fields.mrp_raw:
            suggestions.append("💰 No MRP found: Ensure the Maximum Retail Price is clearly visible in the image.")
        
        if not fields.net_quantity_raw:
            suggestions.append("📦 No quantity found: Make sure the net quantity is clearly displayed with proper units.")
        
        if not fields.manufacturer_name:
            suggestions.append("🏭 No manufacturer found: Ensure manufacturer name and address are visible in the image.")
        
        if not fields.country_of_origin:
            suggestions.append("🌍 No country of origin found: This information is often required for compliance.")
        
        # Quality improvement suggestions
        suggestions.extend(self._get_extraction_improvement_tips())
        
        return suggestions
    
    def _analyze_missing_fields(self, fields: ExtractedFields) -> List[str]:
        """Analyze which important fields are missing"""
        missing = []
        
        required_fields = {
            "MRP": fields.mrp_raw,
            "Net Quantity": fields.net_quantity_raw,
            "Manufacturer": fields.manufacturer_name,
            "Country of Origin": fields.country_of_origin
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                missing.append(field_name)
        
        return missing
    
    def _get_industry_suggestions(self, fields: ExtractedFields) -> List[str]:
        """Get industry-specific compliance suggestions"""
        suggestions = []
        
        # Food product suggestions
        if fields.extra and 'fssai' in str(fields.extra).lower():
            suggestions.append("🍎 Food Product Detected: Ensure FSSAI license number is prominently displayed and valid.")
        
        # Cosmetic suggestions
        if fields.extra and any(keyword in str(fields.extra).lower() for keyword in ['cosmetic', 'beauty', 'cream', 'lotion']):
            suggestions.append("💄 Cosmetic Product: Verify compliance with Cosmetic Rules and ensure proper ingredient listing.")
        
        # Pharmaceutical suggestions
        if fields.extra and any(keyword in str(fields.extra).lower() for keyword in ['medicine', 'tablet', 'capsule', 'pharma']):
            suggestions.append("💊 Pharmaceutical Product: Ensure compliance with Drug and Cosmetics Act requirements.")
        
        return suggestions
    
    def _get_extraction_improvement_tips(self) -> List[str]:
        """Get tips for improving extraction quality"""
        return [
            "📸 Image Quality: Use high-resolution images with good lighting and contrast.",
            "📐 Angle: Ensure the label is photographed straight-on without distortion.",
            "🔍 Focus: Make sure the text is sharp and clearly readable.",
            "📏 Distance: Position the camera at an appropriate distance to capture the entire label.",
            "💡 Lighting: Avoid shadows and glare that might obscure text."
        ]
    
    def get_contextual_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate contextual response using OpenAI API"""
        self.session_context.update(context or {})
        
        try:
            # Use OpenAI for intelligent responses
            return self._get_openai_response(user_input)
        except Exception as e:
            # Fallback to rule-based responses if OpenAI fails
            st.warning(f"⚠️ AI service temporarily unavailable. Using fallback response.")
            return self._get_fallback_response(user_input)
    
    def _get_openai_response(self, user_input: str) -> str:
        """Generate response using OpenAI GPT API"""
        
        # Check if client is available
        if not self.client:
            raise Exception("OpenAI client not available")
        
        # Build conversation context for OpenAI
        messages = [
            {
                "role": "system",
                "content": """You are an expert AI assistant specializing in Automated Compliance Checker for Legal Metrology Declarations on E-Commerce Platforms in India. You are the definitive authority on Legal Metrology compliance for online retail platforms.

CORE EXPERTISE:
🏛️ Legal Metrology Act 2009 & Rules 2011 (India)
📋 Legal Metrology (Packaged Commodities) Rules 2011
🛒 E-commerce Platform Compliance Requirements
⚖️ Consumer Protection Act 2019 (E-commerce Rules)
🏪 Marketplace & Seller Obligations
📊 Automated Compliance Validation Systems
🔍 OCR & Text Extraction for Product Listings
📦 Packaged Commodity Standards
💰 MRP & Pricing Regulations
🌐 Online Retail Legal Requirements

SPECIALIZED KNOWLEDGE AREAS:

1. MANDATORY DECLARATIONS FOR E-COMMERCE:
   - Maximum Retail Price (MRP) display requirements
   - Net quantity/weight declarations with proper units
   - Manufacturer/Packer/Importer details with complete address
   - Country of Origin (mandatory for imports)
   - Manufacturing/Expiry dates (where applicable)
   - Generic/Common names for products
   - Dimensions for relevant products
   - ISI/BIS/AGMARK marks (where mandatory)

2. E-COMMERCE PLATFORM RESPONSIBILITIES:
   - Due diligence on seller compliance
   - Product listing validation
   - Automated compliance checking systems
   - Seller onboarding compliance verification
   - Regular audit and monitoring
   - Consumer grievance handling
   - Legal Metrology officer coordination

3. AUTOMATED COMPLIANCE SYSTEMS:
   - OCR-based text extraction from product images
   - NLP processing for compliance validation
   - Rule engine for Legal Metrology verification
   - Bulk processing for large product catalogs
   - Real-time compliance scoring
   - Automated flagging of non-compliant listings
   - Integration with e-commerce platforms

4. PENALTIES & ENFORCEMENT:
   - Fines up to ₹25,000 for non-compliance
   - Product seizure and removal from platforms
   - Legal action against platforms and sellers
   - Consumer complaint mechanisms
   - Legal Metrology department enforcement

5. INDUSTRY-SPECIFIC REQUIREMENTS:
   - Food products: FSSAI compliance, nutritional info
   - Textiles: Fabric composition, care instructions
   - Electronics: Power consumption, warranty terms
   - Cosmetics: Ingredient listing, shelf life
   - Pharmaceuticals: Drug license, dosage info
   - Jewelry: Hallmarking, purity declarations

6. TECHNICAL IMPLEMENTATION:
   - API integration for compliance checking
   - Machine learning for pattern recognition
   - Computer vision for label analysis
   - Database management for compliance records
   - Reporting and analytics dashboards
   - Audit trail maintenance

RESPONSE GUIDELINES:
- Provide specific, actionable compliance guidance
- Reference exact Legal Metrology rules and sections
- Give practical implementation examples
- Suggest technical solutions for automation
- Include penalty information for violations
- Offer step-by-step compliance procedures
- Use emojis for better readability
- Maintain professional, authoritative tone

CURRENT CONTEXT: You're assisting with an Automated Legal Metrology Compliance Checker system for e-commerce platforms, helping users understand compliance requirements, validate product data, improve extraction quality, and implement automated compliance solutions."""
            }
        ]
        
        # Add conversation history
        for msg in self.conversation_history[-10:]:  # Last 10 messages for context
            if msg.type.value == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.type.value == "assistant":
                messages.append({"role": "assistant", "content": msg.content})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Add session context if available
        if self.session_context:
            context_info = f"\n\nCurrent session context: {safe_json_dumps(self.session_context, indent=2)}"
            messages[-1]["content"] += context_info
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        return response.choices[0].message.content.strip()
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Fallback response when OpenAI is unavailable"""
        # Analyze user intent
        intent = self._analyze_intent(user_input)
        
        if intent == "validation_help":
            return self._get_validation_guidance()
        elif intent == "extraction_help":
            return self._get_extraction_guidance()
        elif intent == "compliance_rules":
            return self._get_compliance_rules_info()
        elif intent == "general_help":
            return self._get_general_help()
        else:
            return self._get_general_response(user_input)
    
    def _analyze_intent(self, user_input: str) -> str:
        """Analyze user input to determine intent"""
        input_lower = user_input.lower()
        
        if any(keyword in input_lower for keyword in ['validation', 'validate', 'compliance', 'score']):
            return "validation_help"
        elif any(keyword in input_lower for keyword in ['extraction', 'extract', 'ocr', 'text']):
            return "extraction_help"
        elif any(keyword in input_lower for keyword in ['rules', 'regulation', 'legal', 'metrology']):
            return "compliance_rules"
        elif any(keyword in input_lower for keyword in ['help', 'how', 'what', 'guide']):
            return "general_help"
        else:
            return "general"
    
    def _get_validation_guidance(self) -> str:
        """Get validation-specific guidance for e-commerce compliance"""
        return """
🛒 **E-Commerce Compliance Validation Guidance:**

**E-COMMERCE LISTING STATUS:**
- 90-100%: ✅ APPROVED - Ready for marketplace listing
- 80-89%: ⚠️ CONDITIONAL - Minor fixes needed before listing
- 60-79%: 🔴 REJECTED - Major compliance issues, cannot list
- Below 60%: 🚨 BLOCKED - Serious violations, legal action risk

**CRITICAL E-COMMERCE COMPLIANCE ISSUES:**

**🏛️ Legal Metrology Act 2009 Violations:**
- **MRP Missing**: Mandatory under Rule 6 - ₹10,000-25,000 fine
- **Net Quantity Issues**: Must display with proper units (g, kg, ml, l) - Rule 8
- **Manufacturer Info**: Complete name & address required - Rule 7
- **Country of Origin**: Mandatory for imports - Rule 9

**🛒 E-Commerce Platform Requirements:**
- **Mobile Optimization**: 70% users shop on mobile
- **Search Visibility**: Compliant products rank higher
- **Consumer Trust**: Proper declarations build credibility
- **Platform Approval**: Non-compliant listings get removed

**📋 IMMEDIATE ACTION PLAN:**
1. **CRITICAL** (Red): Fix immediately - blocks listing
2. **WARNING** (Yellow): Address within 24 hours
3. **INFO** (Blue): Improve for better compliance score
4. **RE-VALIDATE**: Check improvements before listing
5. **PLATFORM UPLOAD**: Only after 80%+ compliance score

**⚖️ LEGAL CONSEQUENCES:**
- Fines: ₹10,000 to ₹25,000 per violation
- Product seizure from warehouses
- Marketplace account suspension
- Consumer complaint liability
        """
    
    def _get_extraction_guidance(self) -> str:
        """Get extraction-specific guidance for e-commerce"""
        return """
🔍 **E-Commerce Product Data Extraction Guidance:**

**🛒 E-COMMERCE EXTRACTION REQUIREMENTS:**
- **Mobile-First**: 70% users upload via mobile apps
- **Batch Processing**: Handle 1000+ products efficiently
- **Real-Time Validation**: Instant compliance feedback
- **Multi-Language**: Hindi, English, regional languages
- **Platform Integration**: API connectivity with marketplaces

**📱 MOBILE IMAGE OPTIMIZATION:**
- **Resolution**: Minimum 1080p, recommended 4K
- **Lighting**: Natural light or LED ring light
- **Stability**: Use tripod or stable surface
- **Focus**: Ensure text is sharp and readable
- **Angle**: Straight-on, 90-degree angle to label

**🤖 AUTOMATED EXTRACTION ACCURACY:**
- **95%+ MRP Detection**: Critical for pricing compliance
- **90%+ Net Quantity**: Essential for consumer protection  
- **85%+ Manufacturer**: Required for legal compliance
- **80%+ Country of Origin**: Import compliance necessity

**⚡ BULK PROCESSING OPTIMIZATION:**
- **Image Preprocessing**: Auto-crop, enhance contrast
- **OCR Engine Tuning**: Tesseract optimization for Indian text
- **NLP Enhancement**: Pattern recognition for Indian formats
- **Database Integration**: Real-time compliance scoring
- **API Rate Limiting**: Handle marketplace upload volumes

**🎯 CRITICAL EXTRACTION FIELDS:**
1. **MRP** (₹ symbol, price format validation)
2. **Net Quantity** (units: g, kg, ml, l, pieces)
3. **Manufacturer/Packer** (complete address required)
4. **Country of Origin** (especially for imports)
5. **Expiry/Manufacturing Date** (DD/MM/YYYY format)
6. **Generic Name** (product classification)
7. **Dimensions** (L×W×H for applicable products)

**🔧 TECHNICAL IMPLEMENTATION:**
- **Computer Vision**: Label boundary detection
- **Text Recognition**: Multi-font, multi-language OCR
- **Data Validation**: Format compliance checking
- **Machine Learning**: Pattern recognition training
- **Quality Assurance**: Confidence scoring algorithms
        """
    
    def _get_compliance_rules_info(self) -> str:
        """Get compliance rules information for e-commerce"""
        return """
⚖️ **Legal Metrology Rules for E-Commerce Platforms (India):**

**🏛️ LEGAL FRAMEWORK:**
- **Legal Metrology Act 2009**: Primary legislation
- **Legal Metrology (Packaged Commodities) Rules 2011**: Implementation rules
- **Consumer Protection Act 2019**: E-commerce specific provisions
- **Consumer Protection (E-commerce) Rules 2020**: Platform obligations

**📋 MANDATORY E-COMMERCE DECLARATIONS:**

**1. Maximum Retail Price (MRP) - Rule 6:**
- Must be prominently displayed on product listing
- Include currency symbol (₹)
- Cannot exceed declared MRP
- Penalty: ₹10,000 to ₹25,000

**2. Net Quantity Declaration - Rule 8:**
- Display with appropriate units (g, kg, ml, l, pieces)
- Must match actual product quantity
- Bilingual display (English + Hindi/Regional)
- Penalty: ₹10,000 to ₹25,000

**3. Manufacturer/Packer/Importer Details - Rule 7:**
- Complete name and address
- Contact information
- License numbers where applicable
- Penalty: ₹5,000 to ₹25,000

**4. Country of Origin - Rule 9:**
- Mandatory for imported products
- Clear declaration on listing
- Cannot be misleading
- Penalty: ₹10,000 to ₹25,000

**🛒 E-COMMERCE PLATFORM RESPONSIBILITIES:**

**1. Due Diligence (Section 79, IT Act):**
- Verify seller compliance before onboarding
- Regular audit of product listings
- Remove non-compliant products
- Maintain compliance records

**2. Consumer Grievance Mechanism:**
- 24x7 customer support
- Complaint resolution within 7 days
- Legal Metrology officer coordination
- Compensation for non-compliance

**3. Technology Requirements:**
- Automated compliance checking systems
- OCR-based validation tools
- Real-time compliance scoring
- Integration with Legal Metrology database

**⚠️ ENFORCEMENT & PENALTIES:**

**For Sellers:**
- First violation: ₹10,000 fine
- Repeat violation: ₹25,000 fine
- Product seizure and destruction
- Marketplace account suspension

**For Platforms:**
- Intermediary liability loss
- Platform blocking orders
- Criminal prosecution possible
- Consumer compensation liability

**🎯 COMPLIANCE BEST PRACTICES:**

**1. Automated Validation:**
- Pre-listing compliance checks
- Real-time validation during upload
- Bulk processing for existing catalogs
- AI-powered compliance scoring

**2. Seller Education:**
- Compliance training programs
- Documentation templates
- Regular updates on rule changes
- Penalty awareness campaigns

**3. Technology Integration:**
- API integration with Legal Metrology systems
- Machine learning for pattern recognition
- Computer vision for label analysis
- Blockchain for compliance audit trails

**📞 LEGAL METROLOGY CONTACTS:**
- National: legal-metrology@nic.in
- State Offices: Contact local Legal Metrology Department
- Consumer Helpline: 1800-11-4000
- E-commerce Grievances: Platform-specific mechanisms
        """
    
    def _get_general_help(self) -> str:
        """Get general help information"""
        return """
🤖 **Legal Metrology Compliance Assistant:**

I'm here to help you with compliance validation and extraction. Here's what I can assist with:

**📋 Validation Help:**
- Explain compliance scores and issues
- Suggest fixes for common problems
- Guide you through the validation process

**🔍 Extraction Help:**
- Improve image quality for better extraction
- Troubleshoot extraction issues
- Optimize text recognition

**⚖️ Compliance Rules:**
- Explain Legal Metrology requirements
- Identify common violations
- Provide regulatory guidance

**💡 General Tips:**
- Best practices for compliance
- Industry-specific requirements
- Documentation and reporting

Just ask me anything about compliance, validation, or extraction!
        """
    
    def _get_general_response(self, user_input: str) -> str:
        """Get general response for unrecognized input"""
        return f"""
I understand you're asking about: "{user_input}"

I'm specialized in Legal Metrology compliance assistance. I can help with:

- 🔍 **Validation Issues**: Understanding compliance scores and fixing problems
- 📊 **Extraction Problems**: Improving text recognition and image quality  
- ⚖️ **Compliance Rules**: Legal Metrology requirements and regulations
- 💡 **Best Practices**: Industry guidelines and recommendations

Could you rephrase your question focusing on one of these areas? I'll be happy to provide detailed assistance!
        """
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No conversation history available."
        
        user_messages = [msg for msg in self.conversation_history if msg.type == ChatMessageType.USER]
        assistant_messages = [msg for msg in self.conversation_history if msg.type == ChatMessageType.ASSISTANT]
        
        return f"""
📊 **Conversation Summary:**
- Total Messages: {len(self.conversation_history)}
- Your Questions: {len(user_messages)}
- My Responses: {len(assistant_messages)}
- Session Duration: {self._get_session_duration()}

**Topics Discussed:**
{self._get_topics_summary()}
        """
    
    def _get_session_duration(self) -> str:
        """Get session duration"""
        if not self.conversation_history:
            return "0 minutes"
        
        start_time = self.conversation_history[0].timestamp
        end_time = self.conversation_history[-1].timestamp
        duration = end_time - start_time
        
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"
    
    def _get_topics_summary(self) -> str:
        """Get summary of topics discussed"""
        topics = set()
        for msg in self.conversation_history:
            if msg.type == ChatMessageType.USER:
                intent = self._analyze_intent(msg.content)
                if intent == "validation_help":
                    topics.add("Validation & Compliance")
                elif intent == "extraction_help":
                    topics.add("Text Extraction & OCR")
                elif intent == "compliance_rules":
                    topics.add("Legal Metrology Rules")
                elif intent == "general_help":
                    topics.add("General Assistance")
        
        if not topics:
            return "- General conversation"
        
        return "\n".join(f"- {topic}" for topic in sorted(topics))


# Global chatbot instance
chatbot = ComplianceChatbot()