import { BarChart3 } from 'lucide-react';

export default function Analytics() {
    return (
        <div className="space-y-6">
            <div className="bg-navy text-white p-6 rounded-2xl shadow-lg">
                <h1 className="text-3xl font-bold">Analytics & Reports</h1>
                <p className="mt-2 opacity-90">
                    Detailed analytics and compliance reports
                </p>
            </div>

            <div className="bg-white p-12 rounded-xl shadow-md border border-gray-200 text-center">
                <BarChart3 className="mx-auto text-gray-400 mb-4" size={64} />
                <h2 className="text-2xl font-bold text-gray-700 mb-2">Analytics Dashboard</h2>
                <p className="text-gray-500">
                    Advanced analytics features coming soon
                </p>
            </div>
        </div>
    );
}
