import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    Home, RefreshCw, Building, Palmtree, TrendingUp,
    Award, ThumbsUp, AlertCircle, ArrowRight, ArrowLeft,
    Mail, Lock, Loader, CheckCircle
} from 'lucide-react';

export default function BorrowerFunnel() {
    const navigate = useNavigate();
    const { register } = useAuth();

    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Funnel answers stored in state
    const [answers, setAnswers] = useState({
        purpose: null,      // "buy" | "refinance"
        occupancy: null,    // "primary" | "vacation" | "investment"
        credit: null        // "excellent" | "good" | "fair"
    });

    // Registration form
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });

    const totalSteps = 4;

    const handleSelect = (key, value) => {
        setAnswers({ ...answers, [key]: value });
        // Auto-advance to next step
        setTimeout(() => setStep(step + 1), 200);
    };

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // Pass funnel answers as initial_metadata
            await register(formData.email, formData.password, 'applicant', {
                purpose: answers.purpose,
                occupancy: answers.occupancy,
                credit: answers.credit,
                funnel_completed_at: new Date().toISOString()
            });
            // Navigate to dashboard on success
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Step 1: Purpose
    const renderStep1 = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    What brings you here today?
                </h2>
                <p className="text-gray-500">Let's find the right solution for you</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <OptionCard
                    icon={Home}
                    title="Buy a Home"
                    description="I'm looking to purchase a new property"
                    selected={answers.purpose === 'buy'}
                    onClick={() => handleSelect('purpose', 'buy')}
                />
                <OptionCard
                    icon={RefreshCw}
                    title="Refinance"
                    description="I want to refinance my current mortgage"
                    selected={answers.purpose === 'refinance'}
                    onClick={() => handleSelect('purpose', 'refinance')}
                />
            </div>
        </div>
    );

    // Step 2: Occupancy
    const renderStep2 = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    How will you use this property?
                </h2>
                <p className="text-gray-500">This helps us find the best rates for you</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <OptionCard
                    icon={Building}
                    title="Primary Residence"
                    description="I'll live here full-time"
                    selected={answers.occupancy === 'primary'}
                    onClick={() => handleSelect('occupancy', 'primary')}
                    compact
                />
                <OptionCard
                    icon={Palmtree}
                    title="Vacation Home"
                    description="Second home / getaway"
                    selected={answers.occupancy === 'vacation'}
                    onClick={() => handleSelect('occupancy', 'vacation')}
                    compact
                />
                <OptionCard
                    icon={TrendingUp}
                    title="Investment"
                    description="Rental property"
                    selected={answers.occupancy === 'investment'}
                    onClick={() => handleSelect('occupancy', 'investment')}
                    compact
                />
            </div>
        </div>
    );

    // Step 3: Credit
    const renderStep3 = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    How would you rate your credit?
                </h2>
                <p className="text-gray-500">A rough estimate is fine - we'll verify later</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <OptionCard
                    icon={Award}
                    title="Excellent"
                    description="720+"
                    badge="Best Rates"
                    badgeColor="green"
                    selected={answers.credit === 'excellent'}
                    onClick={() => handleSelect('credit', 'excellent')}
                    compact
                />
                <OptionCard
                    icon={ThumbsUp}
                    title="Good"
                    description="680 - 720"
                    selected={answers.credit === 'good'}
                    onClick={() => handleSelect('credit', 'good')}
                    compact
                />
                <OptionCard
                    icon={AlertCircle}
                    title="Fair"
                    description="Below 680"
                    badge="Options Available"
                    badgeColor="amber"
                    selected={answers.credit === 'fair'}
                    onClick={() => handleSelect('credit', 'fair')}
                    compact
                />
            </div>
        </div>
    );

    // Step 4: Registration
    const renderStep4 = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="text-center mb-8">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle size={32} className="text-blue-600" />
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                    Great! Let's create your account
                </h2>
                <p className="text-gray-500">Almost there - just a few more details</p>
            </div>

            {/* Summary of answers */}
            <div className="bg-gray-50 rounded-xl p-4 mb-6 border border-gray-100">
                <p className="text-xs uppercase tracking-wider text-gray-500 mb-3 font-medium">Your Profile</p>
                <div className="flex flex-wrap gap-2">
                    <span className="bg-white px-3 py-1 rounded-full text-sm border border-gray-200 text-gray-700">
                        {answers.purpose === 'buy' ? 'Buying' : 'Refinancing'}
                    </span>
                    <span className="bg-white px-3 py-1 rounded-full text-sm border border-gray-200 text-gray-700">
                        {answers.occupancy === 'primary' ? 'Primary Home' :
                         answers.occupancy === 'vacation' ? 'Vacation Home' : 'Investment'}
                    </span>
                    <span className="bg-white px-3 py-1 rounded-full text-sm border border-gray-200 text-gray-700">
                        {answers.credit === 'excellent' ? 'Excellent Credit' :
                         answers.credit === 'good' ? 'Good Credit' : 'Fair Credit'}
                    </span>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-center gap-3 border border-red-100">
                    <AlertCircle size={20} />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            <form onSubmit={handleRegister} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                    <div className="relative">
                        <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
                        <input
                            name="email"
                            type="email"
                            required
                            placeholder="you@example.com"
                            value={formData.email}
                            onChange={handleInputChange}
                            className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Create Password</label>
                    <div className="relative">
                        <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                        <input
                            name="password"
                            type="password"
                            required
                            placeholder="Min. 8 characters"
                            value={formData.password}
                            onChange={handleInputChange}
                            className="w-full pl-11 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className={`
                        w-full py-3 rounded-xl font-semibold text-white
                        flex items-center justify-center gap-2
                        transition-all duration-200
                        ${loading
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg'
                        }
                    `}
                >
                    {loading ? (
                        <Loader className="animate-spin" size={20} />
                    ) : (
                        <>
                            Create Account
                            <ArrowRight size={18} />
                        </>
                    )}
                </button>
            </form>

            <p className="text-center text-sm text-gray-500 mt-4">
                Already have an account?{' '}
                <button onClick={() => navigate('/login')} className="text-blue-600 hover:underline font-medium">
                    Sign in
                </button>
            </p>
        </div>
    );

    return (
        <div className="min-h-[calc(100vh-64px)] bg-gradient-to-b from-gray-50 to-white flex items-center justify-center p-4">
            <div className="max-w-xl w-full">
                {/* Progress Bar */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-2">
                        {[1, 2, 3, 4].map((s) => (
                            <div
                                key={s}
                                className={`
                                    w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm
                                    transition-all duration-300
                                    ${step >= s
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-400'
                                    }
                                `}
                            >
                                {step > s ? <CheckCircle size={18} /> : s}
                            </div>
                        ))}
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-600 transition-all duration-500 ease-out rounded-full"
                            style={{ width: `${((step - 1) / (totalSteps - 1)) * 100}%` }}
                        />
                    </div>
                </div>

                {/* Card Container */}
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
                    {step === 1 && renderStep1()}
                    {step === 2 && renderStep2()}
                    {step === 3 && renderStep3()}
                    {step === 4 && renderStep4()}

                    {/* Back Button (for steps 2-4) */}
                    {step > 1 && (
                        <button
                            onClick={() => setStep(step - 1)}
                            className="mt-6 flex items-center gap-2 text-gray-500 hover:text-gray-700 transition text-sm"
                        >
                            <ArrowLeft size={16} />
                            Back
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Reusable Option Card Component
function OptionCard({ icon: Icon, title, description, badge, badgeColor, selected, onClick, compact }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`
                relative text-left p-5 rounded-xl border-2 transition-all duration-200
                ${compact ? 'p-4' : 'p-5'}
                ${selected
                    ? 'border-blue-600 bg-blue-50 ring-2 ring-blue-200'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
            `}
        >
            {badge && (
                <span className={`
                    absolute top-3 right-3 text-xs px-2 py-0.5 rounded-full font-medium
                    ${badgeColor === 'green' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}
                `}>
                    {badge}
                </span>
            )}
            <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center mb-3
                ${selected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}
            `}>
                <Icon size={20} />
            </div>
            <h3 className={`font-semibold ${selected ? 'text-blue-900' : 'text-gray-900'}`}>
                {title}
            </h3>
            <p className={`text-sm mt-1 ${selected ? 'text-blue-700' : 'text-gray-500'}`}>
                {description}
            </p>
        </button>
    );
}
