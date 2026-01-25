import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import {
    PlusCircle, FileText, Calendar, DollarSign, Loader, RefreshCw,
    CheckCircle, Circle, ArrowRight, Eye, FolderOpen, PenTool,
    Upload, Brain, UserCheck, FileSignature, Building, PartyPopper,
    AlertCircle, Clock
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

// Progress Stepper Component
function ProgressStepper({ currentStage, status }) {
    const stages = [
        { key: 'applied', label: 'Applied', icon: Upload },
        { key: 'ai_review', label: 'AI Review', icon: Brain },
        { key: 'manager_review', label: 'Manager Review', icon: UserCheck },
        { key: 'sign_docs', label: 'Sign Docs', icon: FileSignature },
        { key: 'underwriting', label: 'Underwriting', icon: Building },
        { key: 'funded', label: 'Funded', icon: PartyPopper },
    ];

    // Determine current step based on status and loan_stage
    const getStepIndex = () => {
        const s = status?.toLowerCase() || "";
        const stage = currentStage?.toUpperCase() || "";

        if (s.includes("rejected")) return -1; // Rejected
        if (stage === "ARCHIVED" && !s.includes("rejected")) return 5; // Funded
        if (stage === "CLOSING") return 4; // Underwriting complete
        if (s.includes("signed") || stage === "CLOSING") return 4;
        if (stage === "UNDERWRITING") return 3; // Waiting for signature
        if (stage === "PROCESSING") return 2; // Manager approved
        if (s.includes("approved")) return 2;
        if (s.includes("submitted")) return 1; // AI Review
        return 0; // Applied
    };

    const currentStep = getStepIndex();
    const isRejected = status?.toLowerCase().includes("rejected");

    return (
        <div className="w-full py-4">
            <div className="flex items-center justify-between">
                {stages.map((stage, idx) => {
                    const Icon = stage.icon;
                    const isCompleted = currentStep > idx;
                    const isCurrent = currentStep === idx;
                    const isPending = currentStep < idx;

                    return (
                        <React.Fragment key={stage.key}>
                            {/* Step Circle */}
                            <div className="flex flex-col items-center">
                                <div className={`
                                    w-10 h-10 rounded-full flex items-center justify-center transition-all
                                    ${isRejected && idx > 0 ? 'bg-gray-200 text-gray-400' :
                                        isCompleted ? 'bg-green-500 text-white' :
                                            isCurrent ? 'bg-blue-600 text-white ring-4 ring-blue-200' :
                                                'bg-gray-200 text-gray-400'}
                                `}>
                                    {isCompleted ? <CheckCircle size={20} /> : <Icon size={18} />}
                                </div>
                                <span className={`
                                    mt-2 text-xs font-medium
                                    ${isCompleted ? 'text-green-600' :
                                        isCurrent ? 'text-blue-600' : 'text-gray-400'}
                                `}>
                                    {stage.label}
                                </span>
                            </div>

                            {/* Connector Line */}
                            {idx < stages.length - 1 && (
                                <div className={`
                                    flex-1 h-1 mx-2 rounded
                                    ${isCompleted ? 'bg-green-500' :
                                        isCurrent ? 'bg-blue-200' : 'bg-gray-200'}
                                `} />
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        </div>
    );
}

// Action Card Component
function ActionCard({ title, description, icon: Icon, action, actionLabel, variant = "primary", loading }) {
    const variants = {
        primary: "bg-blue-600 hover:bg-blue-700 text-white",
        warning: "bg-orange-500 hover:bg-orange-600 text-white",
        success: "bg-green-600 hover:bg-green-700 text-white",
        secondary: "bg-gray-100 hover:bg-gray-200 text-gray-700",
    };

    return (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl p-6 shadow-lg">
            <div className="flex items-start gap-4">
                <div className="w-14 h-14 bg-blue-600 text-white rounded-xl flex items-center justify-center flex-shrink-0">
                    <Icon size={28} />
                </div>
                <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900">{title}</h3>
                    <p className="text-gray-600 mt-1">{description}</p>
                    {action && (
                        <button
                            onClick={action}
                            disabled={loading}
                            className={`mt-4 px-6 py-2.5 rounded-lg font-bold transition flex items-center gap-2 ${variants[variant]} disabled:opacity-50`}
                        >
                            {loading ? <Loader size={18} className="animate-spin" /> : <Icon size={18} />}
                            {actionLabel}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Application Card Component
function ApplicationCard({ app, onSign, signingId, onRefresh }) {
    const needsSignature = () => {
        const s = app.status?.toLowerCase() || "";
        const stage = app.loan_stage?.toUpperCase() || "";
        return s.includes("approved") && stage === "UNDERWRITING";
    };

    const formatCurrency = (amount) => {
        const num = parseFloat(amount) || 0;
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(num);
    };

    const getStatusInfo = () => {
        const s = app.status?.toLowerCase() || "";
        const stage = app.loan_stage?.toUpperCase() || "";

        if (s.includes("rejected")) return { color: "red", label: "Rejected", icon: AlertCircle };
        if (stage === "ARCHIVED") return { color: "green", label: "Completed", icon: CheckCircle };
        if (stage === "CLOSING") return { color: "green", label: "Closing", icon: Building };
        if (s.includes("signed")) return { color: "green", label: "Signed", icon: CheckCircle };
        if (stage === "UNDERWRITING") return { color: "orange", label: "Sign Required", icon: PenTool };
        if (s.includes("approved")) return { color: "green", label: "Approved", icon: CheckCircle };
        if (s.includes("submitted")) return { color: "blue", label: "In Review", icon: Clock };
        return { color: "gray", label: "Processing", icon: Loader };
    };

    const statusInfo = getStatusInfo();
    const StatusIcon = statusInfo.icon;

    const colorClasses = {
        red: "bg-red-100 text-red-700 border-red-200",
        green: "bg-green-100 text-green-700 border-green-200",
        orange: "bg-orange-100 text-orange-700 border-orange-200",
        blue: "bg-blue-100 text-blue-700 border-blue-200",
        gray: "bg-gray-100 text-gray-700 border-gray-200",
    };

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Progress Stepper */}
            <div className="px-6 pt-4 border-b border-gray-100 bg-gray-50">
                <ProgressStepper currentStage={app.loan_stage} status={app.status} />
            </div>

            {/* Card Content */}
            <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${colorClasses[statusInfo.color]}`}>
                                <StatusIcon size={14} />
                                {statusInfo.label}
                            </span>
                            <span className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                                {app.workflow_id.slice(0, 12)}...
                            </span>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                                <DollarSign size={14} className="text-green-600" />
                                <span className="font-semibold text-gray-900">{formatCurrency(app.loan_amount)}</span>
                            </span>
                            <span className="flex items-center gap-1">
                                <Calendar size={14} />
                                {new Date(app.created_at).toLocaleDateString()}
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onRefresh}
                        className="p-2 hover:bg-gray-100 rounded-lg transition text-gray-400 hover:text-gray-600"
                    >
                        <RefreshCw size={16} />
                    </button>
                </div>

                {/* Action Required Card */}
                {needsSignature() && (
                    <ActionCard
                        title="Action Required: Sign Your Documents"
                        description="Your Initial Disclosures are ready. Please review and sign to proceed to underwriting."
                        icon={PenTool}
                        action={() => onSign(app.workflow_id)}
                        actionLabel={signingId === app.workflow_id ? "Signing..." : "Sign Documents Now"}
                        variant="warning"
                        loading={signingId === app.workflow_id}
                    />
                )}

                {/* View Documents */}
                {!needsSignature() && (app.status?.toLowerCase().includes('approved') || app.status?.toLowerCase().includes('signed') || app.loan_stage === 'CLOSING' || app.loan_stage === 'ARCHIVED') && (
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => window.open(`${API_URL}/static/${app.workflow_id}/Initial_Disclosures.pdf`, '_blank')}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg font-medium transition"
                        >
                            <Eye size={16} />
                            View Disclosures
                        </button>
                        {app.status?.toLowerCase().includes('signed') && (
                            <button
                                onClick={() => window.open(`${API_URL}/static/${app.workflow_id}/Initial_Disclosures_SIGNED.pdf`, '_blank')}
                                className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 hover:bg-green-200 rounded-lg font-medium transition"
                            >
                                <CheckCircle size={16} />
                                View Signed Copy
                            </button>
                        )}
                    </div>
                )}

                {/* Decision Reason */}
                {app.decision_reason && (
                    <div className={`mt-4 p-3 rounded-lg text-sm ${app.status?.toLowerCase().includes('approved')
                            ? 'bg-green-50 border border-green-200 text-green-800'
                            : 'bg-red-50 border border-red-200 text-red-800'
                        }`}>
                        <strong>Manager Note:</strong> {app.decision_reason}
                    </div>
                )}
            </div>
        </div>
    );
}

// Empty State Component
function EmptyState() {
    return (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-12">
            <div className="max-w-md mx-auto text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                    <FileText size={40} />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">Start Your Loan Journey</h3>
                <p className="text-gray-500 mb-8">
                    Apply for a mortgage in minutes. Our AI-powered system will analyze your documents
                    and provide a decision quickly.
                </p>

                {/* Visual Steps */}
                <div className="grid grid-cols-4 gap-2 mb-8">
                    {[
                        { icon: Upload, label: "Upload" },
                        { icon: Brain, label: "AI Review" },
                        { icon: UserCheck, label: "Approval" },
                        { icon: PartyPopper, label: "Funded" },
                    ].map((step, idx) => (
                        <div key={idx} className="flex flex-col items-center">
                            <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mb-2">
                                <step.icon size={20} className="text-gray-400" />
                            </div>
                            <span className="text-xs text-gray-500">{step.label}</span>
                        </div>
                    ))}
                </div>

                <Link
                    to="/apply"
                    className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-blue-700 transition shadow-lg hover:shadow-xl hover:-translate-y-0.5 text-lg"
                >
                    <PlusCircle size={22} />
                    Start Application
                </Link>
            </div>
        </div>
    );
}

export default function ApplicantDashboard() {
    const { user } = useAuth();
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [signingId, setSigningId] = useState(null);

    const handleSignDocuments = async (workflowId) => {
        setSigningId(workflowId);
        try {
            await api.post(`/applications/${workflowId}/sign`);
            await fetchApplications();
        } catch (err) {
            console.error('Error signing documents:', err);
            alert('Failed to sign documents. Please try again.');
        } finally {
            setSigningId(null);
        }
    };

    const fetchApplications = async () => {
        setLoading(true);
        try {
            const res = await api.get('/applications');
            setApplications(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchApplications();
        // Auto-refresh every 10 seconds
        const interval = setInterval(fetchApplications, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-4xl mx-auto p-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                            Welcome back, {user?.email?.split('@')[0]}!
                        </h1>
                        <p className="text-gray-500 mt-1">Track your loan application progress</p>
                    </div>
                    <Link
                        to="/apply"
                        className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg font-bold hover:bg-blue-700 transition shadow-md hover:shadow-lg"
                    >
                        <PlusCircle size={18} /> New Application
                    </Link>
                </div>

                {/* Content */}
                {loading && applications.length === 0 ? (
                    <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
                        <Loader className="animate-spin mx-auto text-blue-600 mb-4" size={32} />
                        <p className="text-gray-500">Loading your applications...</p>
                    </div>
                ) : applications.length === 0 ? (
                    <EmptyState />
                ) : (
                    <div className="space-y-6">
                        {applications.map((app) => (
                            <ApplicationCard
                                key={app.workflow_id}
                                app={app}
                                onSign={handleSignDocuments}
                                signingId={signingId}
                                onRefresh={fetchApplications}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
