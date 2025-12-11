"""
PackNetra Backend Server - Flask API
Integrates with the frontend and provides all necessary endpoints
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Try to import existing backend modules
try:
    from backend.database import db
    from backend.crawler import WebCrawler
    from backend.audit_logger import AuditLogger
    from backend.ocr_integration import OCRIntegration
except ImportError:
    print("Warning: Some backend modules not available. Using mock implementations.")

# ==================== APP INITIALIZATION ====================

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MOCK DATA FOR TESTING ====================

MOCK_PRODUCTS = [
    {"id": 1, "name": "Soap 100g", "brand": "Brand A", "category": "Cosmetics", "compliant": False},
    {"id": 2, "name": "Oil 500ml", "brand": "Brand B", "category": "Food", "compliant": True},
    {"id": 3, "name": "Tea 250g", "brand": "Brand C", "category": "Food", "compliant": True},
    {"id": 4, "name": "Detergent 1kg", "brand": "Brand D", "category": "Chemicals", "compliant": False},
]

MOCK_DEVICES = [
    {"id": 1, "name": "PackNetra-01", "location": "Delhi, India", "online": True, "lastSync": "2 minutes ago", "scansToday": 124},
    {"id": 2, "name": "PackNetra-02", "location": "Mumbai, India", "online": True, "lastSync": "5 minutes ago", "scansToday": 98},
    {"id": 3, "name": "PackNetra-03", "location": "Bangalore, India", "online": False, "lastSync": "30 minutes ago", "scansToday": 0},
]

MOCK_VIOLATIONS = [
    {"state": "Maharashtra", "count": 830, "percentage": 85, "trend": "↑ 12%"},
    {"state": "Uttar Pradesh", "count": 580, "percentage": 65, "trend": "↑ 8%"},
    {"state": "Karnataka", "count": 600, "percentage": 68, "trend": "↑ 5%"},
    {"state": "Tamil Nadu", "count": 520, "percentage": 58, "trend": "↓ 3%"},
    {"state": "Delhi", "count": 315, "percentage": 35, "trend": "↑ 2%"},
]

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'PackNetra Backend'
    }), 200

# ==================== STATISTICS ENDPOINTS ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    return jsonify({
        'totalScans': 12840,
        'complianceRate': 88.5,
        'violations': 1456,
        'activeDevices': 3,
        'trend': {
            'scans': 8.6,
            'compliance': -2.1,
            'violations': 12.0
        }
    }), 200

# ==================== PRODUCTS ENDPOINTS ====================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    return jsonify(MOCK_PRODUCTS), 200

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product"""
    product = next((p for p in MOCK_PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product), 200

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create new product"""
    data = request.json
    new_product = {
        'id': max([p['id'] for p in MOCK_PRODUCTS]) + 1,
        'name': data.get('name'),
        'brand': data.get('brand'),
        'category': data.get('category'),
        'compliant': True
    }
    MOCK_PRODUCTS.append(new_product)
    return jsonify(new_product), 201

# ==================== VALIDATION/SCANNING ENDPOINTS ====================

@app.route('/api/validate', methods=['POST'])
def validate_image():
    """
    Validate product image for compliance
    Expected: multipart/form-data with 'image' field
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Mock validation result
    result = {
        'filename': filename,
        'timestamp': datetime.now().isoformat(),
        'compliant': True,
        'confidence': 92,
        'details': 'Product labeling meets all compliance requirements',
        'violations': [],
        'metadata': {
            'brand': 'Sample Brand',
            'category': 'Food',
            'mrp': 'Present',
            'quantity': 'Present',
            'date': 'Present'
        }
    }

    logger.info(f"Validated image: {filename}")
    return jsonify(result), 200

@app.route('/api/batch-process', methods=['POST'])
def batch_process():
    """Process multiple images"""
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400

    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No files selected'}), 400

    results = []
    compliant_count = 0

    for file in files:
        if file.filename == '':
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Mock validation
        is_compliant = len(filename) % 2 == 0
        if is_compliant:
            compliant_count += 1

        results.append({
            'filename': filename,
            'compliant': is_compliant,
            'confidence': 85 + (id(filename) % 15),
            'details': 'Compliant' if is_compliant else 'Missing MRP'
        })

    return jsonify({
        'total': len(results),
        'compliant': compliant_count,
        'violations': len(results) - compliant_count,
        'items': results,
        'timestamp': datetime.now().isoformat()
    }), 200

# ==================== VIOLATIONS ENDPOINTS ====================

@app.route('/api/violations', methods=['GET'])
def get_violations():
    """Get violations data"""
    return jsonify(MOCK_VIOLATIONS), 200

@app.route('/api/violations/heatmap', methods=['GET'])
def get_violations_heatmap():
    """Get state-wise violations heatmap"""
    return jsonify({
        'states': MOCK_VIOLATIONS,
        'lastUpdated': datetime.now().isoformat(),
        'period': 'Last 30 days'
    }), 200

# ==================== DEVICES ENDPOINTS ====================

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all devices"""
    return jsonify(MOCK_DEVICES), 200

@app.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device"""
    device = next((d for d in MOCK_DEVICES if d['id'] == device_id), None)
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    return jsonify(device), 200

@app.route('/api/devices/<int:device_id>/status', methods=['GET'])
def get_device_status(device_id):
    """Get device status"""
    device = next((d for d in MOCK_DEVICES if d['id'] == device_id), None)
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    return jsonify({
        'id': device['id'],
        'name': device['name'],
        'online': device['online'],
        'lastSync': device['lastSync'],
        'cpuUsage': 45.2,
        'memoryUsage': 62.8,
        'storageUsage': 78.5,
        'temperature': 38.2,
        'uptime': '12 days 4 hours'
    }), 200

# ==================== SEARCH ENDPOINTS ====================

@app.route('/api/search', methods=['GET'])
def search_products():
    """Search products"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([]), 200

    results = [p for p in MOCK_PRODUCTS 
               if query in p['name'].lower() or query in p['brand'].lower()]
    return jsonify(results), 200

# ==================== USER DASHBOARD ENDPOINTS ====================

@app.route('/api/user/dashboard', methods=['GET'])
def user_dashboard():
    """Get user dashboard data"""
    token = request.headers.get('Authorization', '')
    
    return jsonify({
        'username': 'demo_user',
        'email': 'user@example.com',
        'role': 'Inspector',
        'totalScans': 2450,
        'complianceRate': 91.2,
        'recentScans': [
            {'product': 'Soap 100g', 'brand': 'Brand A', 'status': 'Violation', 'confidence': 72},
            {'product': 'Oil 500ml', 'brand': 'Brand B', 'status': 'Compliant', 'confidence': 95},
        ]
    }), 200

# ==================== ADMIN DASHBOARD ENDPOINTS ====================

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Get admin dashboard data"""
    token = request.headers.get('Authorization', '')
    
    return jsonify({
        'totalUsers': 156,
        'totalDevices': 24,
        'totalScans': 42580,
        'systemHealth': 98.5,
        'activeUsers': 45,
        'recentActivity': [
            {'user': 'inspector1', 'action': 'scan_completed', 'timestamp': datetime.now().isoformat()},
            {'user': 'inspector2', 'action': 'batch_process', 'timestamp': datetime.now().isoformat()},
        ]
    }), 200

# ==================== EXPORT ENDPOINTS ====================

@app.route('/api/export', methods=['GET'])
def export_data():
    """Export data in various formats"""
    format_type = request.args.get('format', 'csv')

    if format_type == 'csv':
        data = "Product Name,Brand,Category,Compliant\n"
        for product in MOCK_PRODUCTS:
            data += f"{product['name']},{product['brand']},{product['category']},{product['compliant']}\n"
        filename = 'products.csv'
        mimetype = 'text/csv'
    elif format_type == 'json':
        data = json.dumps(MOCK_PRODUCTS, indent=2)
        filename = 'products.json'
        mimetype = 'application/json'
    else:
        return jsonify({'error': 'Invalid format'}), 400

    # Create temporary file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'w') as f:
        f.write(data)

    return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=filename), 200

