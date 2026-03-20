import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import {
  PageHeader, LoadingSpinner, EmptyState, Modal, useToast,
  ToastContainer, DataTable, FormRow, VitalBox, TriageBadge
} from "../../components/common/index.jsx";
import { visitApi, triageApi } from "../../services/api";

const TRIAGE_CATEGORIES = [
  { id: 1, label: "Red — Immediate (Emergency)", color: "RED", bg: "#dc2626" },
  { id: 2, label: "Orange — Very Urgent (10 min)", color: "ORANGE", bg: "#f97316" },
  { id: 3, label: "Yellow — Urgent (30 min)", color: "YELLOW", bg: "#eab308" },
  { id: 4, label: "Green — Standard (60 min)", color: "GREEN", bg: "#16a34a" },
  { id: 5, label: "Blue — Non-Urgent (120 min)", color: "BLUE", bg: "#2563eb" },
];

const EMPTY_TRIAGE = {
  category: "", temperature: "", blood_pressure_systolic: "",
  blood_pressure_diastolic: "", pulse_rate: "", respiratory_rate: "",
  oxygen_saturation: "", weight: "", height: "",
  consciousness_level: "ALERT", breathing_status: "NORMAL",
  pain_score: "0", presenting_symptoms: "", allergies_noted: "",
  current_medications: "", triage_notes: "", requires_immediate_attention: false,
};

