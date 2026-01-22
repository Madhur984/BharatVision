import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { TrendingUp, AlertTriangle, CheckCircle, Activity } from 'lucide-react';
import {
    LineChart,
    Line,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';

export default function Dashboard() {
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['stats'],
        queryFn: api.getStats,
    });

    const { data: recentScans, isLoading: scansLoading } = useQuery({
        queryKey: ['recentScans'],
        queryFn: api.getRecentScans,
    });

    // Mock data for charts
    const violationsData = Array.from({ length: 30 }, (_, i) => ({
        date: `Day ${i + 1}`,
        violations: Math.floor(Math.random() * 100) + 100,
    }));

    const complianceData = stats
        ? [
            { name: 'Compliant', value: stats.compliance_rate },
            { name: 'Non-Compliant', value: 100 - stats.compliance_rate },
        ]
        : [];

    const COLORS = ['#10b981', '#ef4444'];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-navy text-white p-6 rounded-2xl shadow-lg">
                <div className="flex justify-between items-center">
                    <div>
                        <p className="text-sm opacity-90">Government of India · Ministry of Consumer Affairs</p>
                        <h1 className="text-3xl font-bold mt-1">National Packaging Compliance Dashboard</h1>
                    </div>
                    <div className="text-right">
                        <p className="text-sm">Today's Overview</p>
                        <p className="font-semibold">Central Command Console</p>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    icon={<Activity className="text-navy" size={24} />}
                    label="Total Scans Today"
                    value={stats?.total_scans || 0}
                    subtitle="Across all devices"
                    loading={statsLoading}
                />
                <StatCard
                    icon={<CheckCircle className="text-green-600" size={24} />}
                    label="Compliance Rate"
                    value={`${stats?.compliance_rate || 0}%`}
                    subtitle="Last 30 days"
                    loading={statsLoading}
                />
                <StatCard
                    icon={<AlertTriangle className="text-red-600" size={24} />}
                    label="Violations Flagged"
                    value={stats?.violations_flagged || 0}
                    subtitle="Pending review"
                    loading={statsLoading}
                />
                <StatCard
                    icon={<TrendingUp className="text-blue-600" size={24} />}
                    label="Products Checked"
                    value={stats?.total_products_checked || 0}
                    subtitle="All time"
                    loading={statsLoading}
                />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Violations Over Time */}
                <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-md border border-gray-200">
                    <h2 className="text-lg font-bold text-gray-900 mb-4 border-b-2 border-navy pb-2">
                        Violations Over Time
                    </h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={violationsData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="violations"
                                stroke="#3866D5"
                                strokeWidth={2}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Compliance Pie Chart */}
                <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                    <h2 className="text-lg font-bold text-gray-900 mb-4 border-b-2 border-navy pb-2">
                        Overall Compliance
                    </h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={complianceData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                fill="#8884d8"
                                paddingAngle={5}
                                dataKey="value"
                                label
                            >
                                {complianceData.map((_entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Recent Scans Table */}
            <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200">
                <h2 className="text-lg font-bold text-gray-900 mb-4 border-b-2 border-navy pb-2">
                    Recent Scans
                </h2>
                {scansLoading ? (
                    <div className="text-center py-8 text-gray-500">Loading...</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Product ID</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Brand</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Category</th>
                                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentScans?.map((scan, idx) => (
                                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="py-3 px-4">{scan.product_id}</td>
                                        <td className="py-3 px-4">{scan.brand}</td>
                                        <td className="py-3 px-4">{scan.category}</td>
                                        <td className="py-3 px-4">
                                            <span
                                                className={`px-3 py-1 rounded-full text-sm font-semibold ${scan.status.toLowerCase().includes('compliant')
                                                    ? 'bg-green-100 text-green-800 border border-green-300'
                                                    : 'bg-red-100 text-red-800 border border-red-300'
                                                    }`}
                                            >
                                                {scan.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

interface StatCardProps {
    icon: React.ReactNode;
    label: string;
    value: string | number;
    subtitle: string;
    loading?: boolean;
}

function StatCard({ icon, label, value, subtitle, loading }: StatCardProps) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-navy">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-navy-light rounded-lg">{icon}</div>
                <div className="flex-1">
                    <p className="text-sm text-gray-600 font-medium">{label}</p>
                    {loading ? (
                        <div className="h-8 bg-gray-200 rounded animate-pulse mt-1"></div>
                    ) : (
                        <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
                </div>
            </div>
        </div>
    );
}
