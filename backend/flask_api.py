"""Flask API for BharatVision - React Frontend Integration
Enhanced backend matching Streamlit features with real compliance checking
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
import sys
import json
from dataclasses import asdict
sys.path.insert(0, os.path.dirname(__file__))

from database import db
from crawler import EcommerceCrawler
from audit_logger import AuditLogger

# Try to import OCR integrator
try:
    from ocr_integration import get_ocr_integrator
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    def get_ocr_integrator():
        return None

# Configuration
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

# Initialize crawler (robust instantiation)
try:
    crawler = EcommerceCrawler()
except TypeError as e:
    # Fallback for older/newer signatures
    try:
        crawler = EcommerceCrawler(base_url='https://www.amazon.in', platform='amazon', product_extractor=None)
    except Exception:
        crawler = None

# Initialize OCR if available
ocr_integrator = get_ocr_integrator() if OCR_AVAILABLE else None


# ==================== COMPLIANCE CHECKING ENGINE ====================

def calculate_compliance(product) -> dict:
    """
    Calculate Legal Metrology compliance score for a product
    Matching Streamlit's compliance checking logic exactly
    """
    checks = {}
    
    # Get product attributes safely
    title = getattr(product, 'title', '') or product.get('title', '') if isinstance(product, dict) else (product.title if hasattr(product, 'title') else '')
    brand = getattr(product, 'brand', None) or product.get('brand') if isinstance(product, dict) else (product.brand if hasattr(product, 'brand') else None)
    category = getattr(product, 'category', None) or product.get('category') if isinstance(product, dict) else (product.category if hasattr(product, 'category') else None)
    price = getattr(product, 'price', None) or product.get('price') if isinstance(product, dict) else (product.price if hasattr(product, 'price') else None)
    mrp = getattr(product, 'mrp', None) or product.get('mrp') if isinstance(product, dict) else (product.mrp if hasattr(product, 'mrp') else None)
    description = getattr(product, 'description', '') or product.get('description', '') if isinstance(product, dict) else (product.description if hasattr(product, 'description') else '')
    image_urls = getattr(product, 'image_urls', []) or product.get('image_urls', []) if isinstance(product, dict) else (product.image_urls if hasattr(product, 'image_urls') else [])
    manufacturer = getattr(product, 'manufacturer', None) or product.get('manufacturer') if isinstance(product, dict) else (product.manufacturer if hasattr(product, 'manufacturer') else None)
    country_of_origin = getattr(product, 'country_of_origin', None) or product.get('country_of_origin') if isinstance(product, dict) else (product.country_of_origin if hasattr(product, 'country_of_origin') else None)
    expiry_date = getattr(product, 'expiry_date', None) or product.get('expiry_date') if isinstance(product, dict) else (product.expiry_date if hasattr(product, 'expiry_date') else None)
    
    description_lower = (description or '').lower()
    
    # 1. Product Identification
    checks["Product Title"] = len(title or '') > 5
    checks["Brand/Manufacturer"] = bool(brand)
    checks["Product Category"] = bool(category)
    
    # 2. Pricing Information
    checks["Price/MRP Display"] = bool(price)
    has_mrp_info = 'mrp' in description_lower
    checks["MRP Information"] = has_mrp_info or bool(mrp)
    
    # 3. Quantity Information
    has_quantity = any(word in description_lower for word in ['kg', 'gm', 'ml', 'litre', 'liter', 'qty', 'quantity', 'weight', 'volume', 'pack'])
    checks["Net Quantity"] = has_quantity
    
    # 4. Visual Content
    checks["Product Image(s)"] = bool(image_urls and len(image_urls) > 0)
    checks["Clear Description"] = len(description or '') > 30
    
    # 5. Manufacturing Info
    has_mfg_info = any(word in description_lower for word in ['made', 'manufactured', 'product of', 'country', 'origin'])
    checks["Manufacturing Info"] = has_mfg_info or bool(manufacturer) or bool(country_of_origin)
    
    # 6. Expiry/Validity
    has_expiry = any(word in description_lower for word in ['expires', 'expiry', 'best before', 'use by', 'mfg date', 'manufacturing date'])
    checks["Expiry/Validity Info"] = has_expiry or bool(expiry_date)
    
    # 7. Legal Markings
    has_legal_marks = any(mark in description_lower for mark in ['isi', 'agmark', 'fssai', 'standard', 'bis', 'hallmark'])
    checks["Legal Certifications"] = has_legal_marks
    
    # Calculate score
    compliant_count = sum(1 for v in checks.values() if v)
    total_checks = len(checks)
    score = (compliant_count / total_checks * 100) if total_checks > 0 else 0
    
    # Determine status
    if score >= 85:
        status = "COMPLIANT"
    elif score >= 65:
        status = "PARTIAL"
    else:
        status = "NON-COMPLIANT"
    
    return {
        'score': round(score, 1),
        'status': status,
        'checks': checks,
        'compliant_count': compliant_count,
        'total_checks': total_checks
    }

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

# ==================== VALIDATION ENDPOINTS ====================

@app.route('/api/validate', methods=['POST'])
def validate_image():
    """
    Validate product image for compliance
    Expected: multipart/form-data with 'image' field
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(filepath)
        
        logger.info(f"Image uploaded and saved to {filepath}")
        
        # Perform validation (placeholder - integrate with actual OCR/validation logic)
        validation_result = perform_validation(filepath)
        
        # Save to database
        result_id = db.save_validation_result({
            'product_name': validation_result.get('product_name', 'Unknown'),
            'status': validation_result.get('status'),
            'compliance_score': validation_result.get('compliance_score', 0),
            'present_items': validation_result.get('present_items', {}),
            'missing_items': validation_result.get('missing_items', {}),
            'flagged_items': validation_result.get('flagged_items', {}),
            'ocr_text': validation_result.get('ocr_text', ''),
            'image_path': filepath
        })
        
        logger.info(f"Validation result saved with ID: {result_id}")
        
        # Log audit
        audit_logger.log_validation(result_id, filepath, validation_result.get('status'))
        
        return jsonify({
            'id': result_id,
            'status': 'success',
            'data': validation_result,
            'message': 'Image validation completed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<int:result_id>', methods=['GET'])
def get_result(result_id):
    """Get validation result by ID"""
    try:
        result = db.get_validation_result(result_id)
        if not result:
            return jsonify({'error': 'Result not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
    except Exception as e:
        logger.error(f"Error fetching result: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET'])
def get_all_results():
    """Get all validation results with pagination"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        results = db.get_all_validation_results(limit, offset)
        stats = db.get_statistics()
        
        return jsonify({
            'status': 'success',
            'data': results,
            'statistics': stats,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': stats['total_validations']
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<int:result_id>', methods=['DELETE'])
def delete_result(result_id):
    """Delete validation result"""
    try:
        db.delete_validation_result(result_id)
        return jsonify({'status': 'success', 'message': 'Result deleted'}), 200
    except Exception as e:
        logger.error(f"Error deleting result: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== STATISTICS ENDPOINTS ====================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get validation statistics"""
    try:
        stats = db.get_statistics()
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== COMPLIANCE ENDPOINTS ====================

@app.route('/api/compliance-rules', methods=['GET'])
def get_compliance_rules():
    """Get legal metrology compliance rules"""
    rules = {
        'mandatory_fields': [
            {'name': 'Product Name', 'description': 'Clear and legible product name'},
            {'name': 'Net Quantity', 'description': 'Weight/Volume in metric units'},
            {'name': 'Maximum Retail Price (MRP)', 'description': 'MRP in both languages'},
            {'name': 'Manufacturing Date', 'description': 'Date of manufacture'},
            {'name': 'Best Before Date', 'description': 'Expiry/Best before date'},
            {'name': 'Manufacturer Details', 'description': 'Name and address'},
            {'name': 'Batch/Lot Number', 'description': 'For traceability'},
            {'name': 'Nutritional Information', 'description': 'Per 100g serving'}
        ],
        'font_requirements': [
            {'item': 'Quantity Declaration', 'minimum_height': '2mm'},
            {'item': 'MRP', 'minimum_height': '2mm'},
            {'item': 'Ingredients', 'minimum_height': '1mm'},
            {'item': 'Date', 'minimum_height': '1.5mm'}
        ],
        'language_requirements': [
            {'requirement': 'Bilingual (English + Hindi)'},
            {'requirement': 'Clear and legible'},
            {'requirement': 'In horizontal format (preferably)'},
            {'requirement': 'Contrasting colors'}
        ],
        'prohibited_claims': [
            'Pure',
            'Natural',
            'Healthy',
            'Fresh',
            'Traditional'
        ]
    }
    
    return jsonify({
        'status': 'success',
        'data': rules
    }), 200

# ==================== SEARCH/CRAWLER ENDPOINTS ====================

@app.route('/api/search-products', methods=['POST'])
def search_products():
    """
    Search for products from e-commerce sites with full compliance checking
    Matches Streamlit Web_Crawler.py functionality
    """
    try:
        data = request.get_json()
        query = data.get('query')
        platform = data.get('platform', 'amazon')
        max_results = data.get('max_results', 20)
        enable_ocr = data.get('enable_ocr', False)
        enable_compliance = data.get('enable_compliance', True)
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        logger.info(f"Searching '{query}' on {platform} (max: {max_results})")
        
        # Perform actual crawling
        products = crawler.search_products(query, platform, max_results)
        
        results_list = []
        compliance_summary = {
            'total': 0,
            'compliant': 0,
            'partial': 0,
            'non_compliant': 0,
            'avg_score': 0
        }
        
        total_score = 0
        
        for product in products:
            # Convert ProductData to dict
            if hasattr(product, '__dataclass_fields__'):
                product_dict = asdict(product)
            else:
                product_dict = product if isinstance(product, dict) else {}
            
            # Calculate compliance for each product
            if enable_compliance:
                compliance = calculate_compliance(product)
                product_dict['compliance'] = compliance
                
                # Update summary
                compliance_summary['total'] += 1
                total_score += compliance['score']
                
                if compliance['status'] == 'COMPLIANT':
                    compliance_summary['compliant'] += 1
                elif compliance['status'] == 'PARTIAL':
                    compliance_summary['partial'] += 1
                else:
                    compliance_summary['non_compliant'] += 1
                
                # Save to database
                try:
                    db.save_compliance_check(
                        user_id=1,
                        username='api_user',
                        product_title=product_dict.get('title', 'Unknown'),
                        platform=platform,
                        score=compliance['score'],
                        status=compliance['status'],
                        details=json.dumps(compliance['checks'])
                    )
                except Exception as db_err:
                    logger.warning(f"Could not save to DB: {db_err}")
            
            # OCR processing if enabled
            if enable_ocr and OCR_AVAILABLE and ocr_integrator:
                image_urls = product_dict.get('image_urls', [])
                if image_urls and len(image_urls) > 0:
                    try:
                        ocr_result = ocr_integrator.extract_text_from_image_url(image_urls[0])
                        if ocr_result:
                            product_dict['ocr_text'] = ocr_result.get('text', '')[:500]
                    except Exception as e:
                        logger.warning(f"OCR error: {e}")
            
            results_list.append(product_dict)
        
        # Calculate average score
        if compliance_summary['total'] > 0:
            compliance_summary['avg_score'] = round(total_score / compliance_summary['total'], 1)
        
        return jsonify({
            'status': 'success',
            'data': results_list,
            'count': len(results_list),
            'compliance_summary': compliance_summary,
            'query': query,
            'platform': platform
        }), 200
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-from-url', methods=['POST'])
def extract_from_url():
    """
    Extract product details from URL with full compliance checking
    """
    try:
        data = request.get_json()
        url = data.get('url')
        enable_ocr = data.get('enable_ocr', False)
        download_images = data.get('download_images', False)
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        logger.info(f"Extracting product from URL: {url}")
        
        # Extract product
        product = crawler.extract_product_from_url(url)
        
        if not product:
            return jsonify({'error': 'Could not extract product from URL'}), 404
        
        # Convert to dict
        if hasattr(product, '__dataclass_fields__'):
            product_dict = asdict(product)
        else:
            product_dict = product if isinstance(product, dict) else {}
        
        # Calculate compliance
        compliance = calculate_compliance(product)
        product_dict['compliance'] = compliance
        
        # Save to database
        try:
            db.save_compliance_check(
                user_id=1,
                username='api_user',
                product_title=product_dict.get('title', 'Unknown'),
                platform=product_dict.get('platform', 'unknown'),
                score=compliance['score'],
                status=compliance['status'],
                details=json.dumps(compliance['checks'])
            )
        except Exception as db_err:
            logger.warning(f"Could not save to DB: {db_err}")
        
        # OCR processing if enabled
        if enable_ocr and OCR_AVAILABLE and ocr_integrator:
            image_urls = product_dict.get('image_urls', [])
            if image_urls and len(image_urls) > 0:
                try:
                    ocr_result = ocr_integrator.extract_text_from_image_url(image_urls[0])
                    if ocr_result:
                        product_dict['ocr_text'] = ocr_result.get('text', '')[:500]
                except Exception as e:
                    logger.warning(f"OCR error: {e}")
        
        return jsonify({
            'status': 'success',
            'data': product_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Extract error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/supported-platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported e-commerce platforms"""
    try:
        platforms = crawler.get_supported_platforms()
        return jsonify({
            'status': 'success',
            'data': platforms
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compliance-history', methods=['GET'])
def get_compliance_history():
    """Get compliance check history from database"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = db.get_compliance_history(limit)
        return jsonify({
            'status': 'success',
            'data': history
        }), 200
    except Exception as e:
        logger.error(f"Error getting compliance history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/platform-analytics', methods=['GET'])
def get_platform_analytics():
    """Get analytics data per platform for charts"""
    try:
        analytics = db.get_platform_analytics()
        return jsonify({
            'status': 'success',
            'data': analytics
        }), 200
    except Exception as e:
        logger.error(f"Error getting platform analytics: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

def perform_validation(image_path: str) -> dict:
    """
    Perform validation on product image
    This is a placeholder - integrate with actual OCR and validation logic
    """
    validation_result = {
        'product_name': 'Sample Product',
        'status': 'non-compliant',
        'compliance_score': 72,
        'present_items': {
            'Product Name': 'Aloo Bhujia',
            'Net Quantity': '200g',
            'MRP': '₹50',
            'Manufacturing Date': '15/11/2024'
        },
        'missing_items': {
            'Best Before Date': 'Not visible',
            'Batch Number': 'Text too small',
            'Nutritional Information': 'Missing'
        },
        'flagged_items': {
            'Font Size': 'Text below 2mm minimum',
            'Language': 'Missing Hindi translation'
        },
        'ocr_text': 'Sample OCR extracted text from product packaging'
    }
    
    return validation_result

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    print("Starting BharatVision Flask API...")
    print("API available at http://localhost:5000")
    print("React frontend should be running at http://localhost:3000")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
