import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { Upload, Loader2, FileImage, CheckCircle } from 'lucide-react';
import type { OCRResult } from '../types';

export default function OCRUpload() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [preview, setPreview] = useState<string | null>(null);
    const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);

    const uploadMutation = useMutation({
        mutationFn: (file: File) => api.uploadImage(file),
        onSuccess: (data) => {
            setOcrResult(data);
        },
    });

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setOcrResult(null);

            // Create preview
            const reader = new FileReader();
            reader.onloadend = () => {
                setPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            setSelectedFile(file);
            setOcrResult(null);

            const reader = new FileReader();
            reader.onloadend = () => {
                setPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    const handleAnalyze = () => {
        if (selectedFile) {
            uploadMutation.mutate(selectedFile);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-navy text-white p-6 rounded-2xl shadow-lg">
                <h1 className="text-3xl font-bold">OCR Image Analysis</h1>
                <p className="mt-2 opacity-90">
                    Upload product images to extract text and check Legal Metrology compliance
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Upload Section */}
                <div className="space-y-6">
                    {/* Drag & Drop Area */}
                    <div
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        className="bg-white p-8 rounded-xl shadow-md border-2 border-dashed border-gray-300 hover:border-navy transition-colors cursor-pointer"
                    >
                        <label className="cursor-pointer block">
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileSelect}
                                className="hidden"
                            />
                            <div className="text-center">
                                <Upload className="mx-auto text-gray-400 mb-4" size={48} />
                                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                                    Upload Product Image
                                </h3>
                                <p className="text-sm text-gray-500 mb-4">
                                    Drag and drop or click to browse
                                </p>
                                <p className="text-xs text-gray-400">
                                    Supported formats: JPG, PNG, JPEG
                                </p>
                            </div>
                        </label>
                    </div>

                    {/* Preview */}
                    {preview && (
                        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                <FileImage size={20} />
                                Image Preview
                            </h3>
                            <img
                                src={preview}
                                alt="Preview"
                                className="w-full rounded-lg border border-gray-200"
                            />
                            <button
                                onClick={handleAnalyze}
                                disabled={uploadMutation.isPending}
                                className="w-full mt-4 bg-navy text-white px-6 py-3 rounded-lg font-semibold hover:bg-navy-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {uploadMutation.isPending ? (
                                    <>
                                        <Loader2 className="animate-spin" size={20} />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle size={20} />
                                        Analyze Image
                                    </>
                                )}
                            </button>
                        </div>
                    )}
                </div>

                {/* Results Section */}
                <div className="space-y-6">
                    {uploadMutation.isError && (
                        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg">
                            <p className="font-semibold">Error analyzing image</p>
                            <p className="text-sm mt-1">
                                {(uploadMutation.error as Error).message || 'Please try again'}
                            </p>
                        </div>
                    )}

                    {ocrResult && (
                        <>
                            {/* Extracted Text */}
                            <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                                <h3 className="text-lg font-bold text-gray-900 mb-4 border-b-2 border-navy pb-2">
                                    Extracted Text
                                </h3>
                                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                                    <p className="text-sm text-gray-800 whitespace-pre-wrap">
                                        {ocrResult.extracted_text || 'No text detected'}
                                    </p>
                                </div>
                                <div className="mt-4 flex items-center gap-2 text-sm">
                                    <span className="font-semibold text-gray-700">Confidence:</span>
                                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-navy h-2 rounded-full transition-all"
                                            style={{ width: `${ocrResult.confidence}%` }}
                                        ></div>
                                    </div>
                                    <span className="font-bold text-navy">{ocrResult.confidence}%</span>
                                </div>
                            </div>

                            {/* Analysis */}
                            <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                                <h3 className="text-lg font-bold text-gray-900 mb-4 border-b-2 border-navy pb-2">
                                    Compliance Analysis
                                </h3>
                                <p className="text-gray-700">{ocrResult.analysis}</p>
                            </div>
                        </>
                    )}

                    {!ocrResult && !uploadMutation.isPending && (
                        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl p-12 text-center">
                            <FileImage className="mx-auto text-gray-400 mb-4" size={48} />
                            <h3 className="text-xl font-semibold text-gray-700 mb-2">
                                No results yet
                            </h3>
                            <p className="text-gray-500">
                                Upload an image to see OCR extraction and compliance analysis
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