# ==================== ANALYTICS ENDPOINTS ====================

@app.route('/api/analytics/compliance-trend', methods=['GET'])
def compliance_trend():
    """Get compliance trend data"""
    return jsonify({
        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
        'data': [82, 84, 85, 86, 87, 88.5],
        'period': 'Last 6 weeks'
    }), 200

@app.route('/api/analytics/category-distribution', methods=['GET'])
def category_distribution():
    """Get category distribution"""
    return jsonify({
        'labels': ['Food', 'Cosmetics', 'Pharma', 'Chemicals'],
        'data': [40, 30, 20, 10]
    }), 200

# ==================== SETTINGS ENDPOINTS ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get user settings"""
    return jsonify({
        'sensitivity': 'medium',
        'notifications': True,
        'theme': 'light',
        'language': 'en'
    }), 200

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save user settings"""
    settings = request.json
    logger.info(f"Settings saved: {settings}")
    return jsonify({'message': 'Settings saved successfully', 'settings': settings}), 200

# ==================== WEB CRAWLER ENDPOINTS ====================

@app.route('/api/crawler/start', methods=['POST'])
def start_crawler():
    """Start web crawler"""
    data = request.json
    logger.info(f"Starting crawler with config: {data}")
    
    return jsonify({
        'status': 'started',
        'crawlerId': 'crawler_' + str(int(datetime.now().timestamp())),
        'message': 'Web crawler started successfully'
    }), 201

@app.route('/api/crawler/<crawler_id>/status', methods=['GET'])
def crawler_status(crawler_id):
    """Get crawler status"""
    return jsonify({
        'crawlerId': crawler_id,
        'status': 'running',
        'progress': 65,
        'itemsProcessed': 234,
        'itemsFound': 156,
        'startTime': datetime.now().isoformat(),
        'estimatedTimeRemaining': '15 minutes'
    }), 200

@app.route('/api/crawler/<crawler_id>/results', methods=['GET'])
def crawler_results(crawler_id):
    """Get crawler results"""
    return jsonify({
        'crawlerId': crawler_id,
        'totalResults': 156,
        'compliant': 138,
        'violations': 18,
        'items': [
            {'url': 'https://example.com/product1', 'status': 'compliant', 'details': 'All requirements met'},
            {'url': 'https://example.com/product2', 'status': 'violation', 'details': 'Missing MRP'},
        ]
    }), 200

# ==================== ERROR HANDLING ====================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'The requested resource was not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

# ==================== MIDDLEWARE ====================

@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}")

@app.after_request
def add_headers(response):
    response.headers['X-API-Version'] = '1.0.0'
    response.headers['X-Powered-By'] = 'PackNetra'
    return response

# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info("Starting BharatVision Backend Server...")
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        threaded=True
    )
