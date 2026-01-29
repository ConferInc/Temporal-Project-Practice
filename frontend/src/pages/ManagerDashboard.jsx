import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import {
    Folder, FolderOpen, FileText, CheckCircle, XCircle,
    AlertTriangle, RefreshCw, Shield, Lock, Unlock,
    Database, Gavel, ExternalLink, Terminal, Activity,
    Users, Clock, TrendingUp, Archive, PenTool, ChevronRight
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

// =========================================
// PIPELINE STAGES (Encompass-style Folders)
// =========================================
const PIPELINE_STAGES = [
    { id: 'LEAD_CAPTURE', label: 'Lead Capture', icon: Users, color: 'blue' },
    { id: 'PROCESSING', label: 'Processing', icon: Activity, color: 'indigo' },
    { id: 'UNDERWRITING', label: 'Underwriting', icon: Gavel, color: 'orange' },
    { id: 'CLOSING', label: 'Closing', icon: PenTool, color: 'green' },
    { id: 'ARCHIVED', label: 'Archived', icon: Archive, color: 'gray' },
];

export default function ManagerDashboard() {
    // === STATE ===
    const [loanApplications, setLoanApplications] = useState([]);
    const [operationsSummary, setOperationsSummary] = useState(null);
    const [systemLogs, setSystemLogs] = useState([]);
    const [selectedStage, setSelectedStage] = useState(null); // null = show all
    const [selectedApp, setSelectedApp] = useState(null);
    const [details, setDetails] = useState(null);
    const [loadingDetails, setLoadingDetails] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [uwReason, setUwReason] = useState('');
    const [approvalReason, setApprovalReason] = useState('');

    // === DATA FETCHING ===
    const fetchAllData = async () => {
        await Promise.all([
            fetchLoanApplications(),
            fetchOperationsSummary(),
            fetchSystemLogs()
        ]);
    };

    const fetchLoanApplications = async () => {
        try {
            const res = await api.get('/loan-applications');
            setLoanApplications(res.data);
        } catch (err) {
            console.error("Loan applications fetch error:", err);
        }
    };

    const fetchOperationsSummary = async () => {
        try {
            const res = await api.get('/operations/summary');
            setOperationsSummary(res.data);
        } catch (err) {
            console.error("Operations summary fetch error:", err);
        }
    };

    const fetchSystemLogs = async () => {
        try {
            const res = await api.get('/recent_logs?limit=15');
            setSystemLogs(res.data);
        } catch (err) {
            console.error("System logs fetch error:", err);
        }
    };

    const fetchDetails = async (workflowId) => {
        setLoadingDetails(true);
        setDetails(null);
        try {
            const res = await api.get(`/status/${workflowId}`);
            setDetails(res.data);

            if (res.data.data?.public_urls) {
                const urls = res.data.data.public_urls;
                setSelectedDoc(urls.tax_document ? 'tax_document' : Object.keys(urls)[0]);
            }
        } catch (err) {
            console.warn("Details fetch failed:", err);
        } finally {
            setLoadingDetails(false);
        }
    };

    useEffect(() => {
        fetchAllData();
        const interval = setInterval(fetchAllData, 5000);
        return () => clearInterval(interval);
    }, []);

    // === HANDLERS ===
    const handleSelectApp = (app) => {
        setSelectedApp(app);
        setDetails(null);
        setSelectedDoc(null);
        fetchDetails(app.workflow_id);
    };

    const handleManagerApproval = async (approved) => {
        if (!selectedApp) return;
        try {
            await api.post('/review', {
                workflow_id: selectedApp.workflow_id,
                approved: approved,
                reason: approvalReason || (approved ? 'Approved by manager' : 'Rejected by manager')
            });
            setApprovalReason('');
            fetchAllData();
            fetchDetails(selectedApp.workflow_id);
        } catch (err) {
            alert("Action failed: " + err.message);
        }
    };

    const handleUnderwritingDecision = async (workflowId, approved) => {
        if (!uwReason.trim()) {
            alert("Please provide a reason for your underwriting decision.");
            return;
        }
        try {
            const res = await api.post('/underwriting/decision', {
                workflow_id: workflowId,
                approved: approved,
                reason: uwReason
            });
            setUwReason('');
            fetchAllData();

            // Show warning if signal failed but DB was updated
            if (res.data.warning) {
                alert(`Decision saved!\n\nNote: ${res.data.note}`);
            }

            if (selectedApp?.workflow_id === workflowId) {
                setSelectedApp(prev => ({
                    ...prev,
                    is_locked: false,
                    underwriting_decision: approved ? 'approved' : 'rejected'
                }));
            }
        } catch (err) {
            alert("Failed to submit decision: " + err.message);
        }
    };

    // === HELPERS ===
    const getStageCount = (stageId) => {
        return loanApplications.filter(app =>
            (app.loan_stage || 'LEAD_CAPTURE').toUpperCase() === stageId
        ).length;
    };

    const getFilteredApps = () => {
        if (!selectedStage) return loanApplications;
        return loanApplications.filter(app =>
            (app.loan_stage || 'LEAD_CAPTURE').toUpperCase() === selectedStage
        );
    };

    const getStageColor = (stageId) => {
        const stage = PIPELINE_STAGES.find(s => s.id === stageId);
        return stage?.color || 'gray';
    };

    const needsManagerApproval = (app) => {
        const status = (app?.status || '').toLowerCase();
        const stage = (app?.loan_stage || '').toUpperCase();
        return status === 'submitted' || stage === 'LEAD_CAPTURE';
    };

    const info = details?.data?.applicant_info || {};
    const analysis = details?.loan_metadata?.analysis || details?.data?.analysis || {};
    const urls = details?.data?.public_urls || {};

    return (
        <div className="flex h-[calc(100vh-64px)] bg-slate-900 overflow-hidden">
            {/* === LEFT SIDEBAR: PIPELINE FOLDERS === */}
            <div className="w-72 bg-slate-800 border-r border-slate-700 flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-slate-700">
                    <h1 className="text-white font-bold text-lg flex items-center gap-2">
                        <Database size={20} className="text-blue-400" />
                        Loan Pipeline
                    </h1>
                    <p className="text-slate-400 text-xs mt-1">Encompass-style Manager View</p>
                </div>

                {/* Stats Cards */}
                {operationsSummary && (
                    <div className="p-3 border-b border-slate-700">
                        <div className="grid grid-cols-3 gap-2">
                            <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                                <div className="text-xl font-bold text-blue-400">{operationsSummary.total_applications}</div>
                                <div className="text-[10px] text-slate-400 uppercase">Total</div>
                            </div>
                            <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                                <div className="text-xl font-bold text-orange-400">{operationsSummary.locked_waiting}</div>
                                <div className="text-[10px] text-slate-400 uppercase">Locked</div>
                            </div>
                            <div className="bg-slate-700/50 rounded-lg p-2 text-center">
                                <div className="text-xl font-bold text-green-400">{operationsSummary.funded}</div>
                                <div className="text-[10px] text-slate-400 uppercase">Funded</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Pipeline Folders */}
                <div className="flex-1 overflow-y-auto p-2">
                    {/* All Loans Option */}
                    <button
                        onClick={() => setSelectedStage(null)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all ${
                            selectedStage === null
                                ? 'bg-blue-600 text-white'
                                : 'text-slate-300 hover:bg-slate-700'
                        }`}
                    >
                        <Database size={18} />
                        <span className="flex-1 text-left font-medium">All Loans</span>
                        <span className="bg-slate-600 text-slate-200 text-xs px-2 py-0.5 rounded-full">
                            {loanApplications.length}
                        </span>
                    </button>

                    <div className="border-t border-slate-700 my-2"></div>

                    {/* Stage Folders */}
                    {PIPELINE_STAGES.map(stage => {
                        const Icon = stage.icon;
                        const count = getStageCount(stage.id);
                        const isSelected = selectedStage === stage.id;

                        return (
                            <button
                                key={stage.id}
                                onClick={() => setSelectedStage(stage.id)}
                                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all ${
                                    isSelected
                                        ? `bg-${stage.color}-600/20 text-${stage.color}-400 border border-${stage.color}-500/30`
                                        : 'text-slate-300 hover:bg-slate-700'
                                }`}
                            >
                                {isSelected ? <FolderOpen size={18} /> : <Folder size={18} />}
                                <span className="flex-1 text-left font-medium">{stage.label}</span>
                                <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    count > 0 ? 'bg-slate-600 text-slate-200' : 'text-slate-500'
                                }`}>
                                    {count}
                                </span>
                            </button>
                        );
                    })}
                </div>

                {/* System Logs Panel (Terminal Style) */}
                <div className="h-48 border-t border-slate-700 bg-slate-900/50">
                    <div className="p-2 border-b border-slate-700 flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-400 flex items-center gap-1">
                            <Terminal size={12} /> SYSTEM LOGS
                        </span>
                        <button onClick={fetchSystemLogs} className="text-slate-500 hover:text-slate-300">
                            <RefreshCw size={12} />
                        </button>
                    </div>
                    <div className="p-2 h-36 overflow-y-auto font-mono text-[10px]">
                        {systemLogs.length === 0 ? (
                            <div className="text-slate-500 text-center py-4">No recent activity</div>
                        ) : (
                            systemLogs.map((log, i) => (
                                <div key={i} className="text-slate-400 mb-1 flex gap-2">
                                    <span className="text-slate-600">[{log.timestamp?.slice(11, 19) || '??:??:??'}]</span>
                                    <span className="text-green-400">{log.agent || 'System'}</span>
                                    <span className="text-slate-300 truncate">{log.message}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* === MIDDLE: LOAN LIST === */}
            <div className="w-80 bg-white border-r flex flex-col">
                {/* Header */}
                <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                    <div>
                        <h2 className="font-bold text-gray-800">
                            {selectedStage ? PIPELINE_STAGES.find(s => s.id === selectedStage)?.label : 'All Loans'}
                        </h2>
                        <p className="text-xs text-gray-500">{getFilteredApps().length} applications</p>
                    </div>
                    <button onClick={fetchAllData} className="p-2 hover:bg-gray-200 rounded-full transition">
                        <RefreshCw size={16} className="text-gray-600" />
                    </button>
                </div>

                {/* Loan List */}
                <div className="flex-1 overflow-y-auto">
                    {getFilteredApps().length === 0 ? (
                        <div className="p-8 text-center text-gray-400">
                            <Folder size={40} className="mx-auto mb-2 opacity-30" />
                            <p>No loans in this stage</p>
                        </div>
                    ) : (
                        getFilteredApps().map(app => (
                            <div
                                key={app.id}
                                onClick={() => handleSelectApp(app)}
                                className={`p-4 border-b cursor-pointer transition-all hover:bg-gray-50 ${
                                    selectedApp?.id === app.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'
                                }`}
                            >
                                {/* Top Row: Name + Lock */}
                                <div className="flex justify-between items-start mb-2">
                                    <div className="font-bold text-gray-800">{app.borrower_name}</div>
                                    {app.is_locked && (
                                        <span className="flex items-center gap-1 text-[10px] font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                                            <Lock size={10} /> LOCKED
                                        </span>
                                    )}
                                </div>

                                {/* Amount + Stage */}
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm text-gray-600">${app.loan_amount?.toLocaleString() || 0}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded bg-${getStageColor(app.loan_stage?.toUpperCase())}-100 text-${getStageColor(app.loan_stage?.toUpperCase())}-700`}>
                                        {app.loan_stage || 'LEAD_CAPTURE'}
                                    </span>
                                </div>

                                {/* Status */}
                                <div className="flex items-center justify-between">
                                    <span className="text-xs text-gray-500">{app.status}</span>
                                    {app.underwriting_decision && (
                                        <span className={`text-xs font-bold ${
                                            app.underwriting_decision === 'approved' ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                            UW: {app.underwriting_decision.toUpperCase()}
                                        </span>
                                    )}
                                </div>

                                {/* DB ID */}
                                <div className="mt-2 font-mono text-[9px] text-gray-400">
                                    DB: {app.id?.slice(0, 8)}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* === RIGHT: DETAIL PANEL === */}
            <div className="flex-1 bg-gray-100 p-6 overflow-hidden flex flex-col">
                {selectedApp ? (
                    <div className="h-full flex gap-6">
                        {/* Left Column: Info & Actions */}
                        <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2">
                            {/* Header Card */}
                            <div className="bg-white p-6 rounded-xl shadow-sm border">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                            {selectedApp.borrower_name}
                                            {selectedApp.is_locked ? (
                                                <Lock className="text-orange-500" size={20} />
                                            ) : (
                                                <Unlock className="text-green-500" size={20} />
                                            )}
                                        </h1>
                                        <p className="text-gray-500 text-sm mt-1">{selectedApp.workflow_id}</p>
                                        <div className="flex gap-2 mt-3">
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold bg-${getStageColor(selectedApp.loan_stage?.toUpperCase())}-100 text-${getStageColor(selectedApp.loan_stage?.toUpperCase())}-700`}>
                                                {selectedApp.loan_stage || 'LEAD_CAPTURE'}
                                            </span>
                                            <span className="px-3 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
                                                {selectedApp.status}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-gray-800">
                                            ${selectedApp.loan_amount?.toLocaleString() || 0}
                                        </div>
                                        <div className="text-xs text-gray-500">Loan Amount</div>
                                    </div>
                                </div>
                            </div>

                            {/* GATE 1: Manager Approval */}
                            {needsManagerApproval(selectedApp) && (
                                <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 shadow-sm">
                                    <h3 className="text-lg font-bold text-blue-800 mb-3 flex items-center gap-2">
                                        <Users size={20} /> Initial Manager Review
                                    </h3>
                                    <p className="text-sm text-blue-700 mb-4">
                                        Review documents and AI analysis, then approve to proceed to Processing.
                                    </p>
                                    <textarea
                                        className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-blue-300"
                                        placeholder="Optional notes..."
                                        value={approvalReason}
                                        onChange={e => setApprovalReason(e.target.value)}
                                        rows={2}
                                    />
                                    <div className="flex gap-3">
                                        <button
                                            onClick={() => handleManagerApproval(true)}
                                            className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 flex items-center justify-center gap-2"
                                        >
                                            <CheckCircle size={18} /> Approve
                                        </button>
                                        <button
                                            onClick={() => handleManagerApproval(false)}
                                            className="flex-1 bg-white text-red-600 border-2 border-red-200 py-3 rounded-lg font-bold hover:bg-red-50 flex items-center justify-center gap-2"
                                        >
                                            <XCircle size={18} /> Reject
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* GATE 2: Underwriting Decision (When Locked) */}
                            {selectedApp.is_locked && (
                                <div className="bg-gradient-to-r from-orange-50 to-amber-50 border-2 border-orange-300 rounded-xl p-6 shadow-sm">
                                    <h3 className="text-lg font-bold text-orange-800 mb-3 flex items-center gap-2">
                                        <Gavel size={20} /> Underwriting Decision Required
                                    </h3>
                                    <div className="bg-white/80 p-4 rounded-lg border border-orange-200 mb-4">
                                        <div className="flex items-center gap-2 text-orange-700">
                                            <Lock size={16} />
                                            <span className="font-semibold">Workflow is PAUSED</span>
                                        </div>
                                        <p className="text-sm text-gray-600 mt-1">
                                            Your decision will unlock the workflow and send disclosures to the borrower.
                                        </p>
                                    </div>
                                    <textarea
                                        className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-orange-300"
                                        placeholder="Enter underwriting reason (e.g., 'Income verified, DTI 32%')..."
                                        value={uwReason}
                                        onChange={e => setUwReason(e.target.value)}
                                        rows={2}
                                    />
                                    <div className="flex gap-3">
                                        <button
                                            onClick={() => handleUnderwritingDecision(selectedApp.workflow_id, true)}
                                            className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 shadow-lg flex items-center justify-center gap-2"
                                        >
                                            <CheckCircle size={18} /> Approve & Send Disclosures
                                        </button>
                                        <button
                                            onClick={() => handleUnderwritingDecision(selectedApp.workflow_id, false)}
                                            className="flex-1 bg-white text-red-600 border-2 border-red-300 py-3 rounded-lg font-bold hover:bg-red-50 flex items-center justify-center gap-2"
                                        >
                                            <XCircle size={18} /> Reject
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Funded Success */}
                            {selectedApp.status?.toLowerCase().includes('funded') && (
                                <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6">
                                    <h3 className="text-lg font-bold text-green-800 flex items-center gap-2">
                                        <CheckCircle size={20} /> Loan Funded Successfully
                                    </h3>
                                    <p className="text-sm text-green-700 mt-2">
                                        This loan has completed the full lifecycle.
                                    </p>
                                </div>
                            )}

                            {/* AI Verification Analysis */}
                            <div className="bg-white p-6 rounded-xl shadow-sm border">
                                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                    <Shield size={20} className="text-blue-600" /> AI Verification Analysis
                                </h3>

                                {analysis.verified_income ? (
                                    <div className="space-y-4">
                                        <div className={`p-4 rounded-lg border ${
                                            analysis.income_mismatch ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
                                        }`}>
                                            <div className="flex justify-between items-center mb-3">
                                                <span className="font-bold text-gray-700">Income Verification</span>
                                                {analysis.income_mismatch ? (
                                                    <span className="text-red-600 text-xs font-bold flex items-center gap-1">
                                                        <AlertTriangle size={12} /> MISMATCH
                                                    </span>
                                                ) : (
                                                    <span className="text-green-600 text-xs font-bold flex items-center gap-1">
                                                        <CheckCircle size={12} /> VERIFIED
                                                    </span>
                                                )}
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <div className="text-xs text-gray-500">Stated</div>
                                                    <div className="text-xl font-bold">${(analysis.stated_income || 0).toLocaleString()}</div>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-gray-500">Verified</div>
                                                    <div className="text-xl font-bold">${(analysis.verified_income || 0).toLocaleString()}</div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="p-4 rounded-lg bg-gray-50 border">
                                            <div className="flex justify-between items-center">
                                                <span className="font-bold text-gray-700">AI Confidence</span>
                                                <span className={`text-xl font-bold ${
                                                    (analysis.confidence || 0) > 0.8 ? 'text-green-600' : 'text-yellow-600'
                                                }`}>
                                                    {((analysis.confidence || 0) * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-6 bg-gray-50 rounded-lg text-center text-gray-400">
                                        <Shield size={32} className="mx-auto mb-2 opacity-30" />
                                        <p>AI analysis pending...</p>
                                    </div>
                                )}
                            </div>

                            {/* DB Record Info */}
                            <div className="bg-slate-800 text-white p-4 rounded-xl">
                                <h3 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                                    <Database size={14} /> Database Record
                                </h3>
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    <div>
                                        <span className="text-slate-400">DB ID:</span>
                                        <span className="ml-2 font-mono text-xs text-blue-400">{selectedApp.id?.slice(0, 12)}...</span>
                                    </div>
                                    <div>
                                        <span className="text-slate-400">Lock:</span>
                                        <span className="ml-2">{selectedApp.is_locked ? '🔒 Locked' : '🔓 Unlocked'}</span>
                                    </div>
                                    <div>
                                        <span className="text-slate-400">Stage:</span>
                                        <span className="ml-2">{selectedApp.loan_stage || 'LEAD_CAPTURE'}</span>
                                    </div>
                                    <div>
                                        <span className="text-slate-400">UW:</span>
                                        <span className={`ml-2 font-bold ${
                                            selectedApp.underwriting_decision === 'approved' ? 'text-green-400' :
                                            selectedApp.underwriting_decision === 'rejected' ? 'text-red-400' : 'text-gray-400'
                                        }`}>
                                            {selectedApp.underwriting_decision?.toUpperCase() || 'Pending'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Right Column: Document Viewer */}
                        <div className="w-[450px] bg-white rounded-xl shadow-lg border flex flex-col overflow-hidden">
                            <div className="p-3 bg-gray-100 border-b flex justify-between items-center">
                                <div className="flex gap-1 flex-wrap">
                                    {Object.keys(urls).length > 0 ? (
                                        Object.keys(urls).map(key => (
                                            <button
                                                key={key}
                                                onClick={() => setSelectedDoc(key)}
                                                className={`px-3 py-1.5 text-xs font-bold rounded-md transition capitalize ${
                                                    selectedDoc === key ? 'bg-white text-blue-600 shadow' : 'text-gray-500 hover:bg-gray-200'
                                                }`}
                                            >
                                                {key.replace('_document', '').replace('_', ' ')}
                                            </button>
                                        ))
                                    ) : (
                                        <span className="text-xs text-gray-500 px-2">Documents</span>
                                    )}
                                </div>
                                {selectedDoc && urls[selectedDoc] && (
                                    <a
                                        href={`${API_URL}${urls[selectedDoc]}`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-gray-400 hover:text-blue-600"
                                    >
                                        <ExternalLink size={16} />
                                    </a>
                                )}
                            </div>

                            {selectedDoc && urls[selectedDoc] ? (
                                <iframe
                                    src={`${API_URL}${urls[selectedDoc]}`}
                                    className="flex-1 w-full bg-slate-50"
                                    title="Document Viewer"
                                />
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center text-gray-300">
                                    <FileText size={48} className="mb-4 opacity-20" />
                                    <p>Select a document to preview</p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    /* Empty State */
                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        {loadingDetails ? (
                            <RefreshCw className="animate-spin mb-4" size={48} />
                        ) : (
                            <>
                                <Folder size={64} className="mb-6 opacity-10" />
                                <h2 className="text-xl font-bold text-gray-600">Loan Pipeline Manager</h2>
                                <p className="text-gray-500 max-w-sm mt-2 text-center">
                                    Select a pipeline stage from the left sidebar, then choose a loan to review.
                                </p>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
