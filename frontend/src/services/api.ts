import axios from 'axios';
import type {
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    ProductSearchResponse,
    Stats,
    RecentScan,
    OCRResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const api = {
    // Health check
    healthCheck: async () => {
        const response = await apiClient.get('/api/health');
        return response.data;
    },

    // Get products from e-commerce platforms
    searchProducts: async (
        query: string,
        platform: string = 'amazon',
        limit: number = 10
    ): Promise<ProductSearchResponse> => {
        const response = await apiClient.get('/api/crawler/products', {
            params: { query, platform, limit },
        });
        return response.data;
    },

    // Check product compliance
    checkCompliance: async (
        request: ComplianceCheckRequest
    ): Promise<ComplianceCheckResponse> => {
        const response = await apiClient.post('/api/compliance/check', request);
        return response.data;
    },

    // Upload and analyze image
    uploadImage: async (file: File): Promise<OCRResult> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/api/upload-image', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Get statistics
    getStats: async (): Promise<Stats> => {
        const response = await apiClient.get('/api/stats');
        return response.data;
    },

    // Get recent scans
    getRecentScans: async (): Promise<RecentScan[]> => {
        const response = await apiClient.get('/api/recent-scans');
        return response.data;
    },
};

export default api;
