import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, FormRow } from "../../components/common/index.jsx";
import { inpatientApi } from "../../services/api";

export default function NurseVitals() {
  const [admissions, setAdmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ temperature: "", blood_pressure_systolic: "", blood_pressure_diastolic: "", pulse_rate: "", respiratory_rate: "", oxygen_saturation: "", weight: "", pain_score: "", notes: "" });
  const [saving, setSaving] = useState(false);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchAdmissions(); }, []);

  async function fetchAdmissions() {
    setLoading(true);
    try {
      const res = await inpatientApi.list({ status: "ACTIVE" });
      setAdmissions(res.data.results || res.data);
    } catch { showToast("Failed to load admissions", "error"); }
    finally { setLoading(false); }
  }

  async function recordVitals() {
    setSaving(true);
    try {
      await inpatientApi.recordVitals(selected.id, form);
      showToast("Vitals recorded successfully", "success");
      setShowModal(false);
      setSelected(null);
      setForm({ temperature: "", blood_pressure_systolic: "", blood_pressure_diastolic: "", pulse_rate: "", respiratory_rate: "", oxygen_saturation: "", weight: "", pain_score: "", notes: "" });
    } catch {
      showToast("Failed to record vitals", "error");
    } finally { setSaving(false); }
  }

  const columns = [
    { key: "admission_number", label: "Admission #", render: a => <code className="text-primary">{a.admission_number}</code> },
    { key: "patient", label: "Patient", render: a => <div><div className="fw-medium">{a.patient?.first_name} {a.patient?.last_name}</div><small className="text-muted">{a.bed?.ward?.ward_name} — Bed {a.bed?.bed_number}</small></div> },
    { key: "days", label: "LOS", render: a => `${a.length_of_stay || 0} day(s)` },
    { key: "critical", label: "Status", render: a => a.is_critical ? <span className="badge bg-danger">Critical</span> : <span className="badge bg-success">Stable</span> },
    { key: "actions", label: "", render: a => (
      <button className="btn btn-sm btn-mc-primary" onClick={() => { setSelected(a); setShowModal(true); }}>
        <i className="bi bi-activity me-1" />Record Vitals
      </button>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Record Patient Vitals" subtitle="Monitor inpatient vital signs" />

      {loading ? <LoadingSpinner /> : admissions.length === 0 ? (
        <EmptyState icon="bi-hospital" title="No active admissions" subtitle="No inpatients require vitals recording" />
      ) : (
        <DataTable columns={columns} data={admissions} />
      )}

      <Modal
        show={showModal}
        onClose={() => setShowModal(false)}
        title={`Record Vitals — ${selected?.patient?.first_name} ${selected?.patient?.last_name}`}
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={recordVitals} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : null}Save Vitals
            </button>
          </>
        }
      >
        <div className="row g-3">
          {[
            { label: "Temperature (°C)", field: "temperature", placeholder: "36.5" },
            { label: "Pulse Rate (bpm)", field: "pulse_rate", placeholder: "72" },
            { label: "BP Systolic (mmHg)", field: "blood_pressure_systolic", placeholder: "120" },
            { label: "BP Diastolic (mmHg)", field: "blood_pressure_diastolic", placeholder: "80" },
            { label: "SpO2 (%)", field: "oxygen_saturation", placeholder: "98" },
            { label: "Respiratory Rate", field: "respiratory_rate", placeholder: "16" },
            { label: "Weight (kg)", field: "weight", placeholder: "70" },
            { label: "Pain Score (0-10)", field: "pain_score", placeholder: "0" },
          ].map(({ label, field, placeholder }) => (
            <div key={field} className="col-6">
              <label className="mc-label">{label}</label>
              <input type="number" className="mc-input" placeholder={placeholder} value={form[field]} onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))} />
            </div>
          ))}
          <FormRow label="Notes" colClass="col-12">
            <textarea className="mc-input" rows={2} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Clinical notes..." />
          </FormRow>
        </div>
      </Modal>
    </Layout>
  );
}