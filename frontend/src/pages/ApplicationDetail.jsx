import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import {
    FileText, CheckCircle, XCircle, AlertTriangle,
    Folder, File, Clock, ArrowLeft, RefreshCw,
    Shield, User, FolderOpen
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

export default function ApplicationDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth(); // Get current user

    const [details, setDetails] = useState(null);
    const [structure, setStructure] = useState([]);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Review Modal State
    const [reviewModal, setReviewModal] = useState({ open: false, approved: false });
    const [reviewReason, setReviewReason] = useState("");

    const fetchData = async () => {
        try {
            // Fetch Status (Critical)
            const statusRes = await api.get(`/status/${id}`);
            setDetails(statusRes.data);

            // Fetch Structure (Non-Critical)
            try {
                const structRes = await api.get(`/applications/${id}/structure`);
                setStructure(structRes.data || []);
            } catch (e) {
                console.warn("Structure fetch failed:", e);
                setStructure([]);
            }

            // Fetch History (Non-Critical)
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
        // Poll for history updates
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
        <div className="h-screen flex items-center justify-center">
            <RefreshCw className="animate-spin text-green-600" size={32} />
        </div>
    );

    if (error) return (
        <div className="p-8 text-center text-red-600">
            <AlertTriangle className="mx-auto mb-4" size={48} />
            <p>{error}</p>
            <button onClick={() => navigate('/manager')} className="mt-4 text-blue-600 underline">
                Back to Dashboard
            </button>
        </div>
    );

    // Helpers
    const info = details?.data?.applicant_info || {};
    const verify = details?.data?.verification || {};
    const status = details?.status || "Unknown";
    const statusColor =
        status.includes("Approved") ? "text-green-600 bg-green-50 border-green-200" :
            status.includes("Rejected") ? "text-red-600 bg-red-50 border-red-200" :
                status.includes("Review") ? "text-yellow-600 bg-yellow-50 border-yellow-200" : "text-blue-600 bg-blue-50 border-blue-200";

    return (
        <div className="min-h-[calc(100vh-64px)] bg-gray-100 p-4">
            {/* Top Bar */}
            <div className="mb-4 flex justify-between items-center">
                <button onClick={() => navigate('/manager')} className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium">
                    <ArrowLeft size={20} /> Back to Dashboard
                </button>
                <div className="flex items-center gap-4">
                    {/* Decision Reason Display if Available */}
                    {details?.decision_reason && (
                        <div className="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-full font-medium">
                            Note: {details.decision_reason}
                        </div>
                    )}
                    <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                        Application: <span className="font-mono text-gray-500">{id}</span>
                    </h1>
                </div>
            </div>

            {/* 3-Column Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">

                {/* COL 1: OVERVIEW & ACTIONS */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col overflow-hidden">
                    <div className="p-4 border-b bg-gray-50 flex items-center gap-2 font-bold text-gray-700">
                        <User size={18} /> Applicant Overview
                    </div>
                    <div className="p-6 overflow-y-auto flex-1 space-y-6">
                        {/* Status Card */}
                        <div className={`p-4 rounded-lg border text-center ${statusColor}`}>
                            <p className="text-xs font-bold uppercase tracking-wider mb-1">Current Status</p>
                            <p className="text-2xl font-bold">{status}</p>
                        </div>

                        {/* Details */}
                        <div className="space-y-3">
                            <div>
                                <label className="text-xs text-gray-500 font-bold uppercase">Name</label>
                                <p className="text-lg font-medium text-gray-900">{info.name || "N/A"}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 font-bold uppercase">Email</label>
                                <p className="text-gray-700">{info.email || "N/A"}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 font-bold uppercase">Stated Income</label>
                                <p className="font-mono text-gray-700">${info.stated_income}</p>
                            </div>
                            <div>
                                <label className="text-xs text-gray-500 font-bold uppercase">SSN</label>
                                <p className="font-mono text-gray-700">***-**-{info.ssn || "****"}</p>
                            </div>
                        </div>

                        <hr />

                        {/* AI Analysis */}
                        <div>
                            <h3 className="flex items-center gap-2 font-bold text-gray-800 mb-3">
                                <Shield size={16} className="text-blue-500" /> AI Verification
                            </h3>
                            {verify.credit_score ? (
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Credit Score</span>
                                        <span className={verify.credit_score >= 620 ? "text-green-600 font-bold" : "text-red-600 font-bold"}>
                                            {verify.credit_score}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Verified Income</span>
                                        <span className="font-mono">${verify.verified_income?.toLocaleString()}</span>
                                    </div>
                                    <div className={`flex items-center gap-2 p-2 rounded ${verify.income_match ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                                        {verify.income_match ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                                        <span className="font-medium">{verify.income_match ? "Income Matches" : "Income Mismatch"}</span>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-gray-400 italic text-sm">Pending Analysis...</p>
                            )}
                        </div>
                    </div>
                    {/* Actions Footer - Only for Managers */}
                    {user?.role === 'manager' && (
                        <div className="p-4 border-t bg-gray-50 flex gap-3">
                            <button onClick={() => openReviewModal(true)} className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg font-bold flex justify-center items-center gap-2 transition">
                                <CheckCircle size={18} /> Approve
                            </button>
                            <button onClick={() => openReviewModal(false)} className="flex-1 bg-white border border-red-200 text-red-600 hover:bg-red-50 py-2 rounded-lg font-bold flex justify-center items-center gap-2 transition">
                                <XCircle size={18} /> Reject
                            </button>
                        </div>
                    )}
                </div>

                {/* COL 2: FILE SYSTEM */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col overflow-hidden">
                    <div className="p-4 border-b bg-gray-50 flex items-center gap-2 font-bold text-gray-700">
                        <FolderOpen size={18} /> Application Files
                    </div>
                    <div className="p-2 overflow-y-auto flex-1">
                        {structure.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-gray-400">
                                <Folder size={48} className="mb-2 opacity-20" />
                                <p>No files found</p>
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {structure.map((file, idx) => (
                                    <a
                                        key={idx}
                                        href={`${API_URL}${file.url}`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="flex items-center gap-3 p-3 hover:bg-blue-50 rounded-lg group transition border border-transparent hover:border-blue-100"
                                    >
                                        <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition">
                                            <FileText size={20} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-gray-800 truncate">{file.name}</p>
                                            <p className="text-xs text-gray-400">PDF Document</p>
                                        </div>
                                    </a>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* COL 3: AGENT LOG (Timeline) */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col overflow-hidden">
                    <div className="p-4 border-b bg-gray-50 flex items-center gap-2 font-bold text-gray-700">
                        <Clock size={18} /> Agent Narrative
                    </div>
                    <div className="p-4 overflow-y-auto flex-1 bg-gray-50/50">
                        {history.length === 0 ? (
                            <div className="mt-10 text-center text-gray-400">
                                <p>No history available</p>
                            </div>
                        ) : (
                            <div className="pl-2">
                                {history.map((event, idx) => (
                                    <div key={idx} className="relative pb-8 pl-8 border-l-2 border-blue-100 last:border-0 last:pb-0 group">
                                        {/* Icon */}
                                        <div className="absolute -left-[9px] top-0 w-5 h-5 rounded-full bg-blue-50 border-2 border-blue-500 flex items-center justify-center">
                                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                                        </div>

                                        {/* Content */}
                                        <div className="-mt-1.5">
                                            <p className="text-xs text-gray-400 font-mono mb-1">
                                                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '--:--:--'}
                                            </p>
                                            <p className="text-sm font-bold text-gray-800">{event.agent}</p>
                                            <p className="text-sm text-gray-600 mt-0.5">{event.message}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Review Modal */}
            {reviewModal.open && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
                        <h3 className="text-xl font-bold text-gray-800 mb-2">
                            {reviewModal.approved ? "Approve Application" : "Reject Application"}
                        </h3>
                        <p className="text-gray-500 text-sm mb-4">
                            Please provide a reason for this decision. This will be visible to the applicant.
                        </p>

                        <textarea
                            className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none min-h-[100px]"
                            placeholder={reviewModal.approved ? "e.g., Criteria met, reliable income..." : "e.g., Credit score below minimum..."}
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
                                Confirm Decision
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
