import { Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
    return (
        <div className="space-y-6">
            <div className="bg-navy text-white p-6 rounded-2xl shadow-lg">
                <h1 className="text-3xl font-bold">Settings</h1>
                <p className="mt-2 opacity-90">
                    Configure your BharatVision application
                </p>
            </div>

            <div className="bg-white p-12 rounded-xl shadow-md border border-gray-200 text-center">
                <SettingsIcon className="mx-auto text-gray-400 mb-4" size={64} />
                <h2 className="text-2xl font-bold text-gray-700 mb-2">Settings</h2>
                <p className="text-gray-500">
                    Configuration options coming soon
                </p>
            </div>
        </div>
    );
}
