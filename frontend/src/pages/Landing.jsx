import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, Briefcase, Building2, ArrowRight, Shield, Zap, Award } from 'lucide-react';

export default function Landing() {
    const navigate = useNavigate();

    const portals = [
        {
            id: 'borrowers',
            title: 'Borrowers',
            subtitle: 'I need a loan',
            description: 'Get pre-qualified in minutes. Fast, simple, and secure.',
            icon: Home,
            cta: 'Get Started',
            color: 'blue',
            route: '/funnel',
            primary: true
        },
        {
            id: 'staff',
            title: 'Staff',
            subtitle: 'I work here',
            description: 'Access your dashboard to manage applications and workflows.',
            icon: Briefcase,
            cta: 'Staff Login',
            color: 'gray',
            route: '/login'
        },
        {
            id: 'partners',
            title: 'Real Estate Partners',
            subtitle: 'I refer clients',
            description: 'Partner portal for real estate agents and brokers.',
            icon: Building2,
            cta: 'Partner Access',
            color: 'emerald',
            route: '/login'
        }
    ];

    const features = [
        { icon: Zap, title: 'Fast Pre-Qualification', description: 'Get answers in minutes, not days' },
        { icon: Shield, title: 'Bank-Level Security', description: 'Your data is encrypted and protected' },
        { icon: Award, title: 'Best Rates Guaranteed', description: 'Competitive rates from top lenders' }
    ];

    return (
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-gray-50 to-white">
            {/* Hero Section */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight mb-6">
                        Welcome to <span className="text-blue-600">Moxi Mortgage</span>
                    </h1>
                    <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                        Your journey to homeownership starts here. Fast approvals, competitive rates, and a seamless digital experience.
                    </p>
                </div>

                {/* Portal Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 max-w-5xl mx-auto">
                    {portals.map((portal) => {
                        const IconComponent = portal.icon;
                        const isPrimary = portal.primary;

                        return (
                            <div
                                key={portal.id}
                                onClick={() => navigate(portal.route)}
                                className={`
                                    relative group cursor-pointer rounded-2xl p-8
                                    transition-all duration-300 ease-out
                                    ${isPrimary
                                        ? 'bg-blue-600 text-white shadow-xl shadow-blue-200 hover:shadow-2xl hover:shadow-blue-300 hover:-translate-y-1'
                                        : 'bg-white border border-gray-200 hover:border-gray-300 hover:shadow-lg hover:-translate-y-1'
                                    }
                                `}
                            >
                                {/* Icon */}
                                <div className={`
                                    w-14 h-14 rounded-xl flex items-center justify-center mb-6
                                    ${isPrimary ? 'bg-blue-500' : 'bg-gray-100'}
                                `}>
                                    <IconComponent
                                        size={28}
                                        className={isPrimary ? 'text-white' : 'text-gray-600'}
                                    />
                                </div>

                                {/* Content */}
                                <h3 className={`text-xl font-semibold mb-1 ${isPrimary ? 'text-white' : 'text-gray-900'}`}>
                                    {portal.title}
                                </h3>
                                <p className={`text-sm mb-4 ${isPrimary ? 'text-blue-100' : 'text-gray-500'}`}>
                                    {portal.subtitle}
                                </p>
                                <p className={`text-sm mb-6 leading-relaxed ${isPrimary ? 'text-blue-100' : 'text-gray-600'}`}>
                                    {portal.description}
                                </p>

                                {/* CTA Button */}
                                <div className={`
                                    inline-flex items-center gap-2 font-medium text-sm
                                    ${isPrimary ? 'text-white' : 'text-blue-600'}
                                    group-hover:gap-3 transition-all duration-200
                                `}>
                                    {portal.cta}
                                    <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
                                </div>

                                {/* Primary Badge */}
                                {isPrimary && (
                                    <div className="absolute top-4 right-4 bg-blue-500 text-xs px-2 py-1 rounded-full text-blue-100">
                                        Most Popular
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Features Section */}
                <div className="mt-24 max-w-4xl mx-auto">
                    <h2 className="text-2xl font-semibold text-center text-gray-900 mb-12">
                        Why Choose Moxi Mortgage?
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {features.map((feature, index) => {
                            const FeatureIcon = feature.icon;
                            return (
                                <div key={index} className="text-center">
                                    <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mx-auto mb-4">
                                        <FeatureIcon size={24} className="text-blue-600" />
                                    </div>
                                    <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                                    <p className="text-sm text-gray-600">{feature.description}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-24 text-center text-sm text-gray-500 pb-8">
                    <p>NMLS #123456 | Equal Housing Opportunity</p>
                    <p className="mt-2">Moxi Mortgage Corporation | All Rights Reserved</p>
                </div>
            </div>
        </div>
    );
}
