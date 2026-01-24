import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import {
    LayoutDashboard, RefreshCw, Trash2, Calendar,
    FolderOpen, FileText, CheckSquare, History,
    ChevronRight, Users, Clock, CheckCircle, XCircle, AlertTriangle
} from 'lucide-react';

const PIPELINE_STAGES = [
    { key: 'all', label: 'All Applications', icon: FolderOpen },
    { key: 'LEAD_CAPTURE', label: 'Lead Capture', icon: Users },
    { key: 'PROCESSING', label: 'Processing', icon: Clock },
    { key: 'UNDERWRITING', label: 'Underwriting', icon: FileText },
    { key: 'CLOSING', label: 'Closing', icon: CheckSquare },
    { key: 'ARCHIVED', label: 'Archived', icon: History },
];

export default function ManagerDashboard() {
    const [applications, setApplications] = useState([]);
    const [selectedStage, setSelectedStage] = useState('all');
    const [selectedApp, setSelectedApp] = useState(null);
    const navigate = useNavigate();

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
        const interval = setInterval(fetchApplications, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleDelete = async (e, appId) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to DELETE this application? This cannot be undone.")) return;
        try {
            await api.delete(`/application/${appId}`);
            fetchApplications();
            if (selectedApp?.workflow_id === appId) setSelectedApp(null);
        } catch (err) {
            alert("Delete failed");
        }
    };

    const getStatusIcon = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved")) return <CheckCircle size={14} className="text-green-600" />;
        if (s.includes("rejected") || s.includes("fail")) return <XCircle size={14} className="text-red-600" />;
        if (s.includes("flagged") || s.includes("mismatch")) return <AlertTriangle size={14} className="text-orange-500" />;
        return <Clock size={14} className="text-blue-500" />;
    };

    const getStatusColor = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved")) return "bg-green-50 border-green-200 text-green-700";
        if (s.includes("rejected") || s.includes("fail")) return "bg-red-50 border-red-200 text-red-700";
        if (s.includes("flagged") || s.includes("mismatch")) return "bg-orange-50 border-orange-200 text-orange-700";
        return "bg-blue-50 border-blue-200 text-blue-700";
    };

    // Filter applications by stage
    const filteredApps = selectedStage === 'all'
        ? applications
        : applications.filter(app => app.loan_stage === selectedStage);

    // Count by stage
    const stageCounts = PIPELINE_STAGES.reduce((acc, stage) => {
        if (stage.key === 'all') {
            acc[stage.key] = applications.length;
        } else {
            acc[stage.key] = applications.filter(app => app.loan_stage === stage.key).length;
        }
        return acc;
    }, {});

    return (
        <div className="h-[calc(100vh-64px)] bg-gray-100 flex">
            {/* Sidebar - Pipeline View */}
            <div className="w-56 bg-white border-r border-gray-200 flex flex-col">
                <div className="p-3 border-b border-gray-100">
                    <h2 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Pipeline</h2>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {PIPELINE_STAGES.map((stage) => {
                        const Icon = stage.icon;
                        const isActive = selectedStage === stage.key;
                        return (
                            <button
                                key={stage.key}
                                onClick={() => setSelectedStage(stage.key)}
                                className={`w-full flex items-center gap-2 px-3 py-2 text-left text-sm transition border-l-2 ${
                                    isActive
                                        ? 'bg-blue-50 border-blue-500 text-blue-700 font-medium'
                                        : 'border-transparent text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                <Icon size={16} className={isActive ? 'text-blue-500' : 'text-gray-400'} />
                                <span className="flex-1 truncate">{stage.label}</span>
                                <span className={`text-xs px-1.5 py-0.5 rounded ${
                                    isActive ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'
                                }`}>
                                    {stageCounts[stage.key] || 0}
                                </span>
                            </button>
                        );
                    })}
                </div>
                <div className="p-2 border-t border-gray-100">
                    <button
                        onClick={fetchApplications}
                        className="w-full flex items-center justify-center gap-2 py-2 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded transition"
                    >
                        <RefreshCw size={14} /> Refresh
                    </button>
                </div>
            </div>

            {/* Main Content - Loan List */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <LayoutDashboard size={20} className="text-blue-600" />
                        <h1 className="text-lg font-bold text-gray-800">Loan Pipeline</h1>
                        <span className="text-sm text-gray-500">
                            ({filteredApps.length} {filteredApps.length === 1 ? 'loan' : 'loans'})
                        </span>
                    </div>
                </div>

                {/* Loan List */}
                <div className="flex-1 overflow-y-auto p-3">
                    {filteredApps.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-gray-400">
                            <FolderOpen size={48} className="mb-2 opacity-30" />
                            <p className="text-sm">No applications in this stage</p>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {filteredApps.map((app) => {
                                const info = app.loan_metadata?.applicant_info || {};
                                return (
                                    <div
                                        key={app.workflow_id}
                                        onClick={() => navigate(`/manager/application/${app.workflow_id}`)}
                                        className={`bg-white border rounded-lg p-3 cursor-pointer transition group hover:border-blue-300 hover:shadow-sm ${
                                            selectedApp?.workflow_id === app.workflow_id ? 'border-blue-400 shadow-sm' : 'border-gray-200'
                                        }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            {/* Status Icon */}
                                            <div className={`w-8 h-8 rounded flex items-center justify-center ${getStatusColor(app.status)}`}>
                                                {getStatusIcon(app.status)}
                                            </div>

                                            {/* Loan Info */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium text-gray-900 text-sm truncate">
                                                        {info.name || 'Unknown Borrower'}
                                                    </span>
                                                    {app.loan_stage && (
                                                        <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
                                                            {app.loan_stage}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                                                    <span className="font-mono">{app.workflow_id.slice(0, 18)}...</span>
                                                    <span className="flex items-center gap-1">
                                                        <Calendar size={10} />
                                                        {new Date(app.created_at).toLocaleDateString()}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Actions */}
                                            <div className="flex items-center gap-2">
                                                <span className={`text-xs px-2 py-1 rounded border font-medium ${getStatusColor(app.status)}`}>
                                                    {app.status}
                                                </span>
                                                <button
                                                    onClick={(e) => handleDelete(e, app.workflow_id)}
                                                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition opacity-0 group-hover:opacity-100"
                                                    title="Delete"
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                                <ChevronRight size={16} className="text-gray-300 group-hover:text-blue-400" />
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
