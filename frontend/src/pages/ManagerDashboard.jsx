import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import {
    LayoutDashboard, RefreshCw, Trash2, Calendar
} from 'lucide-react';

export default function ManagerDashboard() {
    const [applications, setApplications] = useState([]);
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
        const interval = setInterval(fetchApplications, 5000); // Poll every 5s
        return () => clearInterval(interval);
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
    }

    const getStatusColor = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved")) return "bg-green-100 text-green-800";
        if (s.includes("rejected") || s.includes("fail")) return "bg-red-100 text-red-800";
        if (s.includes("flagged") || s.includes("mismatch")) return "bg-orange-100 text-orange-800";
        return "bg-blue-100 text-blue-800";
    };

    return (
        <div className="min-h-[calc(100vh-64px)] bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                            <LayoutDashboard className="text-blue-600" /> Manager Dashboard
                        </h1>
                        <p className="text-gray-500">Overview of all loan applications.</p>
                    </div>
                    <button onClick={fetchApplications} className="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-100 transition shadow-sm">
                        <RefreshCw size={20} className="text-gray-600" />
                    </button>
                </div>

                <div className="bg-white rounded-xl shadow border border-gray-200 overflow-hidden">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-gray-50 text-gray-500 text-sm border-b">
                                <th className="p-4 font-semibold">Application ID</th>
                                <th className="p-4 font-semibold">Date</th>
                                <th className="p-4 font-semibold">Current Status</th>
                                <th className="p-4 font-semibold text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {applications.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="p-8 text-center text-gray-400">
                                        No active applications.
                                    </td>
                                </tr>
                            ) : (
                                applications.map((app) => (
                                    <tr
                                        key={app.workflow_id}
                                        onClick={() => navigate(`/manager/application/${app.workflow_id}`)}
                                        className="border-b last:border-0 hover:bg-blue-50 cursor-pointer transition group"
                                    >
                                        <td className="p-4 font-mono text-sm text-blue-600 font-medium">
                                            {app.workflow_id}
                                        </td>
                                        <td className="p-4 text-gray-600 text-sm">
                                            <div className="flex items-center gap-2">
                                                <Calendar size={14} className="opacity-50" />
                                                {new Date(app.created_at).toLocaleDateString()}
                                                <span className="text-xs text-gray-400">
                                                    {new Date(app.created_at).toLocaleTimeString()}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getStatusColor(app.status)}`}>
                                                {app.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <button
                                                onClick={(e) => handleDelete(e, app.workflow_id)}
                                                className="text-gray-400 hover:text-red-600 p-2 rounded-full hover:bg-red-50 transition"
                                                title="Delete"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
