 ManagerDashboard.jsx:50 Summary Error: AxiosError: Request failed with status code 401

  at settle (axios.js?v=4dc40213:1267:12)
  at XMLHttpRequest.onloadend (axios.js?v=4dc40213:1616:7)
  at Axios.request (axios.js?v=4dc40213:2233:41)
  at async fetchOperationsSummary (ManagerDashboard.jsx:48:25)
  fetchOperationsSummary @ ManagerDashboard.jsx:50
  await in fetchOperationsSummary
  fetchAllData @ ManagerDashboard.jsx:29
  ManagerDashboard.jsx:36 Legacy App Error: AxiosError: Request failed with status code 401
  at settle (axios.js?v=4dc40213:1267:12)
  at XMLHttpRequest.onloadend (axios.js?v=4dc40213:1616:7)
  at Axios.request (axios.js?v=4dc40213:2233:41)
  at async fetchApplications (ManagerDashboard.jsx:34:25)
  fetchApplications @ ManagerDashboard.jsx:36
  await in fetchApplications
  fetchAllData @ ManagerDashboard.jsx:27  This is the issue that I am getting. I have to manage our dashboard.jsx files in my components and pages. The one that you have been updating is within the
  components folder and the one my app.jsx has been using is the pages folder. What I want you to do is make sure you give me the best out of the two.

  What this should do is have the live ops data fetch all the folders like how it was doing when we go to the legacy system and on top of it the AI analysis which was not working before but you worked on
  it and you created a new file in the components one. I want you to make sure that AI analysis is also there. This error that I am getting is because it is not able to access all the files from our
  database. I want to make sure that also works.

  Figure out what the issue is in frontend between these two manager dashboards.jsx files. If you find integrate both of them into one, remove the one which is not necessary and implement the one which is
  the best including both of them. Making sure there is an approve button underwriting so that when I get to underwriting I can approve it and it unlocks it and it sends a disclosures form to the front end
  of that weekend applicant signs that comes back here goes to closing goes to archive.

  The front-end should look nice. Make sure these pages for manager dashboard.jsx is resolved. Integrate them, create the best one.

● Let me investigate the frontend structure and find both dashboard files.

● Searched for 3 patterns, read 1 file (ctrl+o to expand)

● Now let me read both dashboard files and the auth context to understand the authentication:

● Read 4 files (ctrl+o to expand)

● I found the issue. Both dashboards use plain axios without auth headers, but the utils/api.js has the correct auth interceptor. I'll create a unified, production-grade pages/ManagerDashboard.jsx that:

1. Uses the api utility with auth tokens
2. Combines the best features from both files
3. Includes AI analysis, document viewer, underwriting decisions, and signature support

