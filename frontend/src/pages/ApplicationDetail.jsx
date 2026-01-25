import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import {
    FileText, CheckCircle, XCircle, AlertTriangle,
    Folder, Clock, ArrowLeft, RefreshCw, Save,
    FolderOpen, History, Edit3, Eye, Download,
    DollarSign, User, Mail, CreditCard, Building,
    TrendingUp, Shield, AlertOctagon, BadgeCheck, Percent
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

// Info Card Component with verification badge
function InfoCard({ label, value, icon: Icon, verified, source, warning }) {
    return (
        <div className={`p-4 rounded-lg border ${warning ? 'bg-red-50 border-red-200' : 'bg-white border-gray-200'}`}>
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-2 text-xs text-gray-500 uppercase mb-1">
                    {Icon && <Icon size={12} />}
                    {label}
                </div>
                {verified && (
                    <span className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                        <BadgeCheck size={10} />
                        Verified
                    </span>
                )}
                {warning && (
                    <span className="flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                        <AlertTriangle size={10} />
                        Mismatch
                    </span>
                )}
            </div>
            <div className={`text-lg font-bold ${warning ? 'text-red-700' : 'text-gray-900'}`}>
                {value || '-'}
            </div>
            {source && (
                <div className="text-xs text-gray-400 mt-1">
                    Source: {source}
                </div>
            )}
        </div>
    );
}

// Progress Bar Component
function ProgressBar({ stage }) {
    const stages = ['LEAD_CAPTURE', 'PROCESSING', 'UNDERWRITING', 'CLOSING', 'ARCHIVED'];
    const currentIdx = stages.indexOf(stage?.toUpperCase()) || 0;
    const progress = ((currentIdx + 1) / stages.length) * 100;

    return (
        <div className="w-full">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Lead Capture</span>
                <span>Clear to Close</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    );
}

// Document Thumbnail Component
function DocumentThumbnail({ file, onClick }) {
    return (
        <div
            onClick={onClick}
            className="bg-white border border-gray-200 rounded-lg p-3 hover:border-blue-300 hover:shadow-sm cursor-pointer transition group"
        >
            <div className="w-full h-20 bg-gray-100 rounded flex items-center justify-center mb-2">
                <FileText size={32} className="text-gray-400 group-hover:text-blue-500" />
            </div>
            <p className="text-xs font-medium text-gray-700 truncate">{file.name}</p>
            <p className="text-xs text-gray-400">PDF</p>
        </div>
    );
}

// Tab configuration
const TABS = [
    { key: 'overview', label: 'Overview', icon: TrendingUp },
    { key: 'documents', label: 'Documents', icon: FolderOpen },
    { key: 'timeline', label: 'Timeline', icon: History },
];

export default function ApplicationDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();

    const [details, setDetails] = useState(null);
    const [structure, setStructure] = useState([]);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState('overview');

    // Form editing state
    const [formData, setFormData] = useState({});
    const [editingField, setEditingField] = useState(null);
    const [saving, setSaving] = useState(false);

    // Review Modal State
    const [reviewModal, setReviewModal] = useState({ open: false, approved: false });
    const [reviewReason, setReviewReason] = useState("");

    const fetchData = async () => {
        try {
            const statusRes = await api.get(`/status/${id}`);
            setDetails(statusRes.data);

            // Initialize form data from loan_metadata.applicant_info
            const loanMetadata = statusRes.data?.loan_metadata || statusRes.data?.data || {};
            const info = loanMetadata.applicant_info || {};
            setFormData(info);

            try {
                const structRes = await api.get(`/applications/${id}/structure`);
                setStructure(structRes.data || []);
            } catch (e) {
                console.warn("Structure fetch failed:", e);
                setStructure([]);
            }

            try {
                const histRes = await api.get(`/applications/${id}/history`);
                setHistory(histRes.data || []);
            } catch (e) {
                console.warn("History fetch failed:", e);
                setHistory([]);
            }

            setLoading(false);
        } catch (err) {
            console.error(err);
            setError("Failed to load application data. " + (err.response?.data?.detail || err.message));
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(async () => {
            try {
                const histRes = await api.get(`/applications/${id}/history`);
                setHistory(histRes.data || []);
                const statusRes = await api.get(`/status/${id}`);
                setDetails(statusRes.data);
            } catch (e) { console.error(e); }
        }, 5000);
        return () => clearInterval(interval);
    }, [id]);

    const handleFieldChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const saveField = async (field) => {
        setSaving(true);
        try {
            await api.patch(`/applications/${id}/fields`, {
                field: field,
                value: formData[field]
            });
            setEditingField(null);
        } catch (err) {
            alert("Failed to save: " + err.message);
        }
        setSaving(false);
    };

    const openReviewModal = (approved) => {
        setReviewModal({ open: true, approved });
        setReviewReason("");
    };

    const submitReview = async () => {
        try {
            await api.post('/review', {
                workflow_id: id,
                approved: reviewModal.approved,
                reason: reviewReason
            });
            setReviewModal({ open: false, approved: false });
            fetchData();
        } catch (err) {
            alert("Action failed: " + err.message);
        }
    };

    if (loading) return (
        <div className="h-screen flex items-center justify-center bg-gray-100">
            <RefreshCw className="animate-spin text-blue-600" size={32} />
        </div>
    );

    if (error) return (
        <div className="p-8 text-center text-red-600 bg-gray-100 min-h-screen">
            <AlertTriangle className="mx-auto mb-4" size={48} />
            <p>{error}</p>
            <button onClick={() => navigate('/manager')} className="mt-4 text-blue-600 underline">
                Back to Dashboard
            </button>
        </div>
    );

    // Read from loan_metadata (Pyramid) or data (Original workflow)
    const loanMetadata = details?.loan_metadata || details?.data || {};
    const info = loanMetadata.applicant_info || formData;
    const analysis = loanMetadata.analysis || {};
    const riskEval = loanMetadata.risk_evaluation || {};
    const status = details?.status || "Unknown";
    const loanStage = details?.loan_stage || "LEAD_CAPTURE";
    const aiRecommendation = loanMetadata.ai_recommendation || "";
    const underwritingDecision = loanMetadata.underwriting_decision || "";

    const getStatusBadge = () => {
        const s = status.toLowerCase();
        if (underwritingDecision === "CLEAR_TO_CLOSE") return { color: "bg-green-500", text: "Clear to Close" };
        if (s.includes("signed")) return { color: "bg-green-500", text: "Signed" };
        if (s.includes("approved")) return { color: "bg-green-500", text: "Approved" };
        if (s.includes("rejected") || s.includes("fail")) return { color: "bg-red-500", text: "Rejected" };
        if (s.includes("review")) return { color: "bg-yellow-500", text: "In Review" };
        return { color: "bg-blue-500", text: "Processing" };
    };

    const statusBadge = getStatusBadge();

    const formatCurrency = (val) => {
        const num = parseFloat(val) || 0;
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0
        }).format(num);
    };

    return (
        <div className="h-[calc(100vh-64px)] bg-gray-100 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/manager')}
                            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition"
                        >
                            <ArrowLeft size={20} />
                        </button>
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-xl font-bold text-gray-900">{info.name || 'Borrower'}</h1>
                                <span className={`px-3 py-1 text-sm text-white font-medium rounded-lg ${statusBadge.color}`}>
                                    {statusBadge.text}
                                </span>
                                {aiRecommendation && (
                                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                                        aiRecommendation === 'APPROVED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                                    }`}>
                                        AI: {aiRecommendation}
                                    </span>
                                )}
                            </div>
                            <div className="text-sm text-gray-500 font-mono mt-1">{id}</div>
                        </div>
                    </div>
                    <button
                        onClick={fetchData}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition"
                    >
                        <RefreshCw size={18} />
                    </button>
                </div>

                {/* Progress Bar */}
                <ProgressBar stage={loanStage} />
            </div>

            {/* Tab Bar */}
            <div className="bg-white border-b border-gray-200 px-6 flex">
                {TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.key;
                    return (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition ${
                                isActive
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                            }`}
                        >
                            <Icon size={16} />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6">
                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div className="grid grid-cols-3 gap-6">
                        {/* Left Column - Borrower Info */}
                        <div className="space-y-4">
                            <div className="bg-white rounded-xl border border-gray-200 p-4">
                                <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                                    <User size={16} />
                                    Borrower Information
                                </h3>
                                <div className="space-y-3">
                                    <InfoCard label="Full Name" value={info.name} icon={User} />
                                    <InfoCard label="Email" value={info.email} icon={Mail} />
                                    <InfoCard
                                        label="SSN"
                                        value={info.ssn ? `***-**-${info.ssn.slice(-4)}` : '-'}
                                        icon={Shield}
                                    />
                                    <InfoCard
                                        label="Stated Income"
                                        value={formatCurrency(info.stated_income)}
                                        icon={DollarSign}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Middle Column - AI Analysis */}
                        <div className="space-y-4">
                            <div className="bg-white rounded-xl border border-gray-200 p-4">
                                <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                                    <TrendingUp size={16} />
                                    AI Verification Results
                                </h3>

                                {analysis.verified_income > 0 ? (
                                    <div className="space-y-3">
                                        <InfoCard
                                            label="Verified Income"
                                            value={formatCurrency(analysis.verified_income)}
                                            icon={DollarSign}
                                            verified={!analysis.income_mismatch}
                                            source="Tax Return & Pay Stub"
                                            warning={analysis.income_mismatch}
                                        />

                                        {analysis.income_mismatch && (
                                            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                                <div className="flex items-center gap-2 text-red-700 font-bold mb-2">
                                                    <AlertOctagon size={18} />
                                                    Income Mismatch Detected
                                                </div>
                                                <p className="text-sm text-red-600">
                                                    Stated: {formatCurrency(analysis.stated_income)} vs
                                                    Verified: {formatCurrency(analysis.verified_income)}
                                                </p>
                                            </div>
                                        )}

                                        <InfoCard
                                            label="AI Confidence"
                                            value={`${((analysis.confidence || 0) * 100).toFixed(0)}%`}
                                            icon={Percent}
                                            verified={analysis.confidence >= 0.8}
                                        />

                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div className="bg-gray-50 rounded p-2">
                                                <span className="text-gray-500">Pay Stub:</span>
                                                <span className="ml-1 font-medium">{formatCurrency(analysis.pay_stub_income)}</span>
                                            </div>
                                            <div className="bg-gray-50 rounded p-2">
                                                <span className="text-gray-500">Tax Return:</span>
                                                <span className="ml-1 font-medium">{formatCurrency(analysis.tax_income)}</span>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-gray-400">
                                        <TrendingUp size={32} className="mx-auto mb-2 opacity-30" />
                                        <p className="text-sm">AI analysis pending...</p>
                                    </div>
                                )}
                            </div>

                            {/* Risk Evaluation */}
                            {riskEval.decision && (
                                <div className="bg-white rounded-xl border border-gray-200 p-4">
                                    <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                                        <Shield size={16} />
                                        Underwriting Risk Assessment
                                    </h3>
                                    <div className="space-y-3">
                                        <div className={`p-4 rounded-lg ${
                                            riskEval.decision === 'CLEAR_TO_CLOSE'
                                                ? 'bg-green-50 border border-green-200'
                                                : 'bg-yellow-50 border border-yellow-200'
                                        }`}>
                                            <div className={`font-bold text-lg ${
                                                riskEval.decision === 'CLEAR_TO_CLOSE' ? 'text-green-700' : 'text-yellow-700'
                                            }`}>
                                                {riskEval.decision === 'CLEAR_TO_CLOSE' ? 'Clear to Close' : 'Referred for Review'}
                                            </div>
                                        </div>

                                        <InfoCard
                                            label="Credit Score"
                                            value={riskEval.credit_score || '-'}
                                            icon={CreditCard}
                                            verified={riskEval.credit_score > 700}
                                        />
                                        <InfoCard
                                            label="DTI Ratio"
                                            value={`${riskEval.dti_ratio || 0}%`}
                                            icon={Percent}
                                            verified={riskEval.dti_ratio < 43}
                                            warning={riskEval.dti_ratio >= 43}
                                        />

                                        {riskEval.issues?.length > 0 && (
                                            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                                                <div className="text-xs font-bold text-red-700 mb-2">Issues Found:</div>
                                                <ul className="text-xs text-red-600 space-y-1">
                                                    {riskEval.issues.map((issue, idx) => (
                                                        <li key={idx}>- {issue}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Right Column - Actions */}
                        <div className="space-y-4">
                            {/* Loan Details */}
                            <div className="bg-white rounded-xl border border-gray-200 p-4">
                                <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                                    <Building size={16} />
                                    Loan Details
                                </h3>
                                <div className="space-y-3">
                                    <InfoCard
                                        label="Loan Amount"
                                        value={formatCurrency(loanMetadata.loan_amount)}
                                        icon={DollarSign}
                                    />
                                    <InfoCard
                                        label="Property Value"
                                        value={formatCurrency(loanMetadata.property_value)}
                                        icon={Building}
                                    />
                                    <InfoCard
                                        label="Down Payment"
                                        value={formatCurrency(loanMetadata.down_payment)}
                                        icon={DollarSign}
                                    />
                                </div>
                            </div>

                            {/* Quick Actions for Manager */}
                            {user?.role === 'manager' && loanStage === 'LEAD_CAPTURE' && (
                                <div className="bg-white rounded-xl border border-gray-200 p-4">
                                    <h3 className="text-sm font-bold text-gray-700 mb-4">Manager Actions</h3>
                                    <div className="space-y-2">
                                        <button
                                            onClick={() => openReviewModal(true)}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition"
                                        >
                                            <CheckCircle size={18} /> Approve Application
                                        </button>
                                        <button
                                            onClick={() => openReviewModal(false)}
                                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-white border border-red-300 text-red-600 hover:bg-red-50 font-bold rounded-lg transition"
                                        >
                                            <XCircle size={18} /> Reject Application
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Documents Tab */}
                {activeTab === 'documents' && (
                    <div className="bg-white rounded-xl border border-gray-200 p-6">
                        <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                            <FolderOpen size={16} />
                            eFolder ({structure.length} documents)
                        </h3>
                        {structure.length === 0 ? (
                            <div className="text-center py-12 text-gray-400">
                                <Folder size={48} className="mx-auto mb-2 opacity-30" />
                                <p className="text-sm">No documents uploaded</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-4 gap-4">
                                {structure.map((file, idx) => (
                                    <DocumentThumbnail
                                        key={idx}
                                        file={file}
                                        onClick={() => window.open(`${API_URL}${file.url}`, '_blank')}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Timeline Tab */}
                {activeTab === 'timeline' && (
                    <div className="bg-white rounded-xl border border-gray-200 p-6">
                        <h3 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
                            <History size={16} />
                            Audit Trail
                        </h3>
                        {history.length === 0 ? (
                            <div className="text-center py-12 text-gray-400">
                                <Clock size={48} className="mx-auto mb-2 opacity-30" />
                                <p className="text-sm">No history available</p>
                            </div>
                        ) : (
                            <div className="pl-4 border-l-2 border-gray-200">
                                {history.map((event, idx) => (
                                    <div key={idx} className="relative pb-6 last:pb-0">
                                        <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white border-2 border-blue-500" />
                                        <div className="pl-6">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`text-sm font-bold px-2 py-0.5 rounded ${
                                                    event.agent?.includes('CEO') ? 'bg-purple-100 text-purple-700' :
                                                    event.agent?.includes('AI') || event.agent?.includes('Analyst') ? 'bg-blue-100 text-blue-700' :
                                                    event.agent?.includes('DocGen') ? 'bg-yellow-100 text-yellow-700' :
                                                    event.agent?.includes('Underwriting') ? 'bg-orange-100 text-orange-700' :
                                                    event.agent?.includes('Human') || event.agent?.includes('Manager') ? 'bg-green-100 text-green-700' :
                                                    'bg-gray-100 text-gray-700'
                                                }`}>
                                                    {event.agent}
                                                </span>
                                                <span className="text-xs text-gray-400 font-mono">
                                                    {event.timestamp ? new Date(event.timestamp).toLocaleString() : '--'}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-600">{event.message}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Review Modal */}
            {reviewModal.open && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
                        <h3 className="text-xl font-bold text-gray-800 mb-2">
                            {reviewModal.approved ? "Approve Application" : "Reject Application"}
                        </h3>
                        <p className="text-gray-500 text-sm mb-4">
                            Please provide a reason for this decision.
                        </p>

                        <textarea
                            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none min-h-[100px]"
                            placeholder={reviewModal.approved ? "e.g., All criteria met, stable income verified..." : "e.g., Credit score below threshold..."}
                            value={reviewReason}
                            onChange={e => setReviewReason(e.target.value)}
                        ></textarea>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setReviewModal({ open: false, approved: false })}
                                className="flex-1 py-2 text-gray-600 font-medium hover:bg-gray-100 rounded-lg"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={submitReview}
                                className={`flex-1 py-2 text-white font-bold rounded-lg ${reviewModal.approved ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"}`}
                            >
                                Confirm
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
