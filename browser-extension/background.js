// BharatVision Browser Extension - Background Script
// Handles API communication

const API_URL = 'http://localhost:8001/api/v1';
let API_KEY = 'demo_key_12345';

// Load API key from storage
chrome.storage.sync.get(['apiKey'], (result) => {
    if (result.apiKey) {
        API_KEY = result.apiKey;
    }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'validateProduct') {
        validateProduct(request.data)
            .then(result => sendResponse({ success: true, result }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // Keep channel open for async response
    }
});

// Validate product via API
async function validateProduct(productData) {
    try {
        const response = await fetch(`${API_URL}/validate/product`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify(productData)
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Validation error:', error);
        throw error;
    }
}

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
    chrome.tabs.sendMessage(tab.id, { action: 'checkCompliance' });
});
