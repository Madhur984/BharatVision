// BharatVision Browser Extension - Content Script
// Extracts product data from e-commerce pages

(function () {
    'use strict';

    // Platform-specific extractors
    const extractors = {
        amazon: extractAmazonData,
        flipkart: extractFlipkartData,
        meesho: extractMeeshoData,
        jiomart: extractJioMartData,
        myntra: extractMyntraData,
        shopify: extractShopifyData,
        woocommerce: extractWooCommerceData,
        generic: extractGenericData  // Fallback for all other platforms
    };

    // Detect platform
    function detectPlatform() {
        const hostname = window.location.hostname;
        if (hostname.includes('amazon')) return 'amazon';
        if (hostname.includes('flipkart')) return 'flipkart';
        if (hostname.includes('meesho')) return 'meesho';
        if (hostname.includes('jiomart')) return 'jiomart';
        if (hostname.includes('myntra')) return 'myntra';
        if (hostname.includes('shopify')) return 'shopify';
        if (hostname.includes('woocommerce') || hostname.includes('wp-admin')) return 'woocommerce';
        return 'generic';  // Use generic extractor for unknown platforms
    }

    // Generic extractor - works on any e-commerce site
    function extractGenericData() {
        // Try to find common product elements
        const productData = {
            platform: 'generic',
            generic_name: null,
            mrp: null,
            manufacturer_details: null,
            net_quantity: null,
            image_url: null
        };

        // Try common selectors for product title
        const titleSelectors = [
            'h1[class*="title"]', 'h1[class*="product"]', 'h1[class*="name"]',
            '[class*="product-title"]', '[class*="product-name"]',
            '[itemprop="name"]', 'h1'
        ];
        for (const selector of titleSelectors) {
            const elem = document.querySelector(selector);
            if (elem && elem.textContent.trim()) {
                productData.generic_name = elem.textContent.trim();
                break;
            }
        }

        // Try common selectors for price
        const priceSelectors = [
            '[class*="price"]', '[class*="mrp"]', '[class*="cost"]',
            '[itemprop="price"]', '[data-price]'
        ];
        for (const selector of priceSelectors) {
            const elem = document.querySelector(selector);
            if (elem && elem.textContent.trim()) {
                productData.mrp = elem.textContent.trim();
                break;
            }
        }

        // Try to find product image
        const imageSelectors = [
            '[class*="product-image"] img', '[class*="main-image"]',
            '[itemprop="image"]', 'img[class*="product"]'
        ];
        for (const selector of imageSelectors) {
            const elem = document.querySelector(selector);
            if (elem && elem.src) {
                productData.image_url = elem.src;
                break;
            }
        }

        return productData;
    }

    // Shopify extractor
    function extractShopifyData() {
        return {
            platform: 'shopify',
            generic_name: document.querySelector('.product-single__title')?.textContent.trim() ||
                document.querySelector('h1[class*="product"]')?.textContent.trim(),
            mrp: document.querySelector('.product-single__price')?.textContent.trim() ||
                document.querySelector('[class*="price"]')?.textContent.trim(),
            manufacturer_details: document.querySelector('.product-single__vendor')?.textContent.trim(),
            image_url: document.querySelector('.product-single__photo img')?.src ||
                document.querySelector('[class*="product-image"] img')?.src
        };
    }

    // WooCommerce extractor
    function extractWooCommerceData() {
        return {
            platform: 'woocommerce',
            generic_name: document.querySelector('.product_title')?.textContent.trim(),
            mrp: document.querySelector('.woocommerce-Price-amount')?.textContent.trim(),
            manufacturer_details: extractFromTable('Brand') || extractFromTable('Manufacturer'),
            net_quantity: extractFromTable('Weight') || extractFromTable('Net Quantity'),
            image_url: document.querySelector('.woocommerce-product-gallery__image img')?.src
        };
    }

    // Extract data from Amazon
    function extractAmazonData() {
        return {
            platform: 'amazon',
            generic_name: document.querySelector('#productTitle')?.textContent.trim(),
            mrp: document.querySelector('.a-price-whole')?.textContent.trim(),
            manufacturer_details: document.querySelector('#bylineInfo')?.textContent.trim(),
            net_quantity: extractFromTable('Net Quantity'),
            country_of_origin: extractFromTable('Country of Origin'),
            image_url: document.querySelector('#landingImage')?.src
        };
    }

    // Extract data from Flipkart
    function extractFlipkartData() {
        return {
            platform: 'flipkart',
            generic_name: document.querySelector('.B_NuCI')?.textContent.trim(),
            mrp: document.querySelector('._30jeq3')?.textContent.trim(),
            manufacturer_details: extractFromSpecs('Manufacturer'),
            net_quantity: extractFromSpecs('Net Quantity'),
            country_of_origin: extractFromSpecs('Country of Origin'),
            image_url: document.querySelector('._396cs4')?.src
        };
    }

    // Extract data from Meesho
    function extractMeeshoData() {
        return {
            platform: 'meesho',
            generic_name: document.querySelector('[data-testid="product-title"]')?.textContent.trim(),
            mrp: document.querySelector('[data-testid="product-price"]')?.textContent.trim(),
            image_url: document.querySelector('[data-testid="product-image"]')?.src
        };
    }

    // Extract data from JioMart
    function extractJioMartData() {
        return {
            platform: 'jiomart',
            generic_name: document.querySelector('.pdp-title')?.textContent.trim(),
            mrp: document.querySelector('.jm-heading-xxs')?.textContent.trim(),
            net_quantity: extractFromDetails('Net Quantity'),
            image_url: document.querySelector('.product-img')?.src
        };
    }

    // Extract data from Myntra
    function extractMyntraData() {
        return {
            platform: 'myntra',
            generic_name: document.querySelector('.pdp-title')?.textContent.trim(),
            mrp: document.querySelector('.pdp-mrp')?.textContent.trim(),
            manufacturer_details: extractFromDetails('Manufacturer'),
            image_url: document.querySelector('.image-grid-image')?.src
        };
    }

    // Helper: Extract from product table
    function extractFromTable(label) {
        const rows = document.querySelectorAll('tr');
        for (const row of rows) {
            if (row.textContent.includes(label)) {
                return row.querySelector('td:last-child')?.textContent.trim();
            }
        }
        return null;
    }

    // Helper: Extract from specifications
    function extractFromSpecs(label) {
        const specs = document.querySelectorAll('._1hKmbr');
        for (const spec of specs) {
            if (spec.textContent.includes(label)) {
                return spec.nextElementSibling?.textContent.trim();
            }
        }
        return null;
    }

    // Helper: Extract from details section
    function extractFromDetails(label) {
        const details = document.querySelectorAll('.index-tableContainer');
        for (const detail of details) {
            if (detail.textContent.includes(label)) {
                return detail.querySelector('.index-tableValue')?.textContent.trim();
            }
        }
        return null;
    }

    // Add "Check Compliance" button
    function addComplianceButton() {
        const platform = detectPlatform();
        if (!platform) return;

        // Create button
        const button = document.createElement('button');
        button.id = 'bharatvision-check-btn';
        button.textContent = '✓ Check Compliance';
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        `;

        button.onmouseover = () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
        };

        button.onmouseout = () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
        };

        button.onclick = async () => {
            button.textContent = '⏳ Checking...';
            button.disabled = true;

            const productData = extractors[platform]();

            // Send to background script for API call
            chrome.runtime.sendMessage({
                action: 'validateProduct',
                data: productData
            }, (response) => {
                button.textContent = '✓ Check Compliance';
                button.disabled = false;

                if (response.success) {
                    showResults(response.result);
                } else {
                    showError(response.error);
                }
            });
        };

        document.body.appendChild(button);
    }

    // Show validation results
    function showResults(result) {
        const modal = document.createElement('div');
        modal.id = 'bharatvision-modal';
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 10001;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 90%;
        `;

        const status = result.overall_status === 'COMPLIANT' ? '✅ COMPLIANT' : '❌ VIOLATIONS FOUND';
        const statusColor = result.overall_status === 'COMPLIANT' ? '#10b981' : '#ef4444';

        modal.innerHTML = `
            <h2 style="margin: 0 0 20px 0; color: ${statusColor};">${status}</h2>
            <p style="margin: 10px 0;"><strong>Total Rules:</strong> ${result.total_rules}</p>
            <p style="margin: 10px 0;"><strong>Violations:</strong> ${result.violations_count}</p>
            ${result.violations.length > 0 ? `
                <div style="margin-top: 20px;">
                    <h3 style="margin: 0 0 10px 0;">Issues Found:</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        ${result.violations.map(v => `<li style="margin: 5px 0;">${v.description}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            <button id="close-modal" style="
                margin-top: 20px;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
            ">Close</button>
        `;

        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(modal);

        document.getElementById('close-modal').onclick = () => {
            modal.remove();
            overlay.remove();
        };

        overlay.onclick = () => {
            modal.remove();
            overlay.remove();
        };
    }

    // Show error message
    function showError(error) {
        alert(`Error: ${error}`);
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addComplianceButton);
    } else {
        addComplianceButton();
    }
})();
