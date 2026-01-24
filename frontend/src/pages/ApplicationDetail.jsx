import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import {
    FileText, CheckCircle, XCircle, AlertTriangle,
    Folder, Clock, ArrowLeft, RefreshCw, Save,
    FolderOpen, History, Edit3, Eye, Download
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

// Tab configuration
const TABS = [
    { key: 'forms', label: 'Forms', icon: Edit3 },
    { key: 'efolder', label: 'eFolder', icon: FolderOpen },
    { key: 'log', label: 'Log', icon: History },
];

// Form fields configuration for Encompass-style editing
const FORM_FIELDS = [
    { key: 'name', label: 'Borrower Name', type: 'text', section: 'Borrower Information' },
    { key: 'email', label: 'Email Address', type: 'email', section: 'Borrower Information' },
    { key: 'ssn', label: 'SSN', type: 'text', section: 'Borrower Information' },
    { key: 'stated_income', label: 'Stated Income', type: 'text', section: 'Financial Information' },
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
    const [activeTab, setActiveTab] = useState('forms');

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

            // Initialize form data from applicant_info
            const info = statusRes.data?.data?.applicant_info || {};
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

    const info = details?.data?.applicant_info || formData;
    const verify = details?.data?.verification || {};
    const status = details?.status || "Unknown";
    const loanStage = details?.loan_stage || "LEAD_CAPTURE";

    const getStatusBadgeColor = () => {
        const s = status.toLowerCase();
        if (s.includes("approved")) return "bg-green-500";
        if (s.includes("rejected") || s.includes("fail")) return "bg-red-500";
        if (s.includes("review")) return "bg-yellow-500";
        return "bg-blue-500";
    };

    // Group form fields by section
    const groupedFields = FORM_FIELDS.reduce((acc, field) => {
        if (!acc[field.section]) acc[field.section] = [];
        acc[field.section].push(field);
        return acc;
    }, {});

    return (
        <div className="h-[calc(100vh-64px)] bg-gray-100 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/manager')}
                        className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition"
                    >
                        <ArrowLeft size={18} />
                    </button>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-gray-900">{info.name || 'Borrower'}</span>
                            <span className={`px-2 py-0.5 text-xs text-white font-medium rounded ${getStatusBadgeColor()}`}>
                                {status}
                            </span>
                            <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                {loanStage}
                            </span>
                        </div>
                        <div className="text-xs text-gray-500 font-mono">{id}</div>
                    </div>
                </div>
                <button
                    onClick={fetchData}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition"
                >
                    <RefreshCw size={16} />
                </button>
            </div>

            {/* Tab Bar */}
            <div className="bg-white border-b border-gray-200 px-4 flex">
                {TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.key;
                    return (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition ${
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
            <div className="flex-1 overflow-y-auto p-4">
                {/* Forms Tab */}
                {activeTab === 'forms' && (
                    <div className="max-w-4xl mx-auto space-y-4">
                        {Object.entries(groupedFields).map(([section, fields]) => (
                            <div key={section} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                                    <h3 className="text-sm font-bold text-gray-700">{section}</h3>
                                </div>
                                <div className="divide-y divide-gray-100">
                                    {fields.map((field) => (
                                        <div key={field.key} className="flex items-center px-4 py-2 hover:bg-gray-50">
                                            <label className="w-40 text-xs font-medium text-gray-500 uppercase tracking-wide">
                                                {field.label}
                                            </label>
                                            <div className="flex-1 flex items-center gap-2">
                                                {editingField === field.key ? (
                                                    <>
                                                        <input
                                                            type={field.type}
                                                            value={formData[field.key] || ''}
                                                            onChange={(e) => handleFieldChange(field.key, e.target.value)}
                                                            className="flex-1 px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                            autoFocus
                                                        />
                                                        <button
                                                            onClick={() => saveField(field.key)}
                                                            disabled={saving}
                                                            className="p-1.5 text-green-600 hover:bg-green-50 rounded disabled:opacity-50"
                                                        >
                                                            <Save size={14} />
                                                        </button>
                                                        <button
                                                            onClick={() => setEditingField(null)}
                                                            className="p-1.5 text-gray-400 hover:bg-gray-100 rounded"
                                                        >
                                                            <XCircle size={14} />
                                                        </button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <span className="flex-1 text-sm text-gray-900">
                                                            {field.key === 'ssn'
                                                                ? `***-**-${(formData[field.key] || '').slice(-4)}`
                                                                : formData[field.key] || '-'
                                                            }
                                                        </span>
                                                        {user?.role === 'manager' && (
                                                            <button
                                                                onClick={() => setEditingField(field.key)}
                                                                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded opacity-0 group-hover:opacity-100 transition"
                                                            >
                                                                <Edit3 size={14} />
                                                            </button>
                                                        )}
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}

                        {/* AI Verification Section */}
                        {verify.credit_score && (
                            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                                    <h3 className="text-sm font-bold text-gray-700">AI Verification Results</h3>
                                </div>
                                <div className="p-4 grid grid-cols-3 gap-4">
                                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                                        <div className={`text-2xl font-bold ${verify.credit_score >= 620 ? 'text-green-600' : 'text-red-600'}`}>
                                            {verify.credit_score}
                                        </div>
                                        <div className="text-xs text-gray-500 uppercase mt-1">Credit Score</div>
                                    </div>
                                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                                        <div className="text-2xl font-bold text-gray-900 font-mono">
                                            ${verify.verified_income?.toLocaleString() || '0'}
                                        </div>
                                        <div className="text-xs text-gray-500 uppercase mt-1">Verified Income</div>
                                    </div>
                                    <div className={`text-center p-3 rounded-lg ${verify.income_match ? 'bg-green-50' : 'bg-red-50'}`}>
                                        <div className={`text-lg font-bold ${verify.income_match ? 'text-green-600' : 'text-red-600'}`}>
                                            {verify.income_match ? <CheckCircle size={28} className="mx-auto" /> : <XCircle size={28} className="mx-auto" />}
                                        </div>
                                        <div className="text-xs text-gray-500 uppercase mt-1">Income Match</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* eFolder Tab */}
                {activeTab === 'efolder' && (
                    <div className="max-w-4xl mx-auto">
                        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                                <h3 className="text-sm font-bold text-gray-700">Documents</h3>
                                <span className="text-xs text-gray-500">{structure.length} files</span>
                            </div>
                            {structure.length === 0 ? (
                                <div className="p-12 text-center text-gray-400">
                                    <Folder size={48} className="mx-auto mb-2 opacity-30" />
                                    <p className="text-sm">No documents uploaded</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-100">
                                    {structure.map((file, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center px-4 py-3 hover:bg-gray-50 group"
                                        >
                                            <div className="w-10 h-10 bg-blue-50 text-blue-500 rounded flex items-center justify-center mr-3">
                                                <FileText size={20} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                                                <p className="text-xs text-gray-500">PDF Document</p>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                                                    Uploaded
                                                </span>
                                                <a
                                                    href={`${API_URL}${file.url}`}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                                                    title="View Document"
                                                >
                                                    <Eye size={16} />
                                                </a>
                                                <a
                                                    href={`${API_URL}${file.url}`}
                                                    download
                                                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                                                    title="Download"
                                                >
                                                    <Download size={16} />
                                                </a>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Log Tab */}
                {activeTab === 'log' && (
                    <div className="max-w-4xl mx-auto">
                        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
                                <h3 className="text-sm font-bold text-gray-700">Audit Trail</h3>
                            </div>
                            {history.length === 0 ? (
                                <div className="p-12 text-center text-gray-400">
                                    <Clock size={48} className="mx-auto mb-2 opacity-30" />
                                    <p className="text-sm">No history available</p>
                                </div>
                            ) : (
                                <div className="p-4">
                                    <div className="pl-4 border-l-2 border-gray-200">
                                        {history.map((event, idx) => (
                                            <div key={idx} className="relative pb-6 last:pb-0">
                                                {/* Timeline dot */}
                                                <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white border-2 border-blue-500" />

                                                <div className="pl-6">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="text-sm font-bold text-gray-800">{event.agent}</span>
                                                        <span className="text-xs text-gray-400 font-mono">
                                                            {event.timestamp ? new Date(event.timestamp).toLocaleString() : '--'}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-600">{event.message}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Floating Action Bar - Manager Only */}
            {user?.role === 'manager' && (
                <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-between shadow-lg">
                    <div className="text-sm text-gray-500">
                        {details?.decision_reason && (
                            <span>Decision Note: <span className="text-gray-700">{details.decision_reason}</span></span>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => openReviewModal(true)}
                            className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg transition shadow-sm"
                        >
                            <CheckCircle size={18} /> Approve
                        </button>
                        <button
                            onClick={() => openReviewModal(false)}
                            className="flex items-center gap-2 px-6 py-2 bg-white border border-red-300 text-red-600 hover:bg-red-50 font-bold rounded-lg transition"
                        >
                            <XCircle size={18} /> Reject
                        </button>
                    </div>
                </div>
            )}

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
