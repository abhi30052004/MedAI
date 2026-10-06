import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowLeft, Check, Loader2, Search, ShieldCheck, UserRound, UsersRound } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import api from '../services/api';
import { CONDITION_OPTIONS, INSURANCE_PROVIDERS } from '../constants/medical';

type Patient = {
  id: number;
  first_name: string;
  last_name: string;
  dob?: string;
  identifiers?: { mrn?: string };
};

type AssignmentUser = { id: number; name: string; role: string };
type Mode = 'existing' | 'new';

const emptyForm = {
  firstName: '', lastName: '', dob: '', gender: '', phone: '', mrn: '',
  insuranceAvailable: 'no', insuranceProvider: '', insuranceNumber: '',
  title: '', condition: '', otherCondition: '', symptoms: '', history: '', notes: '',
  doctorId: '', reviewerId: '',
};
const today = new Date().toISOString().slice(0, 10);

function FieldError({ name, errors }: { name: string; errors: Record<string, string> }) {
  return errors[name] ? <p className="mt-1 text-xs text-red-600">{errors[name]}</p> : null;
}

function errorMessage(error: unknown) {
  if (!axios.isAxiosError(error)) return 'Unable to create the case. Please try again.';
  const status = error.response?.status;
  if (status === 401) return 'Session expired. Please log in again.';
  if (status === 403) return 'You do not have permission to create a case.';
  if (status === 409) return error.response?.data?.detail?.message || 'A similar patient already exists.';
  if (status === 422) return 'Please check the highlighted fields.';
  return error.response?.data?.detail || 'Unable to create the case. Please try again.';
}

