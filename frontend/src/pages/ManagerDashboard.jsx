import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import {
    LayoutDashboard, RefreshCw, Trash2, Calendar,
    FolderOpen, FileText, CheckSquare, History,
    ChevronRight, Users, Clock, CheckCircle, XCircle, AlertTriangle,
    Activity, Cpu, Server, Database, Zap, Terminal, Settings, BarChart3
} from 'lucide-react';

const PIPELINE_STAGES = [
    { key: 'all', label: 'All Applications', icon: FolderOpen },
    { key: 'LEAD_CAPTURE', label: 'Lead Capture', icon: Users },
    { key: 'PROCESSING', label: 'Processing', icon: Clock },
    { key: 'UNDERWRITING', label: 'Underwriting', icon: FileText },
    { key: 'CLOSING', label: 'Closing', icon: CheckSquare },
    { key: 'ARCHIVED', label: 'Archived', icon: History },
];

// System Logs Component - Terminal Style
function SystemLogs({ logs, loading }) {
    return (
        <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
            <div className="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
                <div className="flex items-center gap-2">
                    <Terminal size={14} className="text-green-400" />
                    <span className="text-xs font-mono text-gray-400">SYSTEM ACTIVITY</span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="text-xs text-green-400">LIVE</span>
                </div>
            </div>
            <div className="p-3 h-48 overflow-y-auto font-mono text-xs">
                {loading ? (
                    <div className="text-gray-500">Loading logs...</div>
                ) : logs.length === 0 ? (
                    <div className="text-gray-500">No recent activity</div>
                ) : (
                    logs.map((log, idx) => (
                        <div key={idx} className="mb-2 flex items-start gap-2">
                            <span className="text-gray-600 flex-shrink-0">
                                {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                            <span className={`flex-shrink-0 px-1 rounded text-xs ${
                                log.agent?.includes('CEO') ? 'bg-purple-900 text-purple-300' :
                                log.agent?.includes('AI') || log.agent?.includes('Analyst') ? 'bg-blue-900 text-blue-300' :
                                log.agent?.includes('DocGen') ? 'bg-yellow-900 text-yellow-300' :
                                log.agent?.includes('Underwriting') ? 'bg-orange-900 text-orange-300' :
                                'bg-gray-800 text-gray-400'
                            }`}>
                                {log.agent || 'System'}
                            </span>
                            <span className="text-green-400">{log.message}</span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// Worker Status Widget
function WorkerStatus({ workers }) {
    return (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
                <div className="flex items-center gap-2">
                    <Server size={14} className="text-gray-500" />
                    <span className="text-xs font-bold text-gray-600 uppercase">Worker Status</span>
                </div>
            </div>
            <div className="p-2 space-y-1">
                {workers.map((worker, idx) => (
                    <div key={idx} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-gray-50">
                        <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${
                                worker.status === 'online' ? 'bg-green-500' :
                                worker.status === 'busy' ? 'bg-yellow-500' : 'bg-red-500'
                            }`}></div>
                            <span className="text-sm font-medium text-gray-700">{worker.name}</span>
                        </div>
                        <span className="text-xs text-gray-400">{worker.last_activity}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Stats Card
function StatCard({ icon: Icon, label, value, color = "blue" }) {
    const colors = {
        blue: "bg-blue-100 text-blue-600",
        green: "bg-green-100 text-green-600",
        orange: "bg-orange-100 text-orange-600",
        purple: "bg-purple-100 text-purple-600",
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
                    <Icon size={20} />
                </div>
                <div>
                    <div className="text-2xl font-bold text-gray-900">{value}</div>
                    <div className="text-xs text-gray-500 uppercase">{label}</div>
                </div>
            </div>
        </div>
    );
}

export default function ManagerDashboard() {
    const [applications, setApplications] = useState([]);
    const [selectedStage, setSelectedStage] = useState('all');
    const [systemLogs, setSystemLogs] = useState([]);
    const [workers, setWorkers] = useState([
        { name: "AI Analyst", status: "online", last_activity: "2s ago" },
        { name: "DocGen MCP", status: "online", last_activity: "5s ago" },
        { name: "Encompass MCP", status: "online", last_activity: "1s ago" },
        { name: "Underwriting", status: "online", last_activity: "3s ago" },
    ]);
    const [logsLoading, setLogsLoading] = useState(true);
    const navigate = useNavigate();

    const fetchApplications = async () => {
        try {
            const res = await api.get('/applications');
            setApplications(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchLogs = async () => {
        try {
            const res = await api.get('/recent_logs?limit=15');
            setSystemLogs(res.data);
            setLogsLoading(false);
        } catch (err) {
            console.error('Failed to fetch logs:', err);
            setLogsLoading(false);
        }
    };

    const fetchSystemHealth = async () => {
        try {
            const res = await api.get('/system_health');
            if (res.data?.workers) {
                setWorkers(res.data.workers);
            }
        } catch (err) {
            console.error('Failed to fetch system health:', err);
        }
    };

    useEffect(() => {
        fetchApplications();
        fetchLogs();
        fetchSystemHealth();

        const appInterval = setInterval(fetchApplications, 5000);
        const logInterval = setInterval(fetchLogs, 2000);
        const healthInterval = setInterval(fetchSystemHealth, 10000);

        return () => {
            clearInterval(appInterval);
            clearInterval(logInterval);
            clearInterval(healthInterval);
        };
    }, []);

    const handleDelete = async (e, appId) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to DELETE this application? This cannot be undone.")) return;
        try {
            await api.delete(`/application/${appId}`);
            fetchApplications();
        } catch (err) {
            alert("Delete failed");
        }
    };

    const getStatusIcon = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved") || s.includes("signed")) return <CheckCircle size={14} className="text-green-600" />;
        if (s.includes("rejected") || s.includes("fail")) return <XCircle size={14} className="text-red-600" />;
        if (s.includes("flagged") || s.includes("mismatch")) return <AlertTriangle size={14} className="text-orange-500" />;
        return <Clock size={14} className="text-blue-500" />;
    };

    const getStatusColor = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved") || s.includes("signed")) return "bg-green-50 border-green-200 text-green-700";
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

    // Stats
    const pendingReview = applications.filter(a => a.status?.toLowerCase().includes('submitted')).length;
    const approved = applications.filter(a => a.status?.toLowerCase().includes('approved')).length;
    const inClosing = applications.filter(a => a.loan_stage === 'CLOSING').length;

    return (
        <div className="h-[calc(100vh-64px)] bg-gray-100 flex">
            {/* Sidebar - Pipeline View */}
            <div className="w-56 bg-white border-r border-gray-200 flex flex-col">
                <div className="p-3 border-b border-gray-100">
                    <div className="flex items-center gap-2">
                        <LayoutDashboard size={18} className="text-blue-600" />
                        <h2 className="text-sm font-bold text-gray-800">Mission Control</h2>
                    </div>
                </div>

                {/* Navigation */}
                <div className="p-2 border-b border-gray-100">
                    <div className="text-xs font-bold text-gray-400 uppercase px-2 mb-2">Pipeline</div>
                    {PIPELINE_STAGES.map((stage) => {
                        const Icon = stage.icon;
                        const isActive = selectedStage === stage.key;
                        return (
                            <button
                                key={stage.key}
                                onClick={() => setSelectedStage(stage.key)}
                                className={`w-full flex items-center gap-2 px-2 py-1.5 text-left text-sm rounded transition ${
                                    isActive
                                        ? 'bg-blue-50 text-blue-700 font-medium'
                                        : 'text-gray-600 hover:bg-gray-50'
                                }`}
                            >
                                <Icon size={14} className={isActive ? 'text-blue-500' : 'text-gray-400'} />
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

                {/* Worker Status Widget */}
                <div className="flex-1 p-2 overflow-y-auto">
                    <WorkerStatus workers={workers} />
                </div>

                <div className="p-2 border-t border-gray-100">
                    <button
                        onClick={() => { fetchApplications(); fetchLogs(); }}
                        className="w-full flex items-center justify-center gap-2 py-2 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded transition"
                    >
                        <RefreshCw size={14} /> Refresh All
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header with Stats */}
                <div className="bg-white border-b border-gray-200 px-4 py-3">
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <Activity size={20} className="text-blue-600" />
                            <h1 className="text-lg font-bold text-gray-800">Loan Pipeline</h1>
                            <span className="text-sm text-gray-500">
                                ({filteredApps.length} {filteredApps.length === 1 ? 'loan' : 'loans'})
                            </span>
                        </div>
                    </div>
                    {/* Stats Row */}
                    <div className="grid grid-cols-4 gap-3">
                        <StatCard icon={Clock} label="Pending Review" value={pendingReview} color="orange" />
                        <StatCard icon={CheckCircle} label="Approved" value={approved} color="green" />
                        <StatCard icon={FileText} label="In Closing" value={inClosing} color="purple" />
                        <StatCard icon={BarChart3} label="Total Active" value={applications.length} color="blue" />
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 flex overflow-hidden">
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
                                            className="bg-white border rounded-lg p-3 cursor-pointer transition group hover:border-blue-300 hover:shadow-sm border-gray-200"
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

                    {/* Right Panel - System Logs */}
                    <div className="w-80 border-l border-gray-200 bg-gray-50 p-3 flex flex-col gap-3">
                        <SystemLogs logs={systemLogs} loading={logsLoading} />

                        {/* Quick Actions */}
                        <div className="bg-white rounded-lg border border-gray-200 p-3">
                            <div className="text-xs font-bold text-gray-500 uppercase mb-2">Quick Actions</div>
                            <div className="space-y-1">
                                <button
                                    onClick={fetchApplications}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded transition"
                                >
                                    <RefreshCw size={14} /> Refresh Pipeline
                                </button>
                                <button
                                    onClick={() => setSelectedStage('LEAD_CAPTURE')}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded transition"
                                >
                                    <Users size={14} /> View Pending Reviews
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
