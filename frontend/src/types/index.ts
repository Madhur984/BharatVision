// TypeScript types for BharatVision API

export interface Product {
    id: number;
    title: string;
    brand: string;
    price: number;
    mrp: number;
    image: string;
    category: string;
}

export interface ComplianceCheckRequest {
    title: string;
    brand: string;
    price: number;
    mrp: number;
    image?: string;
    category?: string;
    description?: string;
}

export interface ComplianceCheckResponse {
    score: number;
    status: 'Compliant' | 'Partial' | 'Non-Compliant';
    color: 'green' | 'yellow' | 'red';
    details: {
        mrp_check: boolean;
        brand_check: boolean;
        category_check: boolean;
        issues: string[];
    };
}

export interface ProductSearchResponse {
    status: 'success' | 'error';
    products: Product[];
    query: string;
    platform: string;
    count: number;
    message?: string;
}

export interface Stats {
    total_scans: number;
    compliance_rate: number;
    violations_flagged: number;
    devices_online: number;
    total_products_checked: number;
}

export interface RecentScan {
    product_id: string;
    brand: string;
    category: string;
    status: string;
}

export interface OCRResult {
    extracted_text: string;
    confidence: number;
    analysis: string;
}