export default function NewCase() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('new');
  const [form, setForm] = useState(emptyForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [query, setQuery] = useState('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [doctors, setDoctors] = useState<AssignmentUser[]>([]);
  const [reviewers, setReviewers] = useState<AssignmentUser[]>([]);
  const [loadingPeople, setLoadingPeople] = useState(true);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState('');
  const [duplicate, setDuplicate] = useState<Patient | null>(null);

  const insured = form.insuranceAvailable === 'yes';
  const set = (field: keyof typeof emptyForm, value: string) => {
    setForm(current => ({ ...current, [field]: value }));
    setErrors(current => ({ ...current, [field]: '' }));
    setServerError('');
  };

  useEffect(() => {
    Promise.all([
      api.get('/users/', { params: { role: 'doctor', is_active: true } }),
      api.get('/users/', { params: { role: 'insurance_reviewer', is_active: true } }),
    ]).then(([doctorResponse, reviewerResponse]) => {
      setDoctors(doctorResponse.data);
      setReviewers(reviewerResponse.data);
    }).catch(() => setServerError('Assignments could not be loaded. You can still create an unassigned case.'))
      .finally(() => setLoadingPeople(false));
  }, []);

  useEffect(() => {
    if (mode !== 'existing' || query.trim().length < 2) {
      return;
    }
    const timer = window.setTimeout(async () => {
      setSearching(true);
      try {
        const response = await api.get('/patients/', { params: { q: query.trim(), limit: 20 } });
        setPatients(response.data);
      } catch {
        setServerError('Unable to search patients right now.');
      } finally {
        setSearching(false);
      }
    }, 250);
    return () => window.clearTimeout(timer);
  }, [mode, query]);

  const condition = useMemo(
    () => form.condition === 'Other' ? form.otherCondition.trim() : form.condition,
    [form.condition, form.otherCondition],
  );

  const validate = () => {
    const next: Record<string, string> = {};
    if (mode === 'new') {
      if (!form.firstName.trim()) next.firstName = 'First name is required';
      if (!form.lastName.trim()) next.lastName = 'Last name is required';
      if (!form.dob) next.dob = 'Date of birth is required';
    } else if (!selectedPatient) next.patient = 'Select an existing patient';
    if (!form.title.trim()) next.title = 'Case title is required';
    if (insured && !form.insuranceProvider) next.insuranceProvider = 'Insurance provider is required';
    if (insured && !form.insuranceNumber.trim()) next.insuranceNumber = 'Policy number is required';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const useDuplicate = () => {
    if (!duplicate) return;
    setMode('existing');
    setSelectedPatient(duplicate);
    setQuery(`${duplicate.first_name} ${duplicate.last_name}`);
    setDuplicate(null);
    setServerError('');
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setServerError('');
    setDuplicate(null);
    const payload: Record<string, unknown> = {
      title: form.title.trim(),
      symptoms: form.symptoms.trim() ? { reason_for_visit: form.symptoms.trim() } : null,
      diagnoses: condition ? { primary_condition: condition } : null,
      previous_treatments: form.history.trim() ? { history: form.history.trim() } : null,
      additional_notes: form.notes.trim() || null,
      assigned_to: form.doctorId ? Number(form.doctorId) : null,
      insurance_available: insured,
    };
    if (mode === 'existing') payload.patient_id = selectedPatient?.id;
    else payload.patient = {
      first_name: form.firstName.trim(), last_name: form.lastName.trim(), dob: form.dob,
      gender: form.gender || null,
      contact: form.phone.trim() ? { phone: form.phone.trim() } : null,
      identifiers: form.mrn.trim() ? { mrn: form.mrn.trim() } : null,
    };
    if (insured) {
      payload.insurance_provider = form.insuranceProvider;
      payload.insurance_number = form.insuranceNumber.trim();
      payload.assigned_insurance_reviewer = form.reviewerId ? Number(form.reviewerId) : null;
    }
    try {
      const response = await api.post('/cases/', payload);
      navigate(`/cases/${response.data.id}`, { state: { created: true } });
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        const patientId = error.response?.data?.detail?.patient_id;
        if (patientId) setDuplicate({ id: patientId, first_name: form.firstName, last_name: form.lastName, dob: form.dob });
      }
      setServerError(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const fieldClass = (name: string) => `mt-1.5 w-full rounded-lg border bg-white px-3 py-2.5 text-sm outline-none transition focus:ring-2 focus:ring-blue-100 ${errors[name] ? 'border-red-400 focus:border-red-500' : 'border-slate-300 focus:border-blue-500'}`;

  return (
    <div className="mx-auto max-w-5xl pb-12">
      <Link to="/cases" className="mb-5 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900"><ArrowLeft className="h-4 w-4" /> Back to cases</Link>
      <div className="mb-7">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">New case</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">Create a new patient case</h1>
        <p className="mt-2 text-sm text-slate-500">Create the case first. Medical documents and AI analysis come next.</p>
      </div>

      <form onSubmit={submit} className="space-y-5" noValidate>
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center gap-3"><span className="rounded-lg bg-blue-50 p-2 text-blue-600"><UserRound className="h-5 w-5" /></span><div><h2 className="font-semibold text-slate-900">Patient</h2><p className="text-sm text-slate-500">Select a record or register a new patient.</p></div></div>
          <div className="mb-6 grid grid-cols-2 gap-3 rounded-xl bg-slate-100 p-1.5">
            {(['new', 'existing'] as Mode[]).map(value => <button key={value} type="button" onClick={() => { setMode(value); setSelectedPatient(null); setErrors({}); }} className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition ${mode === value ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}>{value === 'new' ? 'Create new patient' : 'Use existing patient'}</button>)}
          </div>
          {mode === 'existing' ? (
            <div>
              <label className="text-sm font-medium text-slate-700">Search by name or patient ID / MRN</label>
              <div className="relative mt-1.5"><Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" /><input value={query} onChange={e => { setQuery(e.target.value); setSelectedPatient(null); }} className={`${fieldClass('patient')} mt-0 pl-9`} placeholder="Start typing a patient name or MRN" />{searching && <Loader2 className="absolute right-3 top-3 h-4 w-4 animate-spin text-blue-600" />}</div>
              <FieldError name="patient" errors={errors} />
              {selectedPatient ? <div className="mt-3 flex items-center justify-between rounded-xl border border-green-200 bg-green-50 p-4"><div><p className="font-semibold text-green-900">{selectedPatient.first_name} {selectedPatient.last_name}</p><p className="text-sm text-green-700">DOB: {selectedPatient.dob || 'Not recorded'} · Patient #{selectedPatient.id}</p></div><Check className="h-5 w-5 text-green-600" /></div> : patients.length > 0 && <div className="mt-2 overflow-hidden rounded-xl border border-slate-200">{patients.map(patient => <button type="button" key={patient.id} onClick={() => setSelectedPatient(patient)} className="flex w-full items-center justify-between border-b border-slate-100 px-4 py-3 text-left last:border-0 hover:bg-slate-50"><span><span className="block text-sm font-semibold text-slate-900">{patient.first_name} {patient.last_name}</span><span className="text-xs text-slate-500">DOB {patient.dob || '—'} · #{patient.id}{patient.identifiers?.mrn ? ` · MRN ${patient.identifiers.mrn}` : ''}</span></span><span className="text-xs font-medium text-blue-600">Select</span></button>)}</div>}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="text-sm font-medium text-slate-700">First name *<input value={form.firstName} onChange={e => set('firstName', e.target.value)} className={fieldClass('firstName')} /><FieldError name="firstName" errors={errors} /></label>
              <label className="text-sm font-medium text-slate-700">Last name *<input value={form.lastName} onChange={e => set('lastName', e.target.value)} className={fieldClass('lastName')} /><FieldError name="lastName" errors={errors} /></label>
              <label className="text-sm font-medium text-slate-700">Date of birth *<input type="date" max={today} value={form.dob} onChange={e => set('dob', e.target.value)} className={fieldClass('dob')} /><FieldError name="dob" errors={errors} /></label>
              <label className="text-sm font-medium text-slate-700">Gender<select value={form.gender} onChange={e => set('gender', e.target.value)} className={fieldClass('gender')}><option value="">Select gender</option><option value="female">Female</option><option value="male">Male</option><option value="non_binary">Non-binary</option><option value="other">Other</option><option value="prefer_not_to_say">Prefer not to say</option></select></label>
              <label className="text-sm font-medium text-slate-700">Contact number<input type="tel" value={form.phone} onChange={e => set('phone', e.target.value)} className={fieldClass('phone')} /></label>
              <label className="text-sm font-medium text-slate-700">Patient ID / MRN<input value={form.mrn} onChange={e => set('mrn', e.target.value)} className={fieldClass('mrn')} /></label>
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center gap-3"><span className="rounded-lg bg-emerald-50 p-2 text-emerald-600"><ShieldCheck className="h-5 w-5" /></span><div><h2 className="font-semibold text-slate-900">Insurance information</h2><p className="text-sm text-slate-500">Is insurance available for this case?</p></div></div>
          <div className="flex gap-3">{['yes', 'no'].map(value => <label key={value} className={`flex cursor-pointer items-center gap-2 rounded-lg border px-5 py-2.5 text-sm font-medium ${form.insuranceAvailable === value ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-300 text-slate-700'}`}><input type="radio" name="insurance" value={value} checked={form.insuranceAvailable === value} onChange={() => { set('insuranceAvailable', value); if (value === 'no') setForm(current => ({ ...current, insuranceAvailable: 'no', insuranceProvider: '', insuranceNumber: '', reviewerId: '' })); }} />{value === 'yes' ? 'Yes' : 'No'}</label>)}</div>
          {insured ? <div className="mt-5 grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-slate-700">Insurance provider *<select value={form.insuranceProvider} onChange={e => set('insuranceProvider', e.target.value)} className={fieldClass('insuranceProvider')}><option value="">Select provider</option>{INSURANCE_PROVIDERS.map(provider => <option key={provider}>{provider}</option>)}</select><FieldError name="insuranceProvider" errors={errors} /></label><label className="text-sm font-medium text-slate-700">Policy number *<input value={form.insuranceNumber} onChange={e => set('insuranceNumber', e.target.value)} className={fieldClass('insuranceNumber')} /><FieldError name="insuranceNumber" errors={errors} /></label></div> : <p className="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-500">No insurance information required.</p>}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-slate-900">Case information</h2><p className="mb-5 text-sm text-slate-500">Provide the reason for this case. A diagnosis is not required.</p>
          <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-slate-700">Case title *<input value={form.title} onChange={e => set('title', e.target.value)} className={fieldClass('title')} placeholder="e.g. Hypertension follow-up" /><FieldError name="title" errors={errors} /></label><label className="text-sm font-medium text-slate-700">Primary disease / condition<select value={form.condition} onChange={e => set('condition', e.target.value)} className={fieldClass('condition')}><option value="">Not yet established</option>{CONDITION_OPTIONS.map(item => <option key={item}>{item}</option>)}</select></label></div>
          {form.condition === 'Other' && <label className="mt-4 block text-sm font-medium text-slate-700">Specify condition<input value={form.otherCondition} onChange={e => set('otherCondition', e.target.value)} className={fieldClass('otherCondition')} /></label>}
          <div className="mt-4 grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-slate-700">Symptoms / reason for visit<textarea rows={4} value={form.symptoms} onChange={e => set('symptoms', e.target.value)} className={fieldClass('symptoms')} placeholder="Describe reported symptoms and reason for visit" /></label><label className="text-sm font-medium text-slate-700">Previous treatment / medical history<textarea rows={4} value={form.history} onChange={e => set('history', e.target.value)} className={fieldClass('history')} placeholder="Optional patient-reported history" /></label></div>
          <label className="mt-4 block text-sm font-medium text-slate-700">Additional notes<textarea rows={3} value={form.notes} onChange={e => set('notes', e.target.value)} className={fieldClass('notes')} placeholder="Operational or context notes" /></label>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center gap-3"><span className="rounded-lg bg-violet-50 p-2 text-violet-600"><UsersRound className="h-5 w-5" /></span><div><h2 className="font-semibold text-slate-900">Assignment</h2><p className="text-sm text-slate-500">Only active users in your organization are shown.</p></div></div>
          {loadingPeople ? <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading assignment options…</div> : <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium text-slate-700">Doctor / practitioner<select value={form.doctorId} onChange={e => set('doctorId', e.target.value)} className={fieldClass('doctorId')}><option value="">Unassigned</option>{doctors.map(doctor => <option key={doctor.id} value={doctor.id}>Dr. {doctor.name}</option>)}</select></label>{insured && <label className="text-sm font-medium text-slate-700">Insurance reviewer<select value={form.reviewerId} onChange={e => set('reviewerId', e.target.value)} className={fieldClass('reviewerId')}><option value="">Unassigned</option>{reviewers.map(reviewer => <option key={reviewer.id} value={reviewer.id}>{reviewer.name}</option>)}</select></label>}</div>}
        </section>

        {serverError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"><p>{serverError}</p>{duplicate && <button type="button" onClick={useDuplicate} className="mt-3 rounded-lg bg-red-700 px-4 py-2 font-semibold text-white hover:bg-red-800">Use existing patient</button>}</div>}
        <div className="flex items-center justify-end gap-3"><Link to="/cases" className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">Cancel</Link><button disabled={submitting} className="inline-flex min-w-36 items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{submitting && <Loader2 className="h-4 w-4 animate-spin" />}{submitting ? 'Creating case…' : 'Create case'}</button></div>
      </form>
    </div>
  );
}
