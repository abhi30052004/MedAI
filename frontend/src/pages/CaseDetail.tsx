import { useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { FileText, Loader2, User, BrainCircuit, MessageSquare, Check, X, Edit2, Upload, CircleCheck } from 'lucide-react';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

export default function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);

  const [caseData, setCaseData] = useState<any>(null);
  const [patient, setPatient] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [extractedItems, setExtractedItems] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [newNote, setNewNote] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [uploading, setUploading] = useState(false);

  // UI States
  const [editingItem, setEditingItem] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');

  const loadCaseData = async () => {
    try {
      setLoading(true);
      const [caseRes, docsRes, notesRes] = await Promise.all([
        api.get(`/cases/${id}`),
        api.get(`/cases/${id}/documents`),
        api.get(`/cases/${id}/notes`)
      ]);
      setCaseData(caseRes.data);
      setDocuments(docsRes.data);
      setNotes(notesRes.data);
      const patientRes = await api.get(`/patients/${caseRes.data.patient_id}`);
      setPatient(patientRes.data);

      if (caseRes.data.status === 'UNDER_REVIEW' || caseRes.data.status === 'COMPLETED') {
        try {
          const [analysisRes, itemsRes] = await Promise.all([
            api.get(`/cases/${id}/analysis`),
            api.get(`/cases/${id}/extracted-items`)
          ]);
          setAnalysis(analysisRes.data.latest_summary);
          setExtractedItems(itemsRes.data);
        } catch (e) {
          console.error("No analysis yet or error fetching", e);
        }
      }
    } catch (error) {
      console.error('Failed to load case data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) loadCaseData();
  }, [id]);

  const handleAnalyze = async () => {
    try {
      await api.post(`/cases/${id}/analyze`);
      alert("Analysis started in background. Refresh in a moment.");
      loadCaseData();
    } catch (e) {
      alert("Failed to start analysis");
    }
  };

  const handleReviewItem = async (itemId: number, action: string, newValue?: string) => {
    try {
      await api.patch(`/extracted-items/${itemId}`, { action, value: newValue });
      setEditingItem(null);
      loadCaseData();
    } catch (e) {
      alert("Failed to update item");
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    try {
      await api.post(`/cases/${id}/notes`, { text: newNote });
      setNewNote('');
      loadCaseData();
    } catch (e) {
      alert("Failed to add note");
    }
  };

  const handleReview = async (decision: 'APPROVED' | 'REJECTED') => {
    try {
      const reason = decision === 'REJECTED' ? window.prompt('Please provide a reason for rejection:') : undefined;
      if (decision === 'REJECTED' && !reason?.trim()) return;
      await api.post(`/cases/${id}/review`, { decision, reason });
      loadCaseData();
    } catch (e) {
      alert("Failed to save review decision");
    }
  };

  if (loading) {
    return <div className="flex h-[60vh] justify-center items-center"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  }

  if (!caseData) return <div>Case not found</div>;

  const maskedPolicy = caseData.insurance_number
    ? `••••${caseData.insurance_number.slice(-4)}`
    : null;

  return (
    <div className="space-y-6 pb-12">
      {location.state?.created && (
        <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
          <CircleCheck className="mt-0.5 h-5 w-5 flex-none text-emerald-600" />
          <div><p className="font-semibold">Case created successfully.</p><p className="text-sm text-emerald-700">Upload medical documents to start AI processing.</p></div>
        </div>
      )}
      {/* HEADER */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">CASE-{caseData.id}: {caseData.title}</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold
                ${caseData.status === 'NEW' ? 'bg-gray-100 text-gray-800' :
                  caseData.status === 'DOCUMENTS_UPLOADED' ? 'bg-blue-100 text-blue-800' :
                    caseData.status === 'UNDER_ANALYSIS' ? 'bg-yellow-100 text-yellow-800' :
                      caseData.status === 'UNDER_REVIEW' ? 'bg-purple-100 text-purple-800' :
                        'bg-green-100 text-green-800'}`}>
                {caseData.status.replace('_', ' ')}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-2 flex items-center gap-4">
              <span className="flex items-center gap-1"><User className="w-4 h-4" /> {patient ? `${patient.first_name} ${patient.last_name}` : `Patient ${caseData.patient_id}`}</span>
              <span>Assigned: {caseData.assigned_to || 'Unassigned'}</span>
            </p>
          </div>
          <div className="flex gap-2">
            {user?.role === 'doctor' && caseData.status === 'DOCUMENTS_UPLOADED' && (
              <button onClick={handleAnalyze} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                <BrainCircuit className="w-4 h-4" /> Run AI Analysis
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT / MAIN AREA */}
        <div className="lg:col-span-2 space-y-6">

          {/* AI SUMMARY */}
          {analysis && analysis.summary_json && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-purple-100">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-purple-600" />
                AI Case Summary
              </h2>
              <div className="bg-purple-50 text-purple-800 text-xs px-3 py-1 rounded-md mb-4 inline-block font-medium">
                AI Generated — Requires Human Review
              </div>
              <div className="space-y-4 text-sm text-gray-700">
                <div><h3 className="mb-1 font-semibold text-gray-900">Overall case summary</h3><p>{analysis.summary_json.patient_summary || 'No summary was generated.'}</p></div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {[
                    ['Clinical findings', 'clinical_findings'],
                    ['Diagnoses / conditions', 'diagnoses'],
                    ['Procedures', 'procedures'],
                    ['Medications', 'medications'],
                    ['Symptoms', 'symptoms'],
                    ['Important observations', 'important_observations'],
                  ].map(([label, key]) => analysis.summary_json[key]?.length > 0 && (
                    <div key={key} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                      <h3 className="mb-2 font-semibold text-gray-900">{label}</h3>
                      <ul className="list-disc space-y-1 pl-4">{analysis.summary_json[key].map((value: string, index: number) => <li key={index}>{value}</li>)}</ul>
                    </div>
                  ))}
                </div>
                {analysis.summary_json.missing_information?.length > 0 && (
                  <div className="mt-4 p-4 bg-orange-50 rounded-lg border border-orange-100">
                    <h3 className="font-semibold text-orange-800 mb-2">Missing/Important Information</h3>
                    <ul className="list-disc pl-5 space-y-1 text-orange-900">
                      {analysis.summary_json.missing_information.map((info: string, i: number) => <li key={i}>{info}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* EXTRACTED ITEMS */}
          {extractedItems.length > 0 && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Extracted Medical Items</h2>
              <div className="space-y-4">
                {extractedItems.map(item => (
                  <div key={item.id} className={`p-4 rounded-lg border ${item.review_status === 'CONFIRMED' ? 'border-green-200 bg-green-50' : item.review_status === 'REJECTED' ? 'border-red-200 bg-red-50' : item.review_status === 'EDITED' ? 'border-blue-200 bg-blue-50' : 'border-gray-200'}`}>
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{item.category}</span>

                        {editingItem === item.id ? (
                          <div className="mt-2 flex gap-2">
                            <input type="text" value={editValue} onChange={e => setEditValue(e.target.value)} className="border rounded px-2 py-1 text-sm" />
                            <button onClick={() => handleReviewItem(item.id, 'edit', editValue)} className="text-xs bg-blue-600 text-white px-3 py-1 rounded">Save</button>
                            <button onClick={() => setEditingItem(null)} className="text-xs bg-gray-200 px-3 py-1 rounded">Cancel</button>
                          </div>
                        ) : (
                          <h4 className="font-medium text-gray-900 mt-1">{item.value}</h4>
                        )}

                        {item.original_value && item.original_value !== item.value && (
                          <p className="text-xs text-gray-500 mt-1 line-through">AI: {item.original_value}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-2">
                          Source: Doc {item.document_id} | Page {item.source_page || '—'} | Confidence: {item.confidence == null ? '—' : `${(item.confidence * 100).toFixed(0)}%`}
                        </p>
                        {item.source_snippet && <p className="text-xs italic text-gray-600 mt-1 bg-white p-2 rounded border border-gray-100">“{item.source_snippet}”</p>}
                      </div>

                      <div className="text-right flex flex-col items-end gap-2">
                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${item.review_status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}`}>
                          {item.review_status}
                        </span>

                        {item.review_status === 'PENDING' && (user?.role === 'doctor' || user?.role === 'insurance_reviewer') && (
                          <div className="flex items-center gap-1 mt-2">
                            <button onClick={() => handleReviewItem(item.id, 'confirm')} className="p-1.5 bg-green-100 text-green-700 rounded hover:bg-green-200" title="Confirm"><Check className="w-4 h-4" /></button>
                            <button onClick={() => { setEditingItem(item.id); setEditValue(item.value); }} className="p-1.5 bg-blue-100 text-blue-700 rounded hover:bg-blue-200" title="Edit"><Edit2 className="w-4 h-4" /></button>
                            <button onClick={() => handleReviewItem(item.id, 'reject')} className="p-1.5 bg-red-100 text-red-700 rounded hover:bg-red-200" title="Reject"><X className="w-4 h-4" /></button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* NOTES */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2"><MessageSquare className="w-5 h-5" /> Case Notes</h2>
            <div className="space-y-4 mb-6">
              {notes.length === 0 ? <p className="text-sm text-gray-500">No notes yet.</p> : notes.map(note => (
                <div key={note.id} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-semibold text-gray-900">User {note.author_id}</span>
                    <span className="text-xs text-gray-500">{new Date(note.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-gray-700">{note.text}</p>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-2">
              <textarea
                value={newNote}
                onChange={e => setNewNote(e.target.value)}
                placeholder="Add a clinical or review note..."
                className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                rows={3}
              />
              <button onClick={handleAddNote} className="self-end px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors">
                Add Note
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT AREA */}
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-bold text-gray-900">Case overview</h2>
            <dl className="space-y-4 text-sm">
              <div><dt className="text-xs font-semibold uppercase tracking-wide text-gray-400">Patient</dt><dd className="mt-1 font-medium text-gray-900">{patient ? `${patient.first_name} ${patient.last_name}` : '—'}</dd><dd className="text-gray-500">DOB {patient?.dob || '—'}</dd></div>
              <div><dt className="text-xs font-semibold uppercase tracking-wide text-gray-400">Case</dt><dd className="mt-1 font-medium text-gray-900">{caseData.title}</dd></div>
              <div><dt className="text-xs font-semibold uppercase tracking-wide text-gray-400">Insurance</dt><dd className="mt-1 font-medium text-gray-900">{caseData.insurance_available ? caseData.insurance_provider : 'Not available'}</dd>{maskedPolicy && <dd className="text-gray-500">Policy {maskedPolicy}</dd>}</div>
              <div><dt className="text-xs font-semibold uppercase tracking-wide text-gray-400">Status</dt><dd className="mt-1 font-semibold text-blue-700">{caseData.status.replaceAll('_', ' ')}</dd></div>
            </dl>
          </div>

          {/* SOURCE DOCUMENTS */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex justify-between items-center">
              Documents
              <label className={`text-xs bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg flex items-center gap-1 hover:bg-blue-100 ${uploading ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}>
                {uploading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Upload className="w-3 h-3" />} {uploading ? 'Uploading' : 'Upload'}
                <input type="file" accept=".pdf,.jpg,.jpeg,.png,.tiff,.docx" disabled={uploading} className="hidden" onChange={async (e) => {
                  if (!e.target.files || !e.target.files[0]) return;
                  const file = e.target.files[0];
                  setUploadError('');
                  if (file.size > 25 * 1024 * 1024) {
                    setUploadError('File exceeds the 25 MB limit.');
                    e.target.value = '';
                    return;
                  }
                  const formData = new FormData();
                  formData.append('file', file);
                  try {
                    setUploading(true);
                    await api.post(`/cases/${id}/documents`, formData, {
                      headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    loadCaseData();
                  } catch (err: any) {
                    setUploadError(err.response?.data?.detail || 'Upload failed. Please try again.');
                  } finally {
                    setUploading(false);
                    e.target.value = '';
                  }
                }} />
              </label>
            </h2>
            {uploadError && <p className="mb-3 rounded-lg bg-red-50 p-2 text-xs text-red-700">{uploadError}</p>}
            <div className="space-y-3">
              {documents.length === 0 ? <div className="rounded-lg border border-dashed border-gray-300 p-4 text-center"><p className="text-sm font-medium text-gray-700">No documents uploaded</p><p className="mt-1 text-xs text-gray-500">PDF, JPG, PNG, TIFF or DOCX · up to 25 MB</p></div> : documents.map(doc => (
                <div key={doc.id} className="p-3 border border-gray-100 rounded-lg flex justify-between items-center bg-gray-50 hover:bg-gray-100 cursor-pointer">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    <div className="truncate">
                      <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                      <p className="text-xs text-gray-500">Status: {doc.status}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* APPROVALS */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Case Approvals</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 border border-gray-100 rounded-lg bg-gray-50">
                <div>
                  <p className="text-sm font-medium text-gray-900">Doctor Review</p>
                  <p className={`text-xs font-semibold mt-1 ${caseData.doctor_review_status === 'APPROVED' ? 'text-green-600' : 'text-yellow-600'}`}>
                    {caseData.doctor_review_status}
                  </p>
                </div>
                {caseData.doctor_review_status === 'PENDING' && user?.role === 'doctor' && caseData.status === 'UNDER_REVIEW' && (
                  <div className="flex gap-1"><button onClick={() => handleReview('REJECTED')} className="px-2 py-1.5 bg-red-50 text-red-700 text-xs font-medium rounded hover:bg-red-100">Reject</button><button onClick={() => handleReview('APPROVED')} className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700">Approve</button></div>
                )}
              </div>

              <div className="flex items-center justify-between p-3 border border-gray-100 rounded-lg bg-gray-50">
                <div>
                  <p className="text-sm font-medium text-gray-900">Insurance Review</p>
                  <p className={`text-xs font-semibold mt-1 ${caseData.insurance_review_status === 'APPROVED' ? 'text-green-600' : 'text-yellow-600'}`}>
                    {caseData.insurance_review_status}
                  </p>
                </div>
                {caseData.insurance_review_status === 'PENDING' && user?.role === 'insurance_reviewer' && caseData.status === 'UNDER_REVIEW' && (
                  <div className="flex gap-1"><button onClick={() => handleReview('REJECTED')} className="px-2 py-1.5 bg-red-50 text-red-700 text-xs font-medium rounded hover:bg-red-100">Reject</button><button onClick={() => handleReview('APPROVED')} className="px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700">Approve</button></div>
                )}
              </div>
              <p className="text-xs leading-relaxed text-gray-500">The case completes automatically after every required review is approved.</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
