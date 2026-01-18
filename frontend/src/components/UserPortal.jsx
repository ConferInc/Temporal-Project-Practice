import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle, Loader, ArrowRight, User, DollarSign, CreditCard } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

export default function UserPortal() {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        ssn: '',
        income: ''
    });
    const [files, setFiles] = useState({
        id_document: null,
        tax_document: null,
        pay_stub: null,
        credit_document: null
    });

    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState(null); // { workflow_id, status: 'success'|'error' }

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleFileChange = (key, e) => {
        setFiles({ ...files, [key]: e.target.files[0] });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setUploading(true);

        const data = new FormData();
        Object.keys(formData).forEach(k => data.append(k, formData[k]));
        Object.keys(files).forEach(k => data.append(k, files[k]));

        try {
            const res = await axios.post(`${API_URL}/apply`, data, {
                headers: { "Content-Type": "multipart/form-data" }
            });
            setResult({ workflow_id: res.data.workflow_id, status: 'success' });
            setStep(3);
        } catch (err) {
            console.error(err);
            setResult({ status: 'error' });
            setStep(3);
        } finally {
            setUploading(false);
        }
    };

    const renderStep1 = () => (
        <div className="space-y-4 animate-in fade-in slide-in-from-right-8 duration-300">
            <h2 className="text-xl font-bold text-gray-800">1. Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <div className="relative">
                        <User className="absolute left-3 top-3 text-gray-400" size={18} />
                        <input name="name" type="text" placeholder="John Doe" required
                            className="w-full pl-10 p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                            onChange={handleInputChange} value={formData.name}
                        />
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input name="email" type="email" placeholder="john@example.com" required
                        className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                        onChange={handleInputChange} value={formData.email}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Annual Income ($)</label>
                    <div className="relative">
                        <DollarSign className="absolute left-3 top-3 text-gray-400" size={18} />
                        <input name="income" type="number" placeholder="100000" required
                            className="w-full pl-10 p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                            onChange={handleInputChange} value={formData.income}
                        />
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">SSN (Last 4)</label>
                    <div className="relative">
                        <CreditCard className="absolute left-3 top-3 text-gray-400" size={18} />
                        <input name="ssn" type="text" placeholder="XXXX" maxLength="4" required
                            className="w-full pl-10 p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                            onChange={handleInputChange} value={formData.ssn}
                        />
                    </div>
                </div>
            </div>
            <div className="flex justify-end pt-4">
                <button type="button" onClick={() => setStep(2)}
                    className="flex items-center bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition shadow-lg">
                    Next: Upload Docs <ArrowRight size={18} className="ml-2" />
                </button>
            </div>
        </div>
    );

    const renderFileUpload = (label, key, icon) => (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:border-blue-300 transition-colors">
            <div className="flex items-start justify-between">
                <div>
                    <p className="font-semibold text-gray-700 mb-1">{label}</p>
                    <p className="text-xs text-gray-500">{files[key] ? files[key].name : "No file selected"}</p>
                </div>
                {files[key] ? (
                    <CheckCircle className="text-green-500" size={24} />
                ) : (
                    <div className="relative overflow-hidden inline-block">
                        <button type="button" className="bg-white border text-blue-600 px-3 py-1 rounded text-sm font-medium">Select</button>
                        <input type="file" accept="application/pdf" className="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer"
                            onChange={(e) => handleFileChange(key, e)} required />
                    </div>
                )}
            </div>
        </div>
    );

    const renderStep2 = () => (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-300">
            <h2 className="text-xl font-bold text-gray-800">2. Required Documents</h2>
            <div className="space-y-3">
                {renderFileUpload("Valid ID (Passport/License)", "id_document")}
                {renderFileUpload("Latest Tax Return (1040)", "tax_document")}
                {renderFileUpload("Recent Pay Stub", "pay_stub")}
                {renderFileUpload("Credit Report (PDF)", "credit_document")}
            </div>

            <div className="flex justify-between pt-6 border-t">
                <button type="button" onClick={() => setStep(1)}
                    className="text-gray-500 font-medium px-4 hover:text-gray-800 transition">
                    Back
                </button>
                <button type="submit" disabled={uploading || !files.id_document || !files.tax_document || !files.pay_stub || !files.credit_document}
                    className={`flex items-center justify-center w-48 px-6 py-3 rounded-lg font-bold text-lg shadow-lg transition
                        ${uploading ? "bg-gray-100 text-gray-400 cursor-not-allowed" : "bg-green-600 text-white hover:bg-green-700 hover:-translate-y-0.5"}`}>
                    {uploading ? <Loader className="animate-spin" /> : "Submit Application"}
                </button>
            </div>
        </div>
    );

    const renderSuccess = () => (
        <div className="text-center py-10 animate-in zoom-in duration-500">
            {result.status === 'success' ? (
                <>
                    <div className="h-24 w-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle size={48} />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h3>
                    <p className="text-gray-600 mb-8">
                        Your tracking ID is <span className="font-mono bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-100">{result.workflow_id}</span>
                    </p>
                    <div className="bg-blue-50 p-4 rounded-lg text-left text-sm text-blue-800 mb-8 border border-blue-100">
                        <p className="font-bold mb-1">What happens next?</p>
                        <ul className="list-disc pl-5 space-y-1">
                            <li>Our AI verification system will analyze your documents (approx. 30s).</li>
                            <li>Your stated income (${formData.income}) will be cross-referenced with your tax returns.</li>
                            <li>You will receive an email notification with the final decision.</li>
                        </ul>
                    </div>
                </>
            ) : (
                <div className="text-red-500 font-bold">Something went wrong. Please try again.</div>
            )}
            <button onClick={() => window.location.reload()} className="text-gray-500 hover:underline">Start New Application</button>
        </div>
    );

    return (
        <div className="min-h-[calc(100vh-64px)] bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl border border-gray-100 p-8 transform transition-all">
                {step < 3 && (
                    <div className="flex items-center justify-between mb-8 px-2">
                        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-blue-600' : 'text-gray-300'}`}>
                            <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold border-current">1</div>
                            <span className="font-medium hidden sm:inline">Info</span>
                        </div>
                        <div className={`h-1 flex-1 mx-4 rounded ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
                        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-blue-600' : 'text-gray-300'}`}>
                            <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold border-current">2</div>
                            <span className="font-medium hidden sm:inline">Documents</span>
                        </div>
                        <div className={`h-1 flex-1 mx-4 rounded ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
                        <div className={`flex items-center gap-2 ${step >= 3 ? 'text-blue-600' : 'text-gray-300'}`}>
                            <div className="w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold border-current">3</div>
                            <span className="font-medium hidden sm:inline">Done</span>
                        </div>
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    {step === 1 && renderStep1()}
                    {step === 2 && renderStep2()}
                    {step === 3 && renderSuccess()}
                </form>
            </div>
        </div>
    );
}
