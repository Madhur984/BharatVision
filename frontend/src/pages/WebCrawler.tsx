import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import ProductCard from '../components/ProductCard';
import type { Product, ComplianceCheckResponse } from '../types';
import { Search, Loader2 } from 'lucide-react';

export default function WebCrawler() {
    const [query, setQuery] = useState('packaged food');
    const [platform, setPlatform] = useState('amazon');
    const [products, setProducts] = useState<Product[]>([]);
    const [complianceResults, setComplianceResults] = useState<
        Record<number, ComplianceCheckResponse>
    >({});

    const searchMutation = useMutation({
        mutationFn: () => api.searchProducts(query, platform, 12),
        onSuccess: (data) => {
            if (data.status === 'success') {
                setProducts(data.products);
                setComplianceResults({});
            }
        },
    });

    const complianceMutation = useMutation({
        mutationFn: (product: Product) =>
            api.checkCompliance({
                title: product.title,
                brand: product.brand,
                price: product.price,
                mrp: product.mrp,
                image: product.image,
                category: product.category,
            }),
        onSuccess: (data, product) => {
            setComplianceResults((prev) => ({
                ...prev,
                [product.id]: data,
            }));
        },
    });

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        searchMutation.mutate();
    };

    const handleCheckCompliance = (product: Product) => {
        complianceMutation.mutate(product);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-navy text-white p-6 rounded-2xl shadow-lg">
                <h1 className="text-3xl font-bold">E-Commerce Web Crawler</h1>
                <p className="mt-2 opacity-90">
                    Search and analyze products from major e-commerce platforms for Legal Metrology compliance
                </p>
            </div>

            {/* Search Form */}
            <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                <form onSubmit={handleSearch} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Search Query */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Search Query
                            </label>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="e.g., packaged food, beverages, cosmetics"
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-transparent"
                            />
                        </div>

                        {/* Platform Selector */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Platform
                            </label>
                            <select
                                value={platform}
                                onChange={(e) => setPlatform(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-navy focus:border-transparent"
                            >
                                <option value="amazon">Amazon</option>
                                <option value="flipkart">Flipkart</option>
                                <option value="jiomart">JioMart</option>
                            </select>
                        </div>
                    </div>

                    {/* Search Button */}
                    <button
                        type="submit"
                        disabled={searchMutation.isPending}
                        className="w-full md:w-auto bg-navy text-white px-8 py-3 rounded-lg font-semibold hover:bg-navy-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {searchMutation.isPending ? (
                            <>
                                <Loader2 className="animate-spin" size={20} />
                                Searching...
                            </>
                        ) : (
                            <>
                                <Search size={20} />
                                Search Products
                            </>
                        )}
                    </button>
                </form>
            </div>

            {/* Error Message */}
            {searchMutation.isError && (
                <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg">
                    <p className="font-semibold">Error searching products</p>
                    <p className="text-sm mt-1">
                        {(searchMutation.error as Error).message || 'Please try again later'}
                    </p>
                </div>
            )}

            {/* Results */}
            {products.length > 0 && (
                <div>
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-2xl font-bold text-gray-900">
                            Search Results ({products.length})
                        </h2>
                        <p className="text-sm text-gray-600">
                            Platform: <span className="font-semibold capitalize">{platform}</span>
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {products.map((product) => (
                            <ProductCard
                                key={product.id}
                                product={product}
                                onCheckCompliance={handleCheckCompliance}
                                complianceResult={complianceResults[product.id]}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!searchMutation.isPending && products.length === 0 && (
                <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl p-12 text-center">
                    <Search className="mx-auto text-gray-400 mb-4" size={48} />
                    <h3 className="text-xl font-semibold text-gray-700 mb-2">No products yet</h3>
                    <p className="text-gray-500">
                        Enter a search query and select a platform to start crawling products
                    </p>
                </div>
            )}
        </div>
    );
}