export default function NurseTriage() {
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_TRIAGE);
  const [saving, setSaving] = useState(false);
  const [triageCategories, setTriageCategories] = useState([]);
  const { toasts, showToast, removeToast } = useToast();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchVisits();
    fetchCategories();
    const vid = searchParams.get("visit");
    if (vid) openTriageForVisit(vid);
  }, []);

  async function fetchVisits() {
    setLoading(true);
    try {
      const res = await visitApi.list({ status: "REGISTERED", ordering: "-arrival_time" });
      setVisits(res.data.results || res.data);
    } catch { showToast("Failed to load visits", "error"); }
    finally { setLoading(false); }
  }

  async function fetchCategories() {
    try {
      const res = await triageApi.categories();
      setTriageCategories(res.data.results || res.data);
    } catch {}
  }

  async function openTriageForVisit(visitId) {
    try {
      const res = await visitApi.get(visitId);
      setSelectedVisit(res.data);
      setShowModal(true);
    } catch {}
  }

  async function submitTriage() {
    if (!form.category || !form.presenting_symptoms || !form.triage_notes) {
      showToast("Triage category, symptoms, and notes are required", "error"); return;
    }
    setSaving(true);
    try {
      await triageApi.create({ ...form, visit: selectedVisit.id });
      await visitApi.updateStatus(selectedVisit.id, { status: "TRIAGED" });
      showToast("Triage completed successfully", "success");
      setShowModal(false);
      setForm(EMPTY_TRIAGE);
      setSelectedVisit(null);
      fetchVisits();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to submit triage", "error");
    } finally { setSaving(false); }
  }

  const f = form;
  const setF = (field, val) => setForm(prev => ({ ...prev, [field]: val }));

  const columns = [
    { key: "visit_number", label: "Visit #", render: v => <code className="text-primary">{v.visit_number}</code> },
    { key: "patient", label: "Patient", render: v => (
      <div><div className="fw-medium">{v.patient_name || "Patient"}</div>
        <small className="text-muted">{v.visit_type?.replace("_", " ")}</small></div>
    )},
    { key: "complaint", label: "Chief Complaint", render: v => <small className="text-muted">{v.chief_complaint?.substring(0, 60)}</small> },
    { key: "arrival", label: "Waiting", render: v => {
      const mins = Math.round((Date.now() - new Date(v.arrival_time)) / 60000);
      return <span className={`badge ${mins > 30 ? "bg-danger" : mins > 15 ? "bg-warning text-dark" : "bg-success"}`}>{mins} min</span>;
    }},
    { key: "actions", label: "", render: v => (
      <button className="btn btn-sm btn-mc-primary" onClick={() => { setSelectedVisit(v); setShowModal(true); }}>
        <i className="bi bi-heart-pulse me-1" />Triage
      </button>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Triage Assessment" subtitle="Assess patients waiting for triage" />

      {loading ? <LoadingSpinner /> : visits.length === 0 ? (
        <EmptyState icon="bi-check2-all" title="No patients waiting for triage" subtitle="All registered patients have been triaged" />
      ) : (
        <DataTable columns={columns} data={visits} />
      )}

      {/* Triage Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setForm(EMPTY_TRIAGE); setSelectedVisit(null); }}
        title={`Triage Assessment — ${selectedVisit?.visit_number || ""}`}
        size="xl"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={submitTriage} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check2 me-2" />}
              Complete Triage
            </button>
          </>
        }
      >
        {selectedVisit && (
          <div>
            {/* Patient Info */}
            <div className="mc-alert info mb-4">
              <div className="d-flex gap-3">
                <div><strong>Patient:</strong> {selectedVisit.patient_name}</div>
                <div><strong>Visit:</strong> {selectedVisit.visit_number}</div>
                <div><strong>Complaint:</strong> {selectedVisit.chief_complaint}</div>
              </div>
            </div>

            {/* Triage Category */}
            <div className="mb-4">
              <label className="mc-label mb-2">Triage Category *</label>
              <div className="d-flex flex-wrap gap-2">
                {TRIAGE_CATEGORIES.map(tc => (
                  <button
                    key={tc.id}
                    type="button"
                    className={`btn ${f.category == tc.id ? "text-white" : "btn-outline-secondary"}`}
                    style={f.category == tc.id ? { background: tc.bg, borderColor: tc.bg } : {}}
                    onClick={() => setF("category", tc.id)}
                  >
                    <span className="rounded-circle me-2" style={{ width: 10, height: 10, background: tc.bg, display: "inline-block" }} />
                    {tc.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="row g-3">
              {/* Vital Signs */}
              <div className="col-12">
                <h6 className="fw-semibold mb-3 text-muted">Vital Signs</h6>
                <div className="row g-3">
                  {[
                    { label: "Temperature (°C)", field: "temperature", placeholder: "36.5", unit: "°C" },
                    { label: "Pulse Rate (bpm)", field: "pulse_rate", placeholder: "72" },
                    { label: "BP Systolic (mmHg)", field: "blood_pressure_systolic", placeholder: "120" },
                    { label: "BP Diastolic (mmHg)", field: "blood_pressure_diastolic", placeholder: "80" },
                    { label: "SpO2 (%)", field: "oxygen_saturation", placeholder: "98" },
                    { label: "Respiratory Rate", field: "respiratory_rate", placeholder: "16" },
                    { label: "Weight (kg)", field: "weight", placeholder: "70" },
                    { label: "Height (cm)", field: "height", placeholder: "170" },
                  ].map(({ label, field, placeholder }) => (
                    <div key={field} className="col-6 col-md-3">
                      <label className="mc-label">{label}</label>
                      <input type="number" className="mc-input" placeholder={placeholder} value={f[field]} onChange={e => setF(field, e.target.value)} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Clinical Assessment */}
              <FormRow label="Consciousness Level" colClass="col-md-4">
                <select className="mc-select" value={f.consciousness_level} onChange={e => setF("consciousness_level", e.target.value)}>
                  <option value="ALERT">Alert and Responsive</option>
                  <option value="VERBAL">Responds to Verbal</option>
                  <option value="PAIN">Responds to Pain</option>
                  <option value="UNRESPONSIVE">Unresponsive</option>
                </select>
              </FormRow>

              <FormRow label="Breathing Status" colClass="col-md-4">
                <select className="mc-select" value={f.breathing_status} onChange={e => setF("breathing_status", e.target.value)}>
                  <option value="NORMAL">Normal</option>
                  <option value="LABORED">Labored</option>
                  <option value="SHALLOW">Shallow</option>
                  <option value="ABSENT">Absent</option>
                </select>
              </FormRow>

              <FormRow label="Pain Score (0-10)" colClass="col-md-4">
                <div className="d-flex align-items-center gap-2">
                  <input type="range" min={0} max={10} value={f.pain_score} onChange={e => setF("pain_score", e.target.value)} className="flex-grow-1" />
                  <span className="fw-bold text-primary" style={{ minWidth: 24 }}>{f.pain_score}</span>
                </div>
              </FormRow>

              <FormRow label="Presenting Symptoms *" colClass="col-12">
                <textarea className="mc-input" rows={3} placeholder="Describe presenting symptoms in detail..." value={f.presenting_symptoms} onChange={e => setF("presenting_symptoms", e.target.value)} />
              </FormRow>

              <FormRow label="Known Allergies" colClass="col-md-6">
                <textarea className="mc-input" rows={2} placeholder="Known allergies..." value={f.allergies_noted} onChange={e => setF("allergies_noted", e.target.value)} />
              </FormRow>

              <FormRow label="Current Medications" colClass="col-md-6">
                <textarea className="mc-input" rows={2} placeholder="Current medications..." value={f.current_medications} onChange={e => setF("current_medications", e.target.value)} />
              </FormRow>

              <FormRow label="Triage Notes *" colClass="col-12">
                <textarea className="mc-input" rows={3} placeholder="Clinical notes and observations..." value={f.triage_notes} onChange={e => setF("triage_notes", e.target.value)} />
              </FormRow>

              <div className="col-12">
                <div className="form-check">
                  <input type="checkbox" className="form-check-input" id="immediate" checked={f.requires_immediate_attention} onChange={e => setF("requires_immediate_attention", e.target.checked)} />
                  <label className="form-check-label fw-medium text-danger" htmlFor="immediate">
                    <i className="bi bi-exclamation-triangle me-2" />Requires Immediate Attention
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}