import type { Product, ComplianceCheckResponse } from '../types';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface ProductCardProps {
    product: Product;
    onCheckCompliance?: (product: Product) => void;
    complianceResult?: ComplianceCheckResponse;
}

export default function ProductCard({
    product,
    onCheckCompliance,
    complianceResult,
}: ProductCardProps) {
    const getStatusIcon = () => {
        if (!complianceResult) return null;

        if (complianceResult.status === 'Compliant') {
            return <CheckCircle className="text-green-600" size={20} />;
        } else if (complianceResult.status === 'Partial') {
            return <AlertCircle className="text-yellow-600" size={20} />;
        } else {
            return <XCircle className="text-red-600" size={20} />;
        }
    };

    const getStatusBadge = () => {
        if (!complianceResult) return null;

        const colors = {
            green: 'bg-green-100 text-green-800 border-green-300',
            yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
            red: 'bg-red-100 text-red-800 border-red-300',
        };

        return (
            <div
                className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold border ${colors[complianceResult.color]
                    }`}
            >
                {getStatusIcon()}
                <span>{complianceResult.status}</span>
                <span className="font-bold">({complianceResult.score}%)</span>
            </div>
        );
    };

    return (
        <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
            {/* Product Image */}
            <div className="aspect-square bg-gray-100 flex items-center justify-center overflow-hidden">
                <img
                    src={product.image}
                    alt={product.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                        (e.target as HTMLImageElement).src =
                            'https://via.placeholder.com/300x300?text=Product';
                    }}
                />
            </div>

            {/* Product Info */}
            <div className="p-4">
                <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2">
                    {product.title}
                </h3>

                <div className="space-y-1 text-sm mb-3">
                    <p className="text-gray-600">
                        <span className="font-medium">Brand:</span> {product.brand}
                    </p>
                    <p className="text-gray-600">
                        <span className="font-medium">Category:</span> {product.category}
                    </p>
                    <div className="flex items-center gap-3">
                        <p className="text-lg font-bold text-navy">₹{product.price}</p>
                        {product.mrp > product.price && (
                            <p className="text-sm text-gray-500 line-through">₹{product.mrp}</p>
                        )}
                    </div>
                </div>

                {/* Compliance Badge */}
                {complianceResult && (
                    <div className="mb-3">{getStatusBadge()}</div>
                )}

                {/* Check Compliance Button */}
                {onCheckCompliance && !complianceResult && (
                    <button
                        onClick={() => onCheckCompliance(product)}
                        className="w-full bg-navy text-white py-2 px-4 rounded-lg font-semibold hover:bg-navy-dark transition-colors"
                    >
                        Check Compliance
                    </button>
                )}

                {/* Show Issues if any */}
                {complianceResult && complianceResult.details.issues.length > 0 && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-xs font-semibold text-red-800 mb-1">Issues:</p>
                        <ul className="text-xs text-red-700 space-y-1">
                            {complianceResult.details.issues.map((issue, idx) => (
                                <li key={idx}>• {issue}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}
