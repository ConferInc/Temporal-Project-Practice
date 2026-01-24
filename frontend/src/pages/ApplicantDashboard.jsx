import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { PlusCircle, FileText, Calendar, DollarSign, Loader, RefreshCw, CheckCircle, Circle } from 'lucide-react';

// Task Item Component for the getting started checklist
function TaskItem({ number, title, description, completed, isNext }) {
    return (
        <div className={`
            flex items-start gap-4 p-4 rounded-xl border-2 transition-all
            ${completed
                ? 'bg-green-50 border-green-200'
                : isNext
                    ? 'bg-blue-50 border-blue-300 shadow-sm'
                    : 'bg-gray-50 border-gray-200'
            }
        `}>
            <div className={`
                w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${completed
                    ? 'bg-green-500 text-white'
                    : isNext
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-500'
                }
            `}>
                {completed ? <CheckCircle size={18} /> : number}
            </div>
            <div>
                <h4 className={`font-semibold ${completed ? 'text-green-800' : isNext ? 'text-blue-900' : 'text-gray-700'}`}>
                    {title}
                </h4>
                <p className={`text-sm mt-0.5 ${completed ? 'text-green-600' : isNext ? 'text-blue-700' : 'text-gray-500'}`}>
                    {description}
                </p>
            </div>
        </div>
    );
}

export default function ApplicantDashboard() {
    const { user } = useAuth();
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);

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
    }, []);

    const getStatusColor = (status) => {
        const s = status?.toLowerCase() || "";
        if (s.includes("approved")) return "bg-green-100 text-green-800 border-green-200";
        if (s.includes("rejected") || s.includes("fail")) return "bg-red-100 text-red-800 border-red-200";
        if (s.includes("flagged") || s.includes("mismatch")) return "bg-orange-100 text-orange-800 border-orange-200";
        if (s.includes("submitted")) return "bg-blue-100 text-blue-800 border-blue-200";
        return "bg-gray-100 text-gray-800 border-gray-200";
    };

    return (
        <div className="max-w-6xl mx-auto p-6">
            <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Welcome, {user?.email?.split('@')[0]}!</h1>
                    <p className="text-gray-500 mt-1">Track and manage your loan applications.</p>
                </div>
                <Link to="/apply" className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 transition shadow-lg hover:-translate-y-0.5">
                    <PlusCircle size={20} /> Start New Application
                </Link>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b bg-gray-50 flex justify-between items-center">
                    <h2 className="font-bold text-gray-700 flex items-center gap-2">
                        <FileText size={20} /> Your Applications
                    </h2>
                    <button onClick={fetchApplications} className="p-2 hover:bg-gray-200 rounded-full transition" title="Refresh">
                        <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
                    </button>
                </div>

                {applications.length === 0 && !loading ? (
                    <div className="p-8">
                        {/* Task List Style - Getting Started */}
                        <div className="max-w-lg mx-auto">
                            <div className="text-center mb-8">
                                <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <FileText size={32} />
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 mb-2">Let's Complete Your Application</h3>
                                <p className="text-gray-500">Follow these steps to submit your loan application.</p>
                            </div>

                            {/* Task List */}
                            <div className="space-y-4">
                                <TaskItem
                                    number={1}
                                    title="Account Created"
                                    description="Your profile is set up and ready to go"
                                    completed={true}
                                />
                                <TaskItem
                                    number={2}
                                    title="Upload Documents"
                                    description="Submit your ID, tax returns, pay stub, and credit report"
                                    completed={false}
                                    isNext={true}
                                />
                                <TaskItem
                                    number={3}
                                    title="AI Verification"
                                    description="Our system will analyze your documents automatically"
                                    completed={false}
                                />
                                <TaskItem
                                    number={4}
                                    title="Receive Decision"
                                    description="Get your approval status within minutes"
                                    completed={false}
                                />
                            </div>

                            {/* CTA Button */}
                            <div className="mt-8 text-center">
                                <Link
                                    to="/apply"
                                    className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-blue-700 transition shadow-lg hover:-translate-y-0.5 text-lg"
                                >
                                    <PlusCircle size={22} />
                                    Upload Documents Now
                                </Link>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50 text-gray-500 text-sm uppercase tracking-wider border-b">
                                    <th className="p-4 font-semibold">Application ID</th>
                                    <th className="p-4 font-semibold">Status</th>
                                    <th className="p-4 font-semibold">Amount</th>
                                    <th className="p-4 font-semibold">Submitted On</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {loading ? (
                                    <tr>
                                        <td colSpan="4" className="p-8 text-center text-gray-500">
                                            <Loader className="animate-spin inline mr-2" /> Loading...
                                        </td>
                                    </tr>
                                ) : (
                                    applications.map((app) => (
                                        <tr key={app.workflow_id} className="hover:bg-gray-50 transition">
                                            <td className="p-4">
                                                <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded text-gray-600">
                                                    {app.workflow_id}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                <div className="flex flex-col items-start gap-2">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(app.status)}`}>
                                                        {app.status}
                                                    </span>
                                                    {app.decision_reason && (
                                                        <div className={`text-xs p-2 rounded border ${app.status.toLowerCase().includes('approved') ? 'bg-green-50 border-green-100 text-green-800' : 'bg-red-50 border-red-100 text-red-800'}`}>
                                                            <strong>Note:</strong> {app.decision_reason}
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="p-4 text-gray-700 font-medium">
                                                ${app.loan_amount?.toLocaleString() || '0'}
                                            </td>
                                            <td className="p-4 text-sm text-gray-500">
                                                <div className="flex items-center gap-1">
                                                    <Calendar size={14} />
                                                    {new Date(app.created_at).toLocaleDateString()}
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
