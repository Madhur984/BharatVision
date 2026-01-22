import { HelpCircle, Book, FileText, Mail } from 'lucide-react';

export default function Help() {
    return (
        <div className="space-y-6">
            <div className="bg-navy text-white p-6 rounded-2xl shadow-lg">
                <h1 className="text-3xl font-bold">Help & Documentation</h1>
                <p className="mt-2 opacity-90">
                    Get help with using BharatVision
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <HelpCard
                    icon={<Book size={32} />}
                    title="User Guide"
                    description="Learn how to use BharatVision for compliance checking"
                />
                <HelpCard
                    icon={<FileText size={32} />}
                    title="API Documentation"
                    description="Technical documentation for developers"
                />
                <HelpCard
                    icon={<HelpCircle size={32} />}
                    title="FAQs"
                    description="Frequently asked questions and answers"
                />
                <HelpCard
                    icon={<Mail size={32} />}
                    title="Contact Support"
                    description="Get in touch with our support team"
                />
            </div>
        </div>
    );
}

interface HelpCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
}

function HelpCard({ icon, title, description }: HelpCardProps) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-200 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="text-navy mb-4">{icon}</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
            <p className="text-gray-600">{description}</p>
        </div>
    );
}