● Write(frontend\src\pages\ManagerDashboard.jsx)
  ⎿  Added 646 lines, removed 330 lines
        1 -import React, { useEffect, useState } from 'react';
        2 -import axios from 'axios'; // We use direct axios to ensure DB connection works
        3 -import {
        4 -    LayoutDashboard, FileText, CheckCircle, XCircle,
        5 -    Trash2, RefreshCw, Lock, Unlock,
        6 -    Database, Gavel, ExternalLink, Shield, Archive, AlertTriangle
        7 -} from 'lucide-react';
        8 -
        9 -const API_URL = "http://localhost:3001";
       10 -
       11 -export default function ManagerDashboard() {
       12 -    // STATE
       13 -    const [viewMode, setViewMode] = useState('operations'); // Default to 'operations' (Live Ops)
       14 -    const [applications, setApplications] = useState([]);
       15 -    const [loanApplications, setLoanApplications] = useState([]);
       16 -    const [operationsSummary, setOperationsSummary] = useState(null);
       17 -
       18 -    // SELECTION STATE
       19 -    const [selectedApp, setSelectedApp] = useState(null);
       20 -    const [details, setDetails] = useState(null);
       21 -    const [loadingDetails, setLoadingDetails] = useState(false);
       22 -    const [selectedDoc, setSelectedDoc] = useState(null);
       23 -    const [uwReason, setUwReason] = useState('');
       24 -
       25 -    // --- DATA FETCHING ---
       26 -    const fetchAllData = () => {
       27 -        fetchApplications();
       28 -        fetchLoanApplications();
       29 -        fetchOperationsSummary();
       30 -    };
       31 -
       32 -    const fetchApplications = async () => {
       33 -        try {
       34 -            const res = await axios.get(`${API_URL}/applications`);
       35 -            setApplications(res.data);
       36 -        } catch (err) { console.error("Legacy App Error:", err); }
       37 -    };
       38 -
       39 -    const fetchLoanApplications = async () => {
       40 -        try {
       41 -            const res = await axios.get(`${API_URL}/loan-applications`);
       42 -            setLoanApplications(res.data);
       43 -        } catch (err) { console.error("DB App Error:", err); }
       44 -    };
       45 -
       46 -    const fetchOperationsSummary = async () => {
       47 -        try {
       48 -            const res = await axios.get(`${API_URL}/operations/summary`);
       49 -            setOperationsSummary(res.data);
       50 -        } catch (err) { console.error("Summary Error:", err); }
       51 -    };
       52 -
       53 -    const fetchDetails = async (workflowId) => {
       54 -        setLoadingDetails(true);
       55 -        setDetails(null);
       56 -        try {
       57 -            const res = await axios.get(`${API_URL}/status/${workflowId}`);
       58 -            setDetails(res.data);
       59 -
       60 -            if (res.data.data?.public_urls) {
       61 -                const urls = res.data.data.public_urls;
       62 -                setSelectedDoc(urls.tax_document ? 'tax_document' : Object.keys(urls)[0]);
       63 -            } else if (res.data.file_url) {
       64 -                setSelectedDoc('legacy');
       65 -            }
       66 -        } catch (err) {
       67 -            console.warn("Legacy details not found (Expected for new DB-only apps)");
       68 -        } finally {
       69 -            setLoadingDetails(false);
       70 -        }
       71 -    };
       72 -
       73 -    useEffect(() => {
       74 -        fetchAllData();
       75 -        const interval = setInterval(fetchAllData, 5000);
       76 -        return () => clearInterval(interval);
       77 -    }, []);
       78 -
       79 -    // --- HANDLERS ---
       80 -    const handleSelectApp = (app) => {
       81 -        setSelectedApp(app);
       82 -        fetchDetails(app.workflow_id);
       83 -    };
       84 -
       85 -    // 1. The Waiter Pattern Trigger
       86 -    const handleUnderwritingDecision = async (workflowId, approved) => {
       87 -        if (!uwReason.trim()) return alert("Please provide a reason!");
       88 -        try {
       89 -            await axios.post(`${API_URL}/underwriting/decision`, {
       90 -                workflow_id: workflowId,
       91 -                approved: approved,
       92 -                reason: uwReason
       93 -            });
       94 -            alert(`Decision Submitted: ${approved ? 'APPROVED' : 'REJECTED'}`);
       95 -            setUwReason('');
       96 -            fetchAllData();
       97 -            // Optimistic Update
       98 -            if (selectedApp?.workflow_id === workflowId) {
       99 -                setSelectedApp(prev => ({
      100 -                    ...prev,
      101 -                    is_locked: false,
      102 -                    status: approved ? 'Funded' : 'Rejected',
      103 -                    underwriting_decision: approved ? 'approved' : 'rejected'
      104 -                }));
      105 -            }
      106 -        } catch (err) {
      107 -            alert("Submission Failed: " + err.message);
      108 -        }
      109 -    };
      110 -
      111 -    // 2. The Manual Archive Trigger
      112 -    const handleArchive = async (workflowId) => {
      113 -        if (!confirm("Archive this loan? It will be moved to history.")) return;
      114 -        try {
      115 -            // We use a simple update to the local status for now, or you can add an endpoint
      116 -            // For now, let's just visually hide it or mark it locally if the API isn't ready
      117 -            // Ideally call: axios.post(`${API_URL}/archive/${workflowId}`)
      118 -            alert("Loan Archived!");
      119 -            // Refresh list
      120 -            fetchAllData();
      121 -            setSelectedApp(null);
      122 -        } catch (err) {
      123 -            alert("Archive failed");
      124 -        }
      125 -    };
      126 -
      127 -    // --- HELPERS ---
      128 -    const getStatusColor = (status) => {
      129 -        const s = status?.toLowerCase() || "";
      130 -        if (s.includes("funded") || s.includes("clear")) return "bg-green-100 text-green-800";
      131 -        if (s.includes("lock") || s.includes("wait") || s.includes("pending")) return "bg-orange-100 text-orange-800";
      132 -        if (s.includes("reject")) return "bg-red-100 text-red-800";
      133 -        return "bg-blue-100 text-blue-800";
      134 -    };
      135 -
      136 -    return (
      137 -        `<div className="flex h-[calc(100vh-64px)] bg-gray-50 overflow-hidden">`
      138 -            {/* === LEFT SIDEBAR === */}
      139 -            `<div className="w-1/3 max-w-md bg-white border-r flex flex-col shadow-lg z-10">`
      140 -                {/* VIEW TOGGLE */}
      141 -                `<div className="p-3 bg-gray-100 border-b flex gap-2">`
      142 -                    <button
      143 -                        onClick={() => { setViewMode('operations'); setSelectedApp(null); }}

| 144 -                        className={`flex-1 py-2 px-3 rounded-lg text-sm font-bold transition ${viewMode === 'operations' ? 'bg-white text-purple-600 shadow' : 'text-gray-500 hover:bg-gray-200' |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 145 -                            }`}                                                                                                                                                                  |
| 146 -                    >                                                                                                                                                                            |
| 147 -                        <Database size={14} className="inline mr-1" /> Live Ops (DB)                                                                                                             |
| 148 -`</button>`                                                                                                                                                                                    |
| 149 -                    <button                                                                                                                                                                      |
| 150 -                        onClick={() => { setViewMode('applications'); setSelectedApp(null); }}                                                                                                   |
| 151 -                        className={`flex-1 py-2 px-3 rounded-lg text-sm font-bold transition ${viewMode === 'applications' ? 'bg-white text-blue-600 shadow' : 'text-gray-500 hover:bg-gray-200' |
| -                                                                                                                                                                                                     |
| 152 -                            }`}                                                                                                                                                                  |
| 153 -                    >                                                                                                                                                                            |
| 154 -                        <LayoutDashboard size={14} className="inline mr-1" /> Legacy                                                                                                             |
| 155 -`</button>`                                                                                                                                                                                    |
| 156 -`</div>`                                                                                                                                                                                       |
| 157 -                                                                                                                                                                                                 |
| 158 -                {/* APP LIST */}                                                                                                                                                                 |
| 159 -`<div className="flex-1 overflow-y-auto">`                                                                                                                                                     |
| 160 -                    {viewMode === 'operations' ? (                                                                                                                                               |
| 161 -                        <>                                                                                                                                                                       |
| 162 -                            {/* LIVE OPS SUMMARY */}                                                                                                                                             |
| 163 -                            {operationsSummary && (                                                                                                                                              |
| 164 -`<div className="grid grid-cols-3 gap-2 p-3 bg-gray-50 border-b text-center">`                                                                                                                 |
| 165 -`<div className="bg-white p-2 rounded shadow-sm">`                                                                                                                                             |
| 166 -`<div className="text-xl font-bold text-blue-600">`{operationsSummary.total_applications}`</div>`                                                                                            |
| 167 -`<div className="text-[10px] text-gray-500 uppercase">`Total`</div>`                                                                                                                         |
| 168 -`</div>`                                                                                                                                                                                       |
| 169 -`<div className="bg-white p-2 rounded shadow-sm">`                                                                                                                                             |
| 170 -`<div className="text-xl font-bold text-orange-600">`{operationsSummary.locked_waiting}`</div>`                                                                                              |
| 171 -`<div className="text-[10px] text-gray-500 uppercase">`Locked`</div>`                                                                                                                        |
| 172 -`</div>`                                                                                                                                                                                       |
| 173 -`<div className="bg-white p-2 rounded shadow-sm">`                                                                                                                                             |
| 174 -`<div className="text-xl font-bold text-green-600">`{operationsSummary.funded}`</div>`                                                                                                       |
| 175 -`<div className="text-[10px] text-gray-500 uppercase">`Funded`</div>`                                                                                                                        |
| 176 -`</div>`                                                                                                                                                                                       |
| 177 -`</div>`                                                                                                                                                                                       |
| 178 -                            )}                                                                                                                                                                   |
| 179 -                                                                                                                                                                                                 |
| 180 -                            {/* DB LIST ITEMS */}                                                                                                                                                |
| 181 -                            {loanApplications.map(app => (                                                                                                                                       |
| 182 -                                <div                                                                                                                                                             |
| 183 -                                    key={app.id}                                                                                                                                                 |
| 184 -                                    onClick={() => handleSelectApp(app)}                                                                                                                         |
| 185 -                                    className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-all                                                                                      |
| 186 -                                        ${selectedApp?.id === app.id ? 'bg-purple-50 border-l-4 border-l-purple-500' : 'border-l-4 border-l-transparent'}                                        |
| 187 -                                    `}                                                                                                                                                           |
| 188 -                                >                                                                                                                                                                |
| 189 -`<div className="flex justify-between items-center mb-1">`                                                                                                                                     |
| 190 -`<span className="font-mono text-[10px] bg-gray-100 text-gray-600 px-1 rounded">`                                                                                                              |
| 191 -                                            {app.workflow_id.split('-').pop()}                                                                                                                   |
| 192 -                                                                                                                                                                                                 |
| 193 -                                        {app.is_locked && (                                                                                                                                      |
| 194 -`<span className="flex items-center gap-1 text-[10px] font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">`                                                                      |
| 195 -`<Lock size={10} />` LOCKED                                                                                                                                                                    |
| 196 -                                                                                                                                                                                                 |
| 197 -                                        )}                                                                                                                                                       |
| 198 -`</div>`                                                                                                                                                                                       |
| 199 -`<div className="font-bold text-gray-800">`{app.borrower_name}`</div>`                                                                                                                       |
| 200 -`<div className="text-xs text-gray-500 flex justify-between mt-1">`                                                                                                                            |
| 201 -`<span>`${app.loan_amount?.toLocaleString()}                                                                                                                                                   |
| 202 -                                        <span className={`px-1.5 rounded ${getStatusColor(app.status)}`}>{app.status}                                                                          |
| 203 -`</div>`                                                                                                                                                                                       |
| 204 -`</div>`                                                                                                                                                                                       |
| 205 -                            ))}                                                                                                                                                                  |
| 206 -                        </>                                                                                                                                                                      |
| 207 -                    ) : (                                                                                                                                                                        |
| 208 -                        /* LEGACY LIST */                                                                                                                                                        |
| 209 -                        applications.map(app => (                                                                                                                                                |
| 210 -                            <div                                                                                                                                                                 |
| 211 -                                key={app.workflow_id}                                                                                                                                            |
| 212 -                                onClick={() => handleSelectApp(app)}                                                                                                                             |
| 213 -                                className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${selectedApp?.workflow_id === app.workflow_id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''}`}    |
| 214 -                            >                                                                                                                                                                    |
| 215 -`<div className="font-mono text-xs text-gray-500 mb-1">`{app.workflow_id}`</div>`                                                                                                            |
| 216 -                                <div className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(app.status)}`}>                                                         |
| 217 -                                    {app.status}                                                                                                                                                 |
| 218 -`</div>`                                                                                                                                                                                       |
| 219 -`</div>`                                                                                                                                                                                       |
| 220 -                        ))                                                                                                                                                                       |
| 221 -                    )}                                                                                                                                                                           |
| 222 -`</div>`                                                                                                                                                                                       |
| 223 -`</div>`                                                                                                                                                                                       |
| 224 -                                                                                                                                                                                                 |
| 225 -            {/* === MAIN CONTENT === */}                                                                                                                                                         |
| 226 -`<div className="flex-1 bg-gray-100 p-6 overflow-hidden flex flex-col">`                                                                                                                       |
| 227 -                {selectedApp ? (                                                                                                                                                                 |
| 228 -`<div className="h-full flex gap-6">`                                                                                                                                                          |
| 229 -                        {/* LEFT COLUMN: ACTION & DATA */}                                                                                                                                       |
| 230 -`<div className="flex-1 flex flex-col gap-4 overflow-y-auto">`                                                                                                                                 |
| 231 -                                                                                                                                                                                                 |
| 232 -                            {/* 1. HEADER CARD */}                                                                                                                                               |
| 233 -`<div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">`                                                                                                                   |
| 234 -`<h1 className="text-2xl font-bold text-gray-800 flex items-center gap-3">`                                                                                                                    |
| 235 -                                    {selectedApp.borrower_name                                                                                                                                   |
| 236 -                                    {selectedApp.is_locked ?`<Lock className="text-orange-500" />` : `<Unlock className="text-green-500" />`}                                                |
| 237 -`</h1>`                                                                                                                                                                                        |
| 238 -`<p className="text-sm text-gray-500 mt-1">`ID: {selectedApp.workflow_id}`</p>`                                                                                                              |
| 239 -`</div>`                                                                                                                                                                                       |
| 240 -                                                                                                                                                                                                 |
| 241 -                            {/* 2. WAITER PATTERN PANEL (Action Required) */}                                                                                                                    |
| 242 -                            {selectedApp.is_locked && (                                                                                                                                          |
| 243 -`<div className="bg-orange-50 border-2 border-orange-200 rounded-xl p-6 shadow-sm">`                                                                                                           |
| 244 -`<h3 className="text-lg font-bold text-orange-800 mb-2 flex items-center gap-2">`                                                                                                              |
| 245 -`<Gavel size={20} />` Underwriting Decision Required                                                                                                                                           |
| 246 -`</h3>`                                                                                                                                                                                        |
| 247 -`<div className="bg-white p-3 rounded border border-orange-100 mb-4 text-sm text-gray-600">`                                                                                                   |
| 248 -                                        ⚠️ Workflow is PAUSED. It will not proceed until you provide a decision.                                                                               |
| 249 -`</div>`                                                                                                                                                                                       |
| 250 -                                    <textarea                                                                                                                                                    |
| 251 -                                        className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-orange-200"                                                                         |
| 252 -                                        placeholder="Enter reason (e.g., 'Income verified, DTI < 40%')..."                                                                                       |
| 253 -                                        value={uwReason}                                                                                                                                         |
| 254 -                                        onChange={e => setUwReason(e.target.value)}                                                                                                              |
| 255 -                                        rows={2}                                                                                                                                                 |
| 256 -                                    />                                                                                                                                                           |
| 257 -`<div className="flex gap-3">`                                                                                                                                                                 |
| 258 -                                        <button                                                                                                                                                  |
| 259 -                                            onClick={() => handleUnderwritingDecision(selectedApp.workflow_id, true)}                                                                            |
| 260 -                                            className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 shadow flex items-center justify-center gap-2"                |
| 261 -                                        >                                                                                                                                                        |
| 262 -`<CheckCircle size={18} />` Approve & Fund                                                                                                                                                     |
| 263 -`</button>`                                                                                                                                                                                    |
| 264 -                                        <button                                                                                                                                                  |
| 265 -                                            onClick={() => handleUnderwritingDecision(selectedApp.workflow_id, false)}                                                                           |
| 266 -                                            className="flex-1 bg-white text-red-600 border border-red-200 py-3 rounded-lg font-bold hover:bg-red-50 flex items-center justify-center gap-2"      |
| 267 -                                        >                                                                                                                                                        |
| 268 -`<XCircle size={18} />` Reject                                                                                                                                                                 |
| 269 -`</button>`                                                                                                                                                                                    |
| 270 -`</div>`                                                                                                                                                                                       |
| 271 -`</div>`                                                                                                                                                                                       |
| 272 -                            )}                                                                                                                                                                   |
| 273 -                                                                                                                                                                                                 |
| 274 -                            {/* 3. POST-CLOSING (Manual Archive) */}                                                                                                                             |
| 275 -                            {!selectedApp.is_locked && selectedApp.status?.toLowerCase().includes('funded') && (                                                                                 |
| 276 -`<div className="bg-green-50 border border-green-200 rounded-xl p-6 shadow-sm">`                                                                                                               |
| 277 -`<h3 className="text-lg font-bold text-green-800 mb-2 flex items-center gap-2">`                                                                                                               |
| 278 -`<CheckCircle size={20} />` Loan Funded Successfully                                                                                                                                           |
| 279 -`</h3>`                                                                                                                                                                                        |
| 280 -`<p className="text-sm text-green-700 mb-4">`                                                                                                                                                  |
| 281 -                                        The workflow is complete. You can now archive this file.                                                                                                 |
| 282 -`</p>`                                                                                                                                                                                         |
| 283 -                                    <button                                                                                                                                                      |
| 284 -                                        onClick={() => handleArchive(selectedApp.workflow_id)}                                                                                                   |
| 285 -                                        className="w-full bg-white text-gray-600 border border-gray-300 py-2 rounded-lg font-bold hover:bg-gray-50 flex items-center justify-center gap-2"       |
| 286 -                                    >                                                                                                                                                            |
| 287 -`<Archive size={18} />` Archive Loan                                                                                                                                                           |
| 288 -`</button>`                                                                                                                                                                                    |
| 289 -`</div>`                                                                                                                                                                                       |
| 290 -                            )}                                                                                                                                                                   |
| 291 -                                                                                                                                                                                                 |
| 292 -                            {/* 4. DETAILS CARD */}                                                                                                                                              |
| 293 -`<div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">`                                                                                                                   |
| 294 -`<h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2">`                                                                                                                        |
| 295 -`<Shield className="text-blue-500" size={18} />` Verification Data                                                                                                                             |
| 296 -`</h3>`                                                                                                                                                                                        |
| 297 -`<pre className="bg-gray-50 p-4 rounded text-xs overflow-auto h-40">`                                                                                                                          |
| 298 -                                    {JSON.stringify(selectedApp, null, 2)}                                                                                                                       |
| 299 -`</pre>`                                                                                                                                                                                       |
| 300 -`</div>`                                                                                                                                                                                       |
| 301 -`</div>`                                                                                                                                                                                       |
| 302 -                                                                                                                                                                                                 |
| 303 -                        {/* RIGHT COLUMN: PDF */}                                                                                                                                                |
| 304 -`<div className="w-[500px] bg-white rounded-xl shadow-lg border border-gray-200 flex flex-col">`                                                                                               |
| 305 -                            {details && selectedDoc ? (                                                                                                                                          |
| 306 -                                <iframe                                                                                                                                                          |
| 307 -                                    src={`${API_URL}${details.data?.public_urls?.[selectedDoc]                                                                                                 |
| 308 -                                    className="flex-1 w-full h-full bg-slate-50 rounded-b-xl"                                                                                                    |
| 309 -                                    title="Doc Viewer"                                                                                                                                           |
| 310 -                                />                                                                                                                                                               |
| 311 -                            ) : (                                                                                                                                                                |
| 312 -`<div className="flex-1 flex flex-col items-center justify-center text-gray-300">`                                                                                                             |
| 313 -                                    <FileText size={48} className="mb-4 opacity-20" />                                                                                                           |
| 314 -`<p>`Document Preview`</p>`                                                                                                                                                                  |
| 315 -`</div>`                                                                                                                                                                                       |
| 316 -                            )}                                                                                                                                                                   |
| 317 -`</div>`                                                                                                                                                                                       |
| 318 -`</div>`                                                                                                                                                                                       |
| 319 -                ) : (                                                                                                                                                                            |
| 320 -                    /* EMPTY STATE */                                                                                                                                                            |
| 321 -`<div className="h-full flex flex-col items-center justify-center text-gray-400">`                                                                                                             |
| 322 -                        <Database size={64} className="mb-6 opacity-10" />                                                                                                                       |
| 323 -`<h2 className="text-xl font-bold text-gray-600">`Live Operations`</h2>`                                                                                                                     |
| 324 -`<p>`Select a loan from the list to view details.`</p>`                                                                                                                                      |
| 325 -`</div>`                                                                                                                                                                                       |
| 326 -                )}                                                                                                                                                                               |
| 327 -`</div>`                                                                                                                                                                                       |
| 328 -`</div>`                                                                                                                                                                                       |
| 329 -    );                                                                                                                                                                                           |
| 330 -}                                                                                                                                                                                                |
| 1   No newline at end of file                                                                                                                                                                         |
| 2 +import React, { useEffect, useState } from 'react';                                                                                                                                                |
| 3 +import api from '../utils/api';                                                                                                                                                                    |
| 4 +import {                                                                                                                                                                                           |
| 5 +    LayoutDashboard, FileText, CheckCircle, XCircle,                                                                                                                                               |
| 6 +    AlertTriangle, Trash2, ExternalLink, RefreshCw,                                                                                                                                                |
| 7 +    Shield, DollarSign, User, Lock, Unlock, Clock,                                                                                                                                                 |
| 8 +    Database, Activity, Gavel, Archive, PenTool                                                                                                                                                    |
| 9 +} from 'lucide-react';                                                                                                                                                                             |
| 10 +                                                                                                                                                                                                  |
| 11 +const API_URL = import.meta.env.VITE_API_URL                                                                                                                                                      |
| 12 +                                                                                                                                                                                                  |
| 13 +export default function ManagerDashboard() {                                                                                                                                                      |
| 14 +    // === STATE ===                                                                                                                                                                              |
| 15 +    const [viewMode, setViewMode] = useState('operations'); // 'operations' (Live Ops) or 'applications' (Legacy)                                                                                 |
| 16 +    const [applications, setApplications] = useState([]);                                                                                                                                         |
| 17 +    const [loanApplications, setLoanApplications] = useState([]);                                                                                                                                 |
| 18 +    const [operationsSummary, setOperationsSummary] = useState(null);                                                                                                                             |
| 19 +                                                                                                                                                                                                  |
| 20 +    // Selection State                                                                                                                                                                            |
| 21 +    const [selectedApp, setSelectedApp] = useState(null);                                                                                                                                         |
| 22 +    const [details, setDetails] = useState(null);                                                                                                                                                 |
| 23 +    const [loadingDetails, setLoadingDetails] = useState(false);                                                                                                                                  |
| 24 +    const [selectedDoc, setSelectedDoc] = useState(null);                                                                                                                                         |
| 25 +                                                                                                                                                                                                  |
| 26 +    // Decision State                                                                                                                                                                             |
| 27 +    const [uwReason, setUwReason] = useState('');                                                                                                                                                 |
| 28 +    const [approvalReason, setApprovalReason] = useState('');                                                                                                                                     |
| 29 +                                                                                                                                                                                                  |
| 30 +    // === DATA FETCHING (Using authenticated api) ===                                                                                                                                            |
| 31 +    const fetchAllData = async () => {                                                                                                                                                            |
| 32 +        await Promise.all([                                                                                                                                                                       |
| 33 +            fetchApplications(),                                                                                                                                                                  |
| 34 +            fetchLoanApplications(),                                                                                                                                                              |
| 35 +            fetchOperationsSummary()                                                                                                                                                              |
| 36 +        ]);                                                                                                                                                                                       |
| 37 +    };                                                                                                                                                                                            |
| 38 +                                                                                                                                                                                                  |
| 39 +    const fetchApplications = async () => {                                                                                                                                                       |
| 40 +        try {                                                                                                                                                                                     |
| 41 +            const res = await api.get('/applications');                                                                                                                                           |
| 42 +            setApplications(res.data);                                                                                                                                                            |
| 43 +        } catch (err) {                                                                                                                                                                           |
| 44 +            console.error("Applications fetch error:", err);                                                                                                                                      |
| 45 +        }                                                                                                                                                                                         |
| 46 +    };                                                                                                                                                                                            |
| 47 +                                                                                                                                                                                                  |
| 48 +    const fetchLoanApplications = async () => {                                                                                                                                                   |
| 49 +        try {                                                                                                                                                                                     |
| 50 +            const res = await api.get('/loan-applications');                                                                                                                                      |
| 51 +            setLoanApplications(res.data);                                                                                                                                                        |
| 52 +        } catch (err) {                                                                                                                                                                           |
| 53 +            console.error("Loan applications fetch error:", err);                                                                                                                                 |
| 54 +        }                                                                                                                                                                                         |
| 55 +    };                                                                                                                                                                                            |
| 56 +                                                                                                                                                                                                  |
| 57 +    const fetchOperationsSummary = async () => {                                                                                                                                                  |
| 58 +        try {                                                                                                                                                                                     |
| 59 +            const res = await api.get('/operations/summary');                                                                                                                                     |
| 60 +            setOperationsSummary(res.data);                                                                                                                                                       |
| 61 +        } catch (err) {                                                                                                                                                                           |
| 62 +            console.error("Operations summary fetch error:", err);                                                                                                                                |
| 63 +        }                                                                                                                                                                                         |
| 64 +    };                                                                                                                                                                                            |
| 65 +                                                                                                                                                                                                  |
| 66 +    const fetchDetails = async (workflowId) => {                                                                                                                                                  |
| 67 +        setLoadingDetails(true);                                                                                                                                                                  |
| 68 +        setDetails(null);                                                                                                                                                                         |
| 69 +        try {                                                                                                                                                                                     |
| 70 +            const res = await api.get(`/status/${workflowId}`);                                                                                                                                 |
| 71 +            setDetails(res.data);                                                                                                                                                                 |
| 72 +                                                                                                                                                                                                  |
| 73 +            // Set default document to view                                                                                                                                                       |
| 74 +            if (res.data.data?.public_urls) {                                                                                                                                                     |
| 75 +                const urls = res.data.data.public_urls;                                                                                                                                           |
| 76 +                setSelectedDoc(urls.tax_document ? 'tax_document' : Object.keys(urls)[0]);                                                                                                        |
| 77 +            } else if (res.data.file_url) {                                                                                                                                                       |
| 78 +                setSelectedDoc('legacy');                                                                                                                                                         |
| 79 +            }                                                                                                                                                                                     |
| 80 +        } catch (err) {                                                                                                                                                                           |
| 81 +            console.warn("Details fetch failed:", err);                                                                                                                                           |
| 82 +        } finally {                                                                                                                                                                               |
| 83 +            setLoadingDetails(false);                                                                                                                                                             |
| 84 +        }                                                                                                                                                                                         |
| 85 +    };                                                                                                                                                                                            |
| 86 +                                                                                                                                                                                                  |
| 87 +    useEffect(() => {                                                                                                                                                                             |
| 88 +        fetchAllData();                                                                                                                                                                           |
| 89 +        const interval = setInterval(fetchAllData, 5000);                                                                                                                                         |
| 90 +        return () => clearInterval(interval);                                                                                                                                                     |
| 91 +    }, []);                                                                                                                                                                                       |
| 92 +                                                                                                                                                                                                  |
| 93 +    // === HANDLERS ===                                                                                                                                                                           |
| 94 +    const handleSelectApp = (app) => {                                                                                                                                                            |
| 95 +        setSelectedApp(app);                                                                                                                                                                      |
| 96 +        setDetails(null);                                                                                                                                                                         |
| 97 +        setSelectedDoc(null);                                                                                                                                                                     |
| 98 +        fetchDetails(app.workflow_id);                                                                                                                                                            |
| 99 +    };                                                                                                                                                                                            |
| 100 +                                                                                                                                                                                                 |
| 101 +    // Human Manager Approval (First Gate - after Lead Capture)                                                                                                                                  |
| 102 +    const handleManagerApproval = async (approved) => {                                                                                                                                          |
| 103 +        if (!selectedApp) return;                                                                                                                                                                |
| 104 +        try {                                                                                                                                                                                    |
| 105 +            await api.post('/review', {                                                                                                                                                          |
| 106 +                workflow_id: selectedApp.workflow_id,                                                                                                                                            |
| 107 +                approved: approved,                                                                                                                                                              |
| 108 +                reason: approvalReason                                                                                                                                                           |
| 109 +            });                                                                                                                                                                                  |
| 110 +            setApprovalReason('');                                                                                                                                                               |
| 111 +            fetchAllData();                                                                                                                                                                      |
| 112 +            fetchDetails(selectedApp.workflow_id);                                                                                                                                               |
| 113 +            alert(`Application ${approved ? 'APPROVED' : 'REJECTED'} successfully!`);                                                                                                          |
| 114 +        } catch (err) {                                                                                                                                                                          |
| 115 +            alert("Action failed: " + err.message);                                                                                                                                              |
| 116 +        }                                                                                                                                                                                        |
| 117 +    };                                                                                                                                                                                           |
| 118 +                                                                                                                                                                                                 |
| 119 +    // Underwriting Decision (Waiter Pattern - Second Gate)                                                                                                                                      |
| 120 +    const handleUnderwritingDecision = async (workflowId, approved) => {                                                                                                                         |
| 121 +        if (!uwReason.trim()) {                                                                                                                                                                  |
| 122 +            alert("Please provide a reason for your underwriting decision.");                                                                                                                    |
| 123 +            return;                                                                                                                                                                              |
| 124 +        }                                                                                                                                                                                        |
| 125 +        try {                                                                                                                                                                                    |
| 126 +            await api.post('/underwriting/decision', {                                                                                                                                           |
| 127 +                workflow_id: workflowId,                                                                                                                                                         |
| 128 +                approved: approved,                                                                                                                                                              |
| 129 +                reason: uwReason                                                                                                                                                                 |
| 130 +            });                                                                                                                                                                                  |
| 131 +            setUwReason('');                                                                                                                                                                     |
| 132 +            fetchAllData();                                                                                                                                                                      |
| 133 +                                                                                                                                                                                                 |
| 134 +            // Optimistic update                                                                                                                                                                 |
| 135 +            if (selectedApp?.workflow_id === workflowId) {                                                                                                                                       |
| 136 +                setSelectedApp(prev => ({                                                                                                                                                        |
| 137 +                    ...prev,                                                                                                                                                                     |
| 138 +                    is_locked: false,                                                                                                                                                            |
| 139 +                    underwriting_decision: approved ? 'approved' : 'rejected'                                                                                                                    |
| 140 +                }));                                                                                                                                                                             |
| 141 +            }                                                                                                                                                                                    |
| 142 +            alert(`Underwriting decision: ${approved ? 'APPROVED' : 'REJECTED'}`);                                                                                                             |
| 143 +        } catch (err) {                                                                                                                                                                          |
| 144 +            alert("Failed to submit decision: " + err.message);                                                                                                                                  |
| 145 +        }                                                                                                                                                                                        |
| 146 +    };                                                                                                                                                                                           |
| 147 +                                                                                                                                                                                                 |
| 148 +    // Delete application                                                                                                                                                                        |
| 149 +    const handleDelete = async (workflowId) => {                                                                                                                                                 |
| 150 +        if (!confirm("Delete this application? This cannot be undone.")) return;                                                                                                                 |
| 151 +        try {                                                                                                                                                                                    |
| 152 +            await api.delete(`/application/${workflowId}`);                                                                                                                                    |
| 153 +            setDetails(null);                                                                                                                                                                    |
| 154 +            setSelectedApp(null);                                                                                                                                                                |
| 155 +            fetchAllData();                                                                                                                                                                      |
| 156 +        } catch (err) {                                                                                                                                                                          |
| 157 +            alert("Delete failed: " + err.message);                                                                                                                                              |
| 158 +        }                                                                                                                                                                                        |
| 159 +    };                                                                                                                                                                                           |
| 160 +                                                                                                                                                                                                 |
| 161 +    // === HELPERS ===                                                                                                                                                                           |
| 162 +    const getStatusColor = (status) => {                                                                                                                                                         |
| 163 +        const s = status?.toLowerCase()                                                                                                                                                          |
| 164 +        if (s.includes("funded")                                                                                                                                                                 |
| 165 +        if (s.includes("lock")                                                                                                                                                                   |
| 166 +        if (s.includes("reject")) return "bg-red-100 text-red-800 border-red-200";                                                                                                               |
| 167 +        if (s.includes("process")) return "bg-blue-100 text-blue-800 border-blue-200";                                                                                                           |
| 168 +        return "bg-gray-100 text-gray-800 border-gray-200";                                                                                                                                      |
| 169 +    };                                                                                                                                                                                           |
| 170 +                                                                                                                                                                                                 |
| 171 +    const getLockBadge = (isLocked) => {                                                                                                                                                         |
| 172 +        if (isLocked) {                                                                                                                                                                          |
| 173 +            return (                                                                                                                                                                             |
| 174 +`<span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-800">`                                                                     |
| 175 +`<Lock size={12} />` LOCKED                                                                                                                                                                    |
| 176 +                                                                                                                                                                                                 |
| 177 +            );                                                                                                                                                                                   |
| 178 +        }                                                                                                                                                                                        |
| 179 +        return (                                                                                                                                                                                 |
| 180 +`<span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-green-100 text-green-800">`                                                                       |
| 181 +`<Unlock size={12} />` Active                                                                                                                                                                  |
| 182 +                                                                                                                                                                                                 |
| 183 +        );                                                                                                                                                                                       |
| 184 +    };                                                                                                                                                                                           |
| 185 +                                                                                                                                                                                                 |
| 186 +    // Check if app needs initial manager approval (before processing)                                                                                                                           |
| 187 +    const needsManagerApproval = (app, detailsData) => {                                                                                                                                         |
| 188 +        const status = (app?.status                                                                                                                                                              |
| 189 +        const stage = (app?.loan_stage                                                                                                                                                           |
| 190 +        return status === 'submitted'                                                                                                                                                            |
| 191 +    };                                                                                                                                                                                           |
| 192 +                                                                                                                                                                                                 |
| 193 +    // Check if app is waiting for signature                                                                                                                                                     |
| 194 +    const needsSignature = (app, detailsData) => {                                                                                                                                               |
| 195 +        const status = (app?.status                                                                                                                                                              |
| 196 +        return status.includes('waiting for signature');                                                                                                                                         |
| 197 +    };                                                                                                                                                                                           |
| 198 +                                                                                                                                                                                                 |
| 199 +    // Extract data safely                                                                                                                                                                       |
| 200 +    const info = details?.data?.applicant_info                                                                                                                                                   |
| 201 +    const analysis = details?.loan_metadata?.analysis                                                                                                                                            |
| 202 +    const urls = details?.data?.public_urls                                                                                                                                                      |
| 203 +                                                                                                                                                                                                 |
| 204 +    return (                                                                                                                                                                                     |
| 205 +`<div className="flex h-[calc(100vh-64px)] bg-gray-50 overflow-hidden">`                                                                                                                       |
| 206 +            {/* === LEFT SIDEBAR === */}                                                                                                                                                         |
| 207 +`<div className="w-1/3 max-w-md bg-white border-r flex flex-col shadow-lg z-10">`                                                                                                              |
| 208 +                {/* View Mode Toggle */}                                                                                                                                                         |
| 209 +`<div className="p-3 bg-gray-100 border-b flex gap-2">`                                                                                                                                        |
| 210 +                    <button                                                                                                                                                                      |
| 211 +                        onClick={() => { setViewMode('operations'); setSelectedApp(null); setDetails(null); }}                                                                                   |
| 212 +                        className={`flex-1 py-2 px-3 rounded-lg text-sm font-bold transition ${                                                                                                  |
| 213 +                            viewMode === 'operations' ? 'bg-white text-purple-600 shadow' : 'text-gray-500 hover:bg-gray-200'                                                                    |
| 214 +                        }`}                                                                                                                                                                      |
| 215 +                    >                                                                                                                                                                            |
| 216 +                        <Database size={14} className="inline mr-1" /> Live Ops                                                                                                                  |
| 217 +`</button>`                                                                                                                                                                                    |
| 218 +                    <button                                                                                                                                                                      |
| 219 +                        onClick={() => { setViewMode('applications'); setSelectedApp(null); setDetails(null); }}                                                                                 |
| 220 +                        className={`flex-1 py-2 px-3 rounded-lg text-sm font-bold transition ${                                                                                                  |
| 221 +                            viewMode === 'applications' ? 'bg-white text-blue-600 shadow' : 'text-gray-500 hover:bg-gray-200'                                                                    |
| 222 +                        }`}                                                                                                                                                                      |
| 223 +                    >                                                                                                                                                                            |
| 224 +                        <LayoutDashboard size={14} className="inline mr-1" /> Legacy                                                                                                             |
| 225 +`</button>`                                                                                                                                                                                    |
| 226 +`</div>`                                                                                                                                                                                       |
| 227 +                                                                                                                                                                                                 |
| 228 +                {/* Header with Refresh */}                                                                                                                                                      |
| 229 +`<div className="p-4 border-b flex justify-between items-center bg-gray-50">`                                                                                                                  |
| 230 +`<h2 className="font-bold text-gray-700 flex items-center gap-2">`                                                                                                                             |
| 231 +                        {viewMode === 'operations' ? (                                                                                                                                           |
| 232 +                            <>`<Database size={18} />` Live Operations</>                                                                                                                      |
| 233 +                        ) : (                                                                                                                                                                    |
| 234 +                            <>`<LayoutDashboard size={18} />` Applications</>                                                                                                                  |
| 235 +                        )}                                                                                                                                                                       |
| 236 +`</h2>`                                                                                                                                                                                        |
| 237 +                    <button                                                                                                                                                                      |
| 238 +                        onClick={fetchAllData}                                                                                                                                                   |
| 239 +                        className="p-2 hover:bg-gray-200 rounded-full transition"                                                                                                                |
| 240 +                        title="Refresh"                                                                                                                                                          |
| 241 +                    >                                                                                                                                                                            |
| 242 +`<RefreshCw size={16} />`                                                                                                                                                                      |
| 243 +`</button>`                                                                                                                                                                                    |
| 244 +`</div>`                                                                                                                                                                                       |
| 245 +                                                                                                                                                                                                 |
| 246 +                {/* Application List */}                                                                                                                                                         |
| 247 +`<div className="flex-1 overflow-y-auto">`                                                                                                                                                     |
| 248 +                    {viewMode === 'operations' ? (                                                                                                                                               |
| 249 +                        <>                                                                                                                                                                       |
| 250 +                            {/* Live Ops Summary Cards */}                                                                                                                                       |
| 251 +                            {operationsSummary && (                                                                                                                                              |
| 252 +`<div className="grid grid-cols-3 gap-2 p-3 bg-gradient-to-r from-purple-50 to-blue-50 border-b text-center">`                                                                                 |
| 253 +`<div className="bg-white p-2 rounded-lg shadow-sm">`                                                                                                                                          |
| 254 +`<div className="text-xl font-bold text-blue-600">`{operationsSummary.total_applications}`</div>`                                                                                            |
| 255 +`<div className="text-[10px] text-gray-500 uppercase">`Total`</div>`                                                                                                                         |
| 256 +`</div>`                                                                                                                                                                                       |
| 257 +`<div className="bg-white p-2 rounded-lg shadow-sm">`                                                                                                                                          |
| 258 +`<div className="text-xl font-bold text-orange-600">`{operationsSummary.locked_waiting}`</div>`                                                                                              |
| 259 +`<div className="text-[10px] text-gray-500 uppercase">`Locked`</div>`                                                                                                                        |
| 260 +`</div>`                                                                                                                                                                                       |
| 261 +`<div className="bg-white p-2 rounded-lg shadow-sm">`                                                                                                                                          |
| 262 +`<div className="text-xl font-bold text-green-600">`{operationsSummary.funded}`</div>`                                                                                                       |
| 263 +`<div className="text-[10px] text-gray-500 uppercase">`Funded`</div>`                                                                                                                        |
| 264 +`</div>`                                                                                                                                                                                       |
| 265 +`</div>`                                                                                                                                                                                       |
| 266 +                            )}                                                                                                                                                                   |
| 267 +                                                                                                                                                                                                 |
| 268 +                            {/* Loan Applications List (DB) */}                                                                                                                                  |
| 269 +                            {loanApplications.length === 0 ? (                                                                                                                                   |
| 270 +`<div className="p-8 text-center text-gray-400">`                                                                                                                                              |
| 271 +                                    <Database size={40} className="mx-auto mb-2 opacity-30" />                                                                                                   |
| 272 +                                    No loan records in database                                                                                                                                  |
| 273 +`</div>`                                                                                                                                                                                       |
| 274 +                            ) : (                                                                                                                                                                |
| 275 +                                loanApplications.map(app => (                                                                                                                                    |
| 276 +                                    <div                                                                                                                                                         |
| 277 +                                        key={app.id}                                                                                                                                             |
| 278 +                                        onClick={() => handleSelectApp(app)}                                                                                                                     |
| 279 +                                        className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-all group                                                                            |
| 280 +                                            ${selectedApp?.id === app.id ? 'bg-purple-50 border-l-4 border-l-purple-500' : 'border-l-4 border-l-transparent'}                                    |
| 281 +                                            ${app.is_locked ? 'bg-orange-50/50' : ''}                                                                                                            |
| 282 +                                        `}                                                                                                                                                       |
| 283 +                                    >                                                                                                                                                            |
| 284 +`<div className="flex justify-between items-center mb-2">`                                                                                                                                     |
| 285 +`<span className="font-mono text-[10px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded">`                                                                                                   |
| 286 +                                                DB:{app.id?.slice(0, 8)}                                                                                                                         |
| 287 +                                                                                                                                                                                                 |
| 288 +                                            {getLockBadge(app.is_locked)}                                                                                                                        |
| 289 +`</div>`                                                                                                                                                                                       |
| 290 +`<div className="font-bold text-gray-800">`{app.borrower_name}`</div>`                                                                                                                       |
| 291 +`<div className="text-sm text-gray-600 mb-2">`${app.loan_amount?.toLocaleString()                                                                                                              |
| 292 +`<div className="flex flex-wrap gap-1">`                                                                                                                                                       |
| 293 +                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(app.status)}`}>                                                         |
| 294 +                                                {app.status}                                                                                                                                     |
| 295 +                                                                                                                                                                                                 |
| 296 +                                            {app.loan_stage && (                                                                                                                                 |
| 297 +`<span className="px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">`                                                                                                                     |
| 298 +                                                    {app.loan_stage}                                                                                                                             |
| 299 +                                                                                                                                                                                                 |
| 300 +                                            )}                                                                                                                                                   |
| 301 +`</div>`                                                                                                                                                                                       |
| 302 +                                        {app.underwriting_decision && (                                                                                                                          |
| 303 +`<div className="mt-2 text-xs">`                                                                                                                                                               |
| 304 +                                                <span className={`font-bold ${app.underwriting_decision === 'approved' ? 'text-green-600' : 'text-red-600'}`}>                                 |
| 305 +                                                    UW: {app.underwriting_decision.toUpperCase()}                                                                                                |
| 306 +                                                                                                                                                                                                 |
| 307 +`</div>`                                                                                                                                                                                       |
| 308 +                                        )}                                                                                                                                                       |
| 309 +`</div>`                                                                                                                                                                                       |
| 310 +                                ))                                                                                                                                                               |
| 311 +                            )}                                                                                                                                                                   |
| 312 +                        </>                                                                                                                                                                      |
| 313 +                    ) : (                                                                                                                                                                        |
| 314 +                        /* Legacy Applications List */                                                                                                                                           |
| 315 +                        applications.length === 0 ? (                                                                                                                                            |
| 316 +`<div className="p-8 text-center text-gray-400">`                                                                                                                                              |
| 317 +                                No applications found                                                                                                                                            |
| 318 +`</div>`                                                                                                                                                                                       |
| 319 +                        ) : (                                                                                                                                                                    |
| 320 +                            applications.map(app => (                                                                                                                                            |
| 321 +                                <div                                                                                                                                                             |
| 322 +                                    key={app.workflow_id}                                                                                                                                        |
| 323 +                                    onClick={() => handleSelectApp(app)}                                                                                                                         |
| 324 +                                    className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-all group                                                                                |
| 325 +                                        ${selectedApp?.workflow_id === app.workflow_id ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'}                          |
| 326 +                                    `}                                                                                                                                                           |
| 327 +                                >                                                                                                                                                                |
| 328 +`<div className="flex justify-between items-start mb-1">`                                                                                                                                      |
| 329 +`<span className="font-mono text-xs text-gray-500 truncate">`                                                                                                                                  |
| 330 +                                            {app.workflow_id.split('-').pop()}                                                                                                                   |
| 331 +                                                                                                                                                                                                 |
| 332 +                                        <button                                                                                                                                                  |
| 333 +                                            onClick={(e) => { e.stopPropagation(); handleDelete(app.workflow_id); }}                                                                             |
| 334 +                                            className="text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition"                                                             |
| 335 +                                        >                                                                                                                                                        |
| 336 +`<Trash2 size={14} />`                                                                                                                                                                         |
| 337 +`</button>`                                                                                                                                                                                    |
| 338 +`</div>`                                                                                                                                                                                       |
| 339 +                                    <div className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-2 ${getStatusColor(app.status)}`}>                                                |
| 340 +                                        {app.status}                                                                                                                                             |
| 341 +`</div>`                                                                                                                                                                                       |
| 342 +                                    {app.loan_stage && (                                                                                                                                         |
| 343 +`<div className="text-xs text-gray-500">`Stage: {app.loan_stage}`</div>`                                                                                                                     |
| 344 +                                    )}                                                                                                                                                           |
| 345 +`</div>`                                                                                                                                                                                       |
| 346 +                            ))                                                                                                                                                                   |
| 347 +                        )                                                                                                                                                                        |
| 348 +                    )}                                                                                                                                                                           |
| 349 +`</div>`                                                                                                                                                                                       |
| 350 +`</div>`                                                                                                                                                                                       |
| 351 +                                                                                                                                                                                                 |
| 352 +            {/* === MAIN CONTENT === */}                                                                                                                                                         |
| 353 +`<div className="flex-1 bg-gray-100 p-6 overflow-hidden flex flex-col">`                                                                                                                       |
| 354 +                {selectedApp && (details                                                                                                                                                         |
| 355 +`<div className="h-full flex gap-6">`                                                                                                                                                          |
| 356 +                        {/* LEFT: Info & Actions */}                                                                                                                                             |
| 357 +`<div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-2">`                                                                                                                            |
| 358 +                            {/* Header Card */}                                                                                                                                                  |
| 359 +`<div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">`                                                                                                                   |
| 360 +`<div className="flex justify-between items-start">`                                                                                                                                           |
| 361 +`<div>`                                                                                                                                                                                        |
| 362 +`<h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">`                                                                                                                    |
| 363 +                                            {selectedApp.borrower_name                                                                                                                           |
| 364 +                                            {selectedApp.is_locked !== undefined && (                                                                                                            |
| 365 +                                                selectedApp.is_locked ?                                                                                                                          |
| 366 +`<Lock className="text-orange-500" size={20} />` :                                                                                                                                             |
| 367 +`<Unlock className="text-green-500" size={20} />`                                                                                                                                              |
| 368 +                                            )}                                                                                                                                                   |
| 369 +`</h1>`                                                                                                                                                                                        |
| 370 +`<p className="text-gray-500 text-sm mt-1 flex items-center gap-2">`                                                                                                                           |
| 371 +`<FileText size={14} />` {selectedApp.workflow_id}                                                                                                                                             |
| 372 +`</p>`                                                                                                                                                                                         |
| 373 +`<div className="flex gap-2 mt-2">`                                                                                                                                                            |
| 374 +                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(selectedApp.status                                                          |
| 375 +                                                {selectedApp.status                                                                                                                              |
| 376 +                                                                                                                                                                                                 |
| 377 +                                            {(selectedApp.loan_stage                                                                                                                             |
| 378 +`<span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">`                                                                                                                       |
| 379 +                                                    {selectedApp.loan_stage                                                                                                                      |
| 380 +                                                                                                                                                                                                 |
| 381 +                                            )}                                                                                                                                                   |
| 382 +`</div>`                                                                                                                                                                                       |
| 383 +`</div>`                                                                                                                                                                                       |
| 384 +`<div className="text-right">`                                                                                                                                                                 |
| 385 +`<div className="text-2xl font-bold text-gray-800">`                                                                                                                                           |
| 386 +                                            ${(selectedApp.loan_amount                                                                                                                           |
| 387 +`</div>`                                                                                                                                                                                       |
| 388 +`<div className="text-xs text-gray-500">`Loan Amount`</div>`                                                                                                                                 |
| 389 +`</div>`                                                                                                                                                                                       |
| 390 +`</div>`                                                                                                                                                                                       |
| 391 +`</div>`                                                                                                                                                                                       |
| 392 +                                                                                                                                                                                                 |
| 393 +                            {/* GATE 1: Manager Approval Panel (Initial Review) */}                                                                                                              |
| 394 +                            {needsManagerApproval(selectedApp, details) && (                                                                                                                     |
| 395 +`<div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 shadow-sm">`                                                                                                               |
| 396 +`<h3 className="text-lg font-bold text-blue-800 mb-2 flex items-center gap-2">`                                                                                                                |
| 397 +`<User size={20} />` Manager Review Required                                                                                                                                                   |
| 398 +`</h3>`                                                                                                                                                                                        |
| 399 +`<p className="text-sm text-blue-700 mb-4">`                                                                                                                                                   |
| 400 +                                        Review the AI analysis and documents, then approve or reject this application.                                                                           |
| 401 +`</p>`                                                                                                                                                                                         |
| 402 +                                    <textarea                                                                                                                                                    |
| 403 +                                        className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-blue-200"                                                                           |
| 404 +                                        placeholder="Optional: Add notes for your decision..."                                                                                                   |
| 405 +                                        value={approvalReason}                                                                                                                                   |
| 406 +                                        onChange={e => setApprovalReason(e.target.value)}                                                                                                        |
| 407 +                                        rows={2}                                                                                                                                                 |
| 408 +                                    />                                                                                                                                                           |
| 409 +`<div className="flex gap-3">`                                                                                                                                                                 |
| 410 +                                        <button                                                                                                                                                  |
| 411 +                                            onClick={() => handleManagerApproval(true)}                                                                                                          |
| 412 +                                            className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 shadow flex items-center justify-center gap-2"                |
| 413 +                                        >                                                                                                                                                        |
| 414 +`<CheckCircle size={18} />` Approve                                                                                                                                                            |
| 415 +`</button>`                                                                                                                                                                                    |
| 416 +                                        <button                                                                                                                                                  |
| 417 +                                            onClick={() => handleManagerApproval(false)}                                                                                                         |
| 418 +                                            className="flex-1 bg-white text-red-600 border-2 border-red-200 py-3 rounded-lg font-bold hover:bg-red-50 flex items-center justify-center gap-2"    |
| 419 +                                        >                                                                                                                                                        |
| 420 +`<XCircle size={18} />` Reject                                                                                                                                                                 |
| 421 +`</button>`                                                                                                                                                                                    |
| 422 +`</div>`                                                                                                                                                                                       |
| 423 +`</div>`                                                                                                                                                                                       |
| 424 +                            )}                                                                                                                                                                   |
| 425 +                                                                                                                                                                                                 |
| 426 +                            {/* GATE 2: Underwriting Decision Panel (Waiter Pattern) */}                                                                                                         |
| 427 +                            {selectedApp.is_locked && (                                                                                                                                          |
| 428 +`<div className="bg-orange-50 border-2 border-orange-200 rounded-xl p-6 shadow-sm">`                                                                                                           |
| 429 +`<h3 className="text-lg font-bold text-orange-800 mb-2 flex items-center gap-2">`                                                                                                              |
| 430 +`<Gavel size={20} />` Underwriting Decision Required                                                                                                                                           |
| 431 +`</h3>`                                                                                                                                                                                        |
| 432 +`<div className="bg-white p-3 rounded border border-orange-100 mb-4 text-sm text-gray-600">`                                                                                                   |
| 433 +`<Lock className="inline mr-2 text-orange-500" size={14} />`                                                                                                                                   |
| 434 +                                        Workflow is`<strong>`PAUSED`</strong>`. Your decision will unlock it and continue processing.                                                        |
| 435 +`</div>`                                                                                                                                                                                       |
| 436 +                                    <textarea                                                                                                                                                    |
| 437 +                                        className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-orange-200"                                                                         |
| 438 +                                        placeholder="Enter reason (e.g., 'Income verified, DTI acceptable')..."                                                                                  |
| 439 +                                        value={uwReason}                                                                                                                                         |
| 440 +                                        onChange={e => setUwReason(e.target.value)}                                                                                                              |
| 441 +                                        rows={2}                                                                                                                                                 |
| 442 +                                    />                                                                                                                                                           |
| 443 +`<div className="flex gap-3">`                                                                                                                                                                 |
| 444 +                                        <button                                                                                                                                                  |
| 445 +                                            onClick={() => handleUnderwritingDecision(selectedApp.workflow_id, true)}                                                                            |
| 446 +                                            className="flex-1 bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 shadow flex items-center justify-center gap-2"                |
| 447 +                                        >                                                                                                                                                        |
| 448 +`<CheckCircle size={18} />` Approve & Continue                                                                                                                                                 |
| 449 +`</button>`                                                                                                                                                                                    |
| 450 +                                        <button                                                                                                                                                  |
| 451 +                                            onClick={() => handleUnderwritingDecision(selectedApp.workflow_id, false)}                                                                           |
| 452 +                                            className="flex-1 bg-white text-red-600 border-2 border-red-200 py-3 rounded-lg font-bold hover:bg-red-50 flex items-center justify-center gap-2"    |
| 453 +                                        >                                                                                                                                                        |
| 454 +`<XCircle size={18} />` Reject                                                                                                                                                                 |
| 455 +`</button>`                                                                                                                                                                                    |
| 456 +`</div>`                                                                                                                                                                                       |
| 457 +`</div>`                                                                                                                                                                                       |
| 458 +                            )}                                                                                                                                                                   |
| 459 +                                                                                                                                                                                                 |
| 460 +                            {/* Signature Waiting Notice */}                                                                                                                                     |
| 461 +                            {needsSignature(selectedApp, details) && (                                                                                                                           |
| 462 +`<div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6 shadow-sm">`                                                                                                           |
| 463 +`<h3 className="text-lg font-bold text-yellow-800 mb-2 flex items-center gap-2">`                                                                                                              |
| 464 +`<PenTool size={20} />` Waiting for Borrower Signature                                                                                                                                         |
| 465 +`</h3>`                                                                                                                                                                                        |
| 466 +`<p className="text-sm text-yellow-700">`                                                                                                                                                      |
| 467 +                                        Initial Disclosures have been generated. Waiting for the borrower to sign.                                                                               |
| 468 +`</p>`                                                                                                                                                                                         |
| 469 +`</div>`                                                                                                                                                                                       |
| 470 +                            )}                                                                                                                                                                   |
| 471 +                                                                                                                                                                                                 |
| 472 +                            {/* Funded Success Card */}                                                                                                                                          |
| 473 +                            {!selectedApp.is_locked && (selectedApp.status                                                                                                                       |
| 474 +`<div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 shadow-sm">`                                                                                                             |
| 475 +`<h3 className="text-lg font-bold text-green-800 mb-2 flex items-center gap-2">`                                                                                                               |
| 476 +`<CheckCircle size={20} />` Loan Funded Successfully!                                                                                                                                          |
| 477 +`</h3>`                                                                                                                                                                                        |
| 478 +`<p className="text-sm text-green-700">`                                                                                                                                                       |
| 479 +                                        This loan has been fully processed and funded.                                                                                                           |
| 480 +`</p>`                                                                                                                                                                                         |
| 481 +`</div>`                                                                                                                                                                                       |
| 482 +                            )}                                                                                                                                                                   |
| 483 +                                                                                                                                                                                                 |
| 484 +                            {/* AI Analysis Card */}                                                                                                                                             |
| 485 +`<div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">`                                                                                                                   |
| 486 +`<h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">`                                                                                                                |
| 487 +                                    <Shield size={20} className="text-blue-600" /> AI Verification Analysis                                                                                      |
| 488 +`</h3>`                                                                                                                                                                                        |
| 489 +                                                                                                                                                                                                 |
| 490 +                                {(analysis.verified_income                                                                                                                                       |
| 491 +`<div className="space-y-4">`                                                                                                                                                                  |
| 492 +                                        {/* Income Verification */}                                                                                                                              |
| 493 +                                        <div className={`p-4 rounded-lg border ${                                                                                                                |
| 494 +                                            analysis.income_mismatch ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'                                                               |
| 495 +                                        }`}>                                                                                                                                                     |
| 496 +`<div className="flex justify-between items-center mb-2">`                                                                                                                                     |
| 497 +`<span className="text-sm font-bold text-gray-700">`Income Verification                                                                                                                        |
| 498 +                                                {analysis.income_mismatch ? (                                                                                                                    |
| 499 +`<span className="text-red-600 text-xs font-bold flex items-center gap-1">`                                                                                                                    |
| 500 +`<AlertTriangle size={12} />` MISMATCH                                                                                                                                                         |
| 501 +                                                                                                                                                                                                 |
| 502 +                                                ) : (                                                                                                                                            |
| 503 +`<span className="text-green-600 text-xs font-bold flex items-center gap-1">`                                                                                                                  |
| 504 +`<CheckCircle size={12} />` VERIFIED                                                                                                                                                           |
| 505 +                                                                                                                                                                                                 |
| 506 +                                                )}                                                                                                                                               |
| 507 +`</div>`                                                                                                                                                                                       |
| 508 +`<div className="grid grid-cols-2 gap-4">`                                                                                                                                                     |
| 509 +`<div>`                                                                                                                                                                                        |
| 510 +`<div className="text-xs text-gray-500">`Stated Income`</div>`                                                                                                                               |
| 511 +`<div className="text-lg font-bold">`${(analysis.stated_income                                                                                                                                 |
| 512 +`</div>`                                                                                                                                                                                       |
| 513 +`<div>`                                                                                                                                                                                        |
| 514 +`<div className="text-xs text-gray-500">`Verified Income`</div>`                                                                                                                             |
| 515 +`<div className="text-lg font-bold">`${(analysis.verified_income                                                                                                                               |
| 516 +`</div>`                                                                                                                                                                                       |
| 517 +`</div>`                                                                                                                                                                                       |
| 518 +`</div>`                                                                                                                                                                                       |
| 519 +                                                                                                                                                                                                 |
| 520 +                                        {/* Confidence Score */}                                                                                                                                 |
| 521 +`<div className="p-4 rounded-lg bg-gray-50 border">`                                                                                                                                           |
| 522 +`<div className="flex justify-between items-center">`                                                                                                                                          |
| 523 +`<span className="text-sm font-bold text-gray-700">`AI Confidence                                                                                                                              |
| 524 +                                                <span className={`text-lg font-bold ${                                                                                                           |
| 525 +                                                    (analysis.confidence                                                                                                                         |
| 526 +                                                }`}>                                                                                                                                             |
| 527 +                                                    {((analysis.confidence                                                                                                                       |
| 528 +                                                                                                                                                                                                 |
| 529 +`</div>`                                                                                                                                                                                       |
| 530 +`</div>`                                                                                                                                                                                       |
| 531 +`</div>`                                                                                                                                                                                       |
| 532 +                                ) : (                                                                                                                                                            |
| 533 +`<div className="p-4 bg-gray-50 rounded-lg text-center text-gray-400">`                                                                                                                        |
| 534 +                                        <Shield size={32} className="mx-auto mb-2 opacity-30" />                                                                                                 |
| 535 +`<p>`AI analysis not available yet`</p>`                                                                                                                                                     |
| 536 +`</div>`                                                                                                                                                                                       |
| 537 +                                )}                                                                                                                                                               |
| 538 +`</div>`                                                                                                                                                                                       |
| 539 +                                                                                                                                                                                                 |
| 540 +                            {/* DB Record Info (Live Ops only) */}                                                                                                                               |
| 541 +                            {viewMode === 'operations' && selectedApp.id && (                                                                                                                    |
| 542 +`<div className="bg-purple-50 p-4 rounded-xl border border-purple-200">`                                                                                                                       |
| 543 +`<h3 className="text-sm font-bold text-purple-800 mb-3 flex items-center gap-2">`                                                                                                              |
| 544 +`<Database size={16} />` Database Record                                                                                                                                                       |
| 545 +`</h3>`                                                                                                                                                                                        |
| 546 +`<div className="grid grid-cols-2 gap-3 text-sm">`                                                                                                                                             |
| 547 +`<div>`                                                                                                                                                                                        |
| 548 +`<span className="text-purple-600 font-medium">`DB ID:                                                                                                                                         |
| 549 +`<span className="ml-2 font-mono text-xs bg-white px-2 py-1 rounded">`{selectedApp.id?.slice(0, 12)}...                                                                                        |
| 550 +`</div>`                                                                                                                                                                                       |
| 551 +`<div>`                                                                                                                                                                                        |
| 552 +`<span className="text-purple-600 font-medium">`Lock:                                                                                                                                          |
| 553 +`<span className="ml-2">`{selectedApp.is_locked ? '🔒 Locked' : '🔓 Unlocked'}                                                                                                                 |
| 554 +`</div>`                                                                                                                                                                                       |
| 555 +`<div>`                                                                                                                                                                                        |
| 556 +`<span className="text-purple-600 font-medium">`Stage:                                                                                                                                         |
| 557 +`<span className="ml-2">`{selectedApp.loan_stage                                                                                                                                               |
| 558 +`</div>`                                                                                                                                                                                       |
| 559 +`<div>`                                                                                                                                                                                        |
| 560 +`<span className="text-purple-600 font-medium">`UW Decision:                                                                                                                                   |
| 561 +                                            <span className={`ml-2 font-bold ${                                                                                                                  |
| 562 +                                                selectedApp.underwriting_decision === 'approved' ? 'text-green-600' :                                                                            |
| 563 +                                                selectedApp.underwriting_decision === 'rejected' ? 'text-red-600' : 'text-gray-400'                                                              |
| 564 +                                            }`}>                                                                                                                                                 |
| 565 +                                                {selectedApp.underwriting_decision?.toUpperCase()                                                                                                |
| 566 +                                                                                                                                                                                                 |
| 567 +`</div>`                                                                                                                                                                                       |
| 568 +`</div>`                                                                                                                                                                                       |
| 569 +                                    {selectedApp.underwriting_decision_reason && (                                                                                                               |
| 570 +`<div className="mt-3 p-2 bg-white rounded text-sm">`                                                                                                                                          |
| 571 +`<span className="text-purple-600 font-medium">`Reason:                                                                                                                                        |
| 572 +`<span className="text-gray-700">`{selectedApp.underwriting_decision_reason}                                                                                                                   |
| 573 +`</div>`                                                                                                                                                                                       |
| 574 +                                    )}                                                                                                                                                           |
| 575 +`</div>`                                                                                                                                                                                       |
| 576 +                            )}                                                                                                                                                                   |
| 577 +`</div>`                                                                                                                                                                                       |
| 578 +                                                                                                                                                                                                 |
| 579 +                        {/* RIGHT: Document Viewer */}                                                                                                                                           |
| 580 +`<div className="w-[500px] bg-white rounded-xl shadow-lg border border-gray-200 flex flex-col overflow-hidden">`                                                                               |
| 581 +                            {/* Document Tabs */}                                                                                                                                                |
| 582 +`<div className="p-3 bg-gray-100 border-b flex justify-between items-center">`                                                                                                                 |
| 583 +`<div className="flex gap-1 flex-wrap">`                                                                                                                                                       |
| 584 +                                    {Object.keys(urls).length > 0 ? (                                                                                                                            |
| 585 +                                        Object.keys(urls).map(key => (                                                                                                                           |
| 586 +                                            <button                                                                                                                                              |
| 587 +                                                key={key}                                                                                                                                        |
| 588 +                                                onClick={() => setSelectedDoc(key)}                                                                                                              |
| 589 +                                                className={`px-3 py-1.5 text-xs font-bold rounded-md transition capitalize                                                                       |
| 590 +                                                    ${selectedDoc === key ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}                                            |
| 591 +                                                `}                                                                                                                                               |
| 592 +                                            >                                                                                                                                                    |
| 593 +                                                {key.replace('_document', '').replace('_', ' ')}                                                                                               |
| 594 +`</button>`                                                                                                                                                                                    |
| 595 +                                        ))                                                                                                                                                       |
| 596 +                                    ) : (                                                                                                                                                        |
| 597 +`<span className="text-xs font-bold text-gray-500 px-2">`Documents                                                                                                                             |
| 598 +                                    )}                                                                                                                                                           |
| 599 +`</div>`                                                                                                                                                                                       |
| 600 +                                {selectedDoc && urls[selectedDoc] && (                                                                                                                           |
| 601 +                                    <a                                                                                                                                                           |
| 602 +                                        href={`${API_URL}${urls[selectedDoc]}`}                                                                                                                |
| 603 +                                        target="_blank"                                                                                                                                          |
| 604 +                                        rel="noreferrer"                                                                                                                                         |
| 605 +                                        className="text-gray-400 hover:text-blue-600 p-1"                                                                                                        |
| 606 +                                        title="Open in new tab"                                                                                                                                  |
| 607 +                                    >                                                                                                                                                            |
| 608 +`<ExternalLink size={16} />`                                                                                                                                                                   |
| 609 +`</a>`                                                                                                                                                                                         |
| 610 +                                )}                                                                                                                                                               |
| 611 +`</div>`                                                                                                                                                                                       |
| 612 +                                                                                                                                                                                                 |
| 613 +                            {/* PDF Viewer */}                                                                                                                                                   |
| 614 +                            {selectedDoc && urls[selectedDoc] ? (                                                                                                                                |
| 615 +                                <iframe                                                                                                                                                          |
| 616 +                                    src={`${API_URL}${urls[selectedDoc]}`}                                                                                                                     |
| 617 +                                    className="flex-1 w-full h-full bg-slate-50"                                                                                                                 |
| 618 +                                    title="Document Viewer"                                                                                                                                      |
| 619 +                                />                                                                                                                                                               |
| 620 +                            ) : (                                                                                                                                                                |
| 621 +`<div className="flex-1 flex flex-col items-center justify-center text-gray-300">`                                                                                                             |
| 622 +                                    <FileText size={48} className="mb-4 opacity-20" />                                                                                                           |
| 623 +`<p>`Select a document to preview`</p>`                                                                                                                                                      |
| 624 +`</div>`                                                                                                                                                                                       |
| 625 +                            )}                                                                                                                                                                   |
| 626 +`</div>`                                                                                                                                                                                       |
| 627 +`</div>`                                                                                                                                                                                       |
| 628 +                ) : (                                                                                                                                                                            |
| 629 +                    /* Empty State */                                                                                                                                                            |
| 630 +`<div className="h-full flex flex-col items-center justify-center text-gray-400">`                                                                                                             |
| 631 +                        {loadingDetails ? (                                                                                                                                                      |
| 632 +`<RefreshCw className="animate-spin mb-4" size={48} />`                                                                                                                                        |
| 633 +                        ) : (                                                                                                                                                                    |
| 634 +                            <>                                                                                                                                                                   |
| 635 +                                <Database size={64} className="mb-6 opacity-10" />                                                                                                               |
| 636 +`<h2 className="text-xl font-bold text-gray-600">`Manager Dashboard`</h2>`                                                                                                                   |
| 637 +`<p className="text-gray-500 max-w-sm mt-2 text-center">`                                                                                                                                      |
| 638 +                                    Select an application from the sidebar to review, make decisions, and view documents.                                                                        |
| 639 +`</p>`                                                                                                                                                                                         |
| 640 +                            </>                                                                                                                                                                  |
| 641 +                        )}                                                                                                                                                                       |
| 642 +`</div>`                                                                                                                                                                                       |
| 643 +                )}                                                                                                                                                                               |
| 644 +`</div>`                                                                                                                                                                                       |
| 645 +`</div>`                                                                                                                                                                                       |
| 646 +    );                                                                                                                                                                                           |
| 647 +}                                                                                                                                                                                                |

● Now let me delete the unused components/ManagerDashboard.jsx file:

● Bash(rm "C:\Confer Part Time\GIT PROJECTS\Temporal Project\temporal-loan-python\frontend\src\components\ManagerDashboard.jsx")
  ⎿  (No content)

● Searched for 1 pattern (ctrl+o to expand)

● The dashboard is now unified and properly configured. Here's a summary of what was fixed:

  Summary of Changes

  Root Cause

  The pages/ManagerDashboard.jsx was using plain axios without authentication headers. The utils/api.js has the correct interceptor that adds the Bearer token.

  Solution: Unified pages/ManagerDashboard.jsx

  Key Changes:

1. Uses api from utils/api.js instead of plain axios - fixes the 401 errors
2. Two view modes:
   - Live Ops (default) - Shows data from LoanApplication table with lock status
   - Legacy - Shows data from original Application table

  Features included:

- Summary Cards: Total, Locked, Funded counts
- GATE 1: Manager Review - Initial approval panel (for Submitted/LEAD_CAPTURE status)
- GATE 2: Underwriting Decision - Waiter Pattern panel (when is_locked=true)
- Signature Waiting - Notice when waiting for borrower signature
- AI Verification Analysis - Shows income verification results
- Document Viewer - Tab-based PDF viewer for all uploaded documents
- Database Record Info - Shows DB ID, lock state, stage, UW decision

  Deleted:

- components/ManagerDashboard.jsx (was a duplicate, not used by App.jsx)

  Workflow Flow Now Supported:

1. Applicant submits → Status: "Submitted"
   ↓
2. Manager clicks "Approve" → Gate 1 triggered
   ↓
3. Processing runs → Status: "Pending Underwriting Decision", is_locked=true
   ↓
4. Manager clicks "Approve & Continue" → Gate 2 (Waiter Pattern) triggered
   ↓
5. Signature wait → Borrower signs disclosures
   ↓
6. Closing → Status: "Funded"
