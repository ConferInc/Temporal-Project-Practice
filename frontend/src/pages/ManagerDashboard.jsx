import React, { useEffect, useState } from 'react';
import api from '../utils/api';
import {
    LayoutDashboard, FileText, CheckCircle, XCircle,
    AlertTriangle, Trash2, ExternalLink, RefreshCw,
    Shield, DollarSign, User
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

export default function ManagerDashboard() {
    const [applications, setApplications] = useState([]);
    const [selectedApp, setSelectedApp] = useState(null);
    const [details, setDetails] = useState(null);
    const [loadingDetails, setLoadingDetails] = useState(false);
    const [selectedDoc, setSelectedDoc] = useState(null); // 'id_document', 'tax_document', 'pay_stub'

    const fetchApplications = async () => {
        try {
            const res = await api.get('/applications');
            setApplications(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchApplications();
        const interval = setInterval(fetchApplications, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const fetchDetails = async (id) => {
        setLoadingDetails(true);
        try {
            const res = await api.get(`/status/${id}`);
            setDetails(res.data);

            // Set default document to view (e.g., Tax Return)
            if (res.data.data?.public_urls) {
                // Default to tax_document if available, otherwise first available
                const urls = res.data.data.public_urls;
                setSelectedDoc(urls.tax_document ? 'tax_document' : Object.keys(urls)[0]);
            } else if (res.data.file_url) {
                // Fallback for legacy single-file data
                setSelectedDoc('legacy');
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingDetails(false);
        }
    };

    const handleSelectApp = (app) => {
        setSelectedApp(app);
        setDetails(null);
        setSelectedDoc(null);
        fetchDetails(app.workflow_id);
    };

    const handleAction = async (approved) => {
        if (!details) return;
        try {
            await api.post('/review', {
                workflow_id: details.workflow_id,
                approved: approved
            });
            fetchDetails(details.workflow_id); // Refresh
        } catch (err) {
            alert("Action failed: " + err.message);
        }
    };

    const handleDelete = async (appId) => {
        if (!confirm("Are you sure you want to DELETE this application? This cannot be undone.")) return;
        try {
            await api.delete(`/application/${appId}`);
            setDetails(null);
            setSelectedApp(null);
            fetchApplications();
        } catch (err) {
            alert("Delete failed");
        }
    }

    const getStatusColor = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved")) return "bg-green-100 text-green-800 border-green-200";
        if (s.includes("rejected") || s.includes("fail") || s.includes("high risk")) return "bg-red-100 text-red-800 border-red-200";
        if (s.includes("flagged") || s.includes("mismatch")) return "bg-orange-100 text-orange-800 border-orange-200";
        if (s.includes("review") || s.includes("wait")) return "bg-yellow-100 text-yellow-800 border-yellow-200";
        return "bg-blue-100 text-blue-800 border-blue-200";
    };

    // Helper to extract data safely
    const info = details?.data?.applicant_info || {};
    const verify = details?.data?.verification || {};
    const urls = details?.data?.public_urls || {};
    // Backward compatibility for legacy single-file apps
    const legacyUrl = details?.file_url;
    // Fallback name logic
    const applicantName = info.name || details?.data?.applicant_name || "Unknown Applicant";
    const annualIncome = info.stated_income || details?.data?.annual_income || 0;
    // Handle both DB model and Temporal response formats if they differ slightly
    // Note: The /applications endpoint now returns DB model created_at instead of Temporal start_time
    const appDate = selectedApp?.created_at || selectedApp?.start_time;

    const creditScore = verify.credit_score || details?.data?.credit_score || 0;

    return (
        <div className="flex h-[calc(100vh-64px)] bg-gray-50 overflow-hidden">
            {/* SIDEBAR LIST */}
            <div className="w-1/3 max-w-md bg-white border-r flex flex-col shadow-lg z-10">
                <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                    <h2 className="font-bold text-gray-700 flex items-center gap-2">
                        <LayoutDashboard size={20} /> Applications
                    </h2>
                    <button onClick={fetchApplications} className="p-2 hover:bg-gray-200 rounded-full transition" title="Refresh List">
                        <RefreshCw size={16} />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {applications.length === 0 ? (
                        <div className="p-8 text-center text-gray-400">
                            No active applications
                        </div>
                    ) : (
                        applications.map((app) => (
                            <div
                                key={app.workflow_id}
                                onClick={() => handleSelectApp(app)}
                                className={`p-4 border-b cursor-pointer transition-all hover:bg-gray-50 group
                                    ${selectedApp?.workflow_id === app.workflow_id ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'}
                                `}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <span className="font-mono text-xs text-gray-500 truncate w-32" title={app.workflow_id}>
                                        {app.workflow_id.split('-').slice(-1)[0]}...
                                    </span>
                                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleDelete(app.workflow_id); }}
                                            className="text-red-400 hover:text-red-600"
                                            title="Delete Application"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                                <div className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-2 ${getStatusColor(app.status)}`}>
                                    {app.status}
                                </div>
                                <div className="text-xs text-gray-400 flex items-center gap-1">
                                    <RefreshCw size={10} />
                                    {/* Use created_at if available (DB), else fallback */}
                                    {new Date(app.created_at || app.start_time).toLocaleDateString()}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* MAIN CONTENT */}
            <div className="flex-1 bg-gray-50 p-6 overflow-hidden flex flex-col">
                {selectedApp && details ? (
                    <div className="h-full flex gap-6">
                        {/* LEFT: INFO & VERIFICATION */}
                        <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2">
                            {/* HEADER */}
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                                            {applicantName}
                                            <span className={`text-sm px-2 py-1 rounded-full ${getStatusColor(details.status)}`}>
                                                {details.status}
                                            </span>
                                        </h1>
                                        <p className="text-gray-500 text-sm mt-1 flex items-center gap-2">
                                            <FileText size={14} /> Workflow ID: {details.workflow_id}
                                        </p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleAction(true)}
                                            className="bg-green-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-green-700 shadow-sm flex items-center gap-2"
                                        >
                                            <CheckCircle size={18} /> Approve
                                        </button>
                                        <button
                                            onClick={() => handleAction(false)}
                                            className="bg-red-50 text-red-600 border border-red-100 px-4 py-2 rounded-lg font-bold hover:bg-red-100 flex items-center gap-2"
                                        >
                                            <XCircle size={18} /> Reject
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* ANALYSIS CARD */}
                            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                                    <Shield size={20} className="text-blue-600" /> AI Verification Analysis
                                </h3>

                                {details.data?.verification ? (
                                    <div className="grid grid-cols-2 gap-6">
                                        {/* INCOME CHECK */}
                                        <div className={`p-4 rounded-lg border ${verify.income_match ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                                            <p className="text-xs font-bold uppercase tracking-wider mb-2 opacity-70">Income Verification</p>
                                            <div className="flex justify-between items-end mb-2">
                                                <div>
                                                    <p className="text-sm text-gray-500">Stated</p>
                                                    <p className="text-lg font-semibold">${parseFloat(annualIncome).toLocaleString()}</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-sm text-gray-500">Tax Verified</p>
                                                    <p className="text-lg font-semibold">${verify.verified_income?.toLocaleString()}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 font-bold text-sm">
                                                {verify.income_match ? (
                                                    <span className="text-green-700 flex items-center gap-1"><CheckCircle size={14} /> Verified Match</span>
                                                ) : (
                                                    <span className="text-red-700 flex items-center gap-1"><AlertTriangle size={14} /> Mismatch Detected</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* INFO GRID */}
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="p-3 bg-gray-50 rounded border">
                                                <p className="text-xs text-gray-500">Credit Score</p>
                                                <p className={`text-xl font-bold ${creditScore >= 720 ? 'text-green-600' : 'text-yellow-600'}`}>
                                                    {creditScore || "N/A"}
                                                </p>
                                            </div>
                                            <div className="p-3 bg-gray-50 rounded border">
                                                <p className="text-xs text-gray-500">SSN</p>
                                                <p className="text-xl font-mono text-gray-700">***-**-{info.ssn || "****"}</p>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    /* LEGACY / SIMPLE VIEW */
                                    <div className="p-4 bg-gray-50 rounded-lg border">
                                        <p className="text-sm text-gray-500 italic">Legacy application data format.</p>
                                        <div className="mt-2 grid grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-xs text-gray-500">Income</p>
                                                <p className="font-bold">${annualIncome.toLocaleString()}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs text-gray-500">Credit Score</p>
                                                <p className="font-bold">{creditScore}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* RIGHT: PDF VIEWER */}
                        <div className="w-[500px] bg-white rounded-xl shadow-lg border border-gray-200 flex flex-col overflow-hidden">
                            <div className="p-3 bg-gray-100 border-b flex justify-between items-center">
                                <div className="flex gap-2">
                                    {Object.keys(urls).length > 0 ? (
                                        Object.keys(urls).map(key => (
                                            <button
                                                key={key}
                                                onClick={() => setSelectedDoc(key)}
                                                className={`px-3 py-1.5 text-xs font-bold rounded-md transition capitalize
                                                    ${selectedDoc === key ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}
                                                `}
                                            >
                                                {key.replace('_document', '').replace('_', ' ')}
                                            </button>
                                        ))
                                    ) : (
                                        <span className="text-xs font-bold text-gray-500 px-2">Document Preview</span>
                                    )}
                                </div>
                                {(selectedDoc && (urls[selectedDoc] || legacyUrl)) && (
                                    <a
                                        href={`${API_URL}${urls[selectedDoc] || legacyUrl}`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-gray-400 hover:text-blue-600 p-1"
                                        title="Open in new tab"
                                    >
                                        <ExternalLink size={16} />
                                    </a>
                                )}
                            </div>

                            {(selectedDoc && (urls[selectedDoc] || (selectedDoc === 'legacy' && legacyUrl))) ? (
                                <iframe
                                    src={`${API_URL}${urls[selectedDoc] || legacyUrl}`}
                                    className="flex-1 w-full h-full bg-slate-50"
                                    title="Document Viewer"
                                />
                            ) : (
                                <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
                                    <FileText size={48} className="mb-4 opacity-20" />
                                    <p>Select a document to preview</p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    /* EMPTY STATE */
                    <div className="h-full flex flex-col items-center justify-center text-center">
                        <div className="w-24 h-24 bg-blue-50 rounded-full flex items-center justify-center mb-6">
                            {loadingDetails ? <RefreshCw className="animate-spin text-blue-400" size={40} /> : <LayoutDashboard className="text-blue-300" size={40} />}
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">
                            {loadingDetails ? "Loading application..." : "Manager Dashboard"}
                        </h2>
                        <p className="text-gray-500 max-w-sm mt-2">
                            Select an application from the sidebar to view analysis, documents, and make logic decisions.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
