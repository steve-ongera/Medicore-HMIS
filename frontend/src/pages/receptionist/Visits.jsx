import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import {
  PageHeader, LoadingSpinner, EmptyState, Modal, Badge, useToast,
  ToastContainer, SearchInput, DataTable, FormRow, Tabs
} from "../../components/common/index.jsx";
import { visitApi, patientApi, miscApi } from "../../services/api";

const VISIT_TYPES = [
  { value: "OUTPATIENT", label: "Outpatient (OPD)" },
  { value: "EMERGENCY", label: "Emergency/Casualty" },
  { value: "FOLLOW_UP", label: "Follow-up" },
  { value: "ANTENATAL", label: "Antenatal Care" },
  { value: "IMMUNIZATION", label: "Immunization" },
  { value: "GENERAL", label: "General Consultation" },
  { value: "REFERRAL", label: "Referral" },
];

const STATUS_COLORS = {
  REGISTERED: "secondary", TRIAGED: "warning", WAITING: "info",
  IN_CONSULTATION: "primary", COMPLETED: "success", CANCELLED: "danger",
  ADMITTED: "dark", REFERRED: "purple",
};

const EMPTY_VISIT = {
  patient: "", visit_type: "OUTPATIENT", chief_complaint: "",
  insurance_provider: "", specialized_service: "", notes: "",
};

export default function ReceptionVisits() {
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_VISIT);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("active");
  const [patients, setPatients] = useState([]);
  const [patientSearch, setPatientSearch] = useState("");
  const [providers, setProviders] = useState([]);
  const [services, setServices] = useState([]);
  const { toasts, showToast, removeToast } = useToast();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchVisits();
    fetchMeta();
    // Pre-fill patient if coming from patient page
    const pid = searchParams.get("patient");
    if (pid) { setForm(f => ({ ...f, patient: pid })); setShowModal(true); }
  }, [activeTab]);

  async function fetchVisits() {
    setLoading(true);
    try {
      const statusFilter = activeTab === "active"
        ? "REGISTERED,TRIAGED,WAITING,IN_CONSULTATION"
        : activeTab === "completed" ? "COMPLETED" : "";
      const res = await visitApi.list({ status: statusFilter, search, ordering: "-arrival_time" });
      setVisits(res.data.results || res.data);
    } catch {
      showToast("Failed to load visits", "error");
    } finally { setLoading(false); }
  }

  async function fetchMeta() {
    try {
      const [provRes, svcRes] = await Promise.all([
        miscApi.insuranceProviders(),
        miscApi.specializedServices(),
      ]);
      setProviders(provRes.data.results || provRes.data);
      setServices(svcRes.data.results || svcRes.data);
    } catch {}
  }

  async function searchPatients(q) {
    if (!q || q.length < 2) { setPatients([]); return; }
    try {
      const res = await patientApi.list({ search: q });
      setPatients(res.data.results || res.data);
    } catch {}
  }

  async function handleRegisterVisit() {
    if (!form.patient || !form.visit_type || !form.chief_complaint) {
      showToast("Patient, visit type, and chief complaint are required", "error"); return;
    }
    setSaving(true);
    try {
      await visitApi.create(form);
      showToast("Visit registered successfully", "success");
      setShowModal(false);
      setForm(EMPTY_VISIT);
      fetchVisits();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to register visit", "error");
    } finally { setSaving(false); }
  }

  async function updateStatus(visitId, status) {
    try {
      await visitApi.updateStatus(visitId, { status });
      showToast("Status updated", "success");
      fetchVisits();
    } catch {
      showToast("Failed to update status", "error");
    }
  }

  const columns = [
    { key: "visit_number", label: "Visit #", render: v => <code className="text-primary">{v.visit_number}</code> },
    { key: "patient", label: "Patient", render: v => (
      <div>
        <div className="fw-medium">{v.patient_name || `${v.patient?.first_name || ""} ${v.patient?.last_name || ""}`}</div>
        <small className="text-muted">{v.visit_type}</small>
      </div>
    )},
    { key: "arrival_time", label: "Arrival", render: v => (
      <small>{new Date(v.arrival_time).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" })}</small>
    )},
    { key: "status", label: "Status", render: v => (
      <span className={`badge bg-${STATUS_COLORS[v.status] || "secondary"}`}>{v.status?.replace("_", " ")}</span>
    )},
    { key: "insurance", label: "Insurance", render: v => v.insurance_provider?.name || "Cash" },
    { key: "actions", label: "", render: v => (
      <div className="d-flex gap-1">
        {v.status === "REGISTERED" && (
          <button className="btn btn-sm btn-mc-secondary" onClick={() => updateStatus(v.id, "TRIAGED")}>
            Send to Triage
          </button>
        )}
        {v.status === "TRIAGED" && (
          <button className="btn btn-sm btn-mc-primary" onClick={() => updateStatus(v.id, "WAITING")}>
            To Queue
          </button>
        )}
      </div>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="Patient Visits"
        subtitle="Manage OPD visits and walk-ins"
        actions={
          <button className="btn btn-mc-primary" onClick={() => setShowModal(true)}>
            <i className="bi bi-hospital me-2" />Register Visit
          </button>
        }
      />

      <div className="mc-card mb-3">
        <div className="d-flex gap-2 align-items-center flex-wrap">
          <Tabs
            tabs={[
              { key: "active", label: "Active Visits" },
              { key: "completed", label: "Completed" },
              { key: "all", label: "All Visits" },
            ]}
            active={activeTab}
            onChange={setActiveTab}
          />
          <div className="ms-auto" style={{ minWidth: 260 }}>
            <SearchInput value={search} onChange={v => { setSearch(v); fetchVisits(); }} placeholder="Search visits..." />
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : visits.length === 0 ? (
        <EmptyState icon="bi-hospital" title="No visits found" subtitle="Register a patient visit to get started" />
      ) : (
        <DataTable columns={columns} data={visits} />
      )}

      {/* Register Visit Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setForm(EMPTY_VISIT); }}
        title="Register Patient Visit"
        size="lg"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={handleRegisterVisit} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : null}Register Visit
            </button>
          </>
        }
      >
        <div className="row g-3">
          {/* Patient Search */}
          <FormRow label="Search Patient *" colClass="col-12">
            <input
              className="mc-input mb-2"
              placeholder="Type patient name or phone..."
              value={patientSearch}
              onChange={e => { setPatientSearch(e.target.value); searchPatients(e.target.value); }}
            />
            {patients.length > 0 && (
              <div className="border rounded" style={{ maxHeight: 180, overflowY: "auto" }}>
                {patients.map(p => (
                  <div
                    key={p.id}
                    className={`px-3 py-2 d-flex align-items-center justify-content-between cursor-pointer ${form.patient === p.id ? "bg-primary text-white" : "hover-bg"}`}
                    style={{ cursor: "pointer" }}
                    onClick={() => { setForm(f => ({ ...f, patient: p.id })); setPatientSearch(`${p.first_name} ${p.last_name}`); setPatients([]); }}
                  >
                    <div>
                      <strong>{p.first_name} {p.last_name}</strong>
                      <small className="ms-2 text-muted">{p.phone_number}</small>
                    </div>
                    <small className="text-muted">{p.id_number}</small>
                  </div>
                ))}
              </div>
            )}
            {form.patient && <small className="text-success"><i className="bi bi-check-circle me-1" />Patient selected</small>}
          </FormRow>

          <FormRow label="Visit Type *" colClass="col-md-6">
            <select className="mc-select" value={form.visit_type} onChange={e => setForm(f => ({ ...f, visit_type: e.target.value }))}>
              {VISIT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </FormRow>

          <FormRow label="Insurance Provider" colClass="col-md-6">
            <select className="mc-select" value={form.insurance_provider} onChange={e => setForm(f => ({ ...f, insurance_provider: e.target.value }))}>
              <option value="">Cash / Self-Pay</option>
              {providers.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </FormRow>

          <FormRow label="Specialized Service" colClass="col-md-6">
            <select className="mc-select" value={form.specialized_service} onChange={e => setForm(f => ({ ...f, specialized_service: e.target.value }))}>
              <option value="">General / OPD</option>
              {services.map(s => <option key={s.id} value={s.id}>{s.name} - KSh {s.consultation_fee}</option>)}
            </select>
          </FormRow>

          <FormRow label="Chief Complaint *" colClass="col-12">
            <textarea
              className="mc-input"
              rows={3}
              placeholder="Main reason for visit..."
              value={form.chief_complaint}
              onChange={e => setForm(f => ({ ...f, chief_complaint: e.target.value }))}
            />
          </FormRow>

          <FormRow label="Additional Notes" colClass="col-12">
            <textarea
              className="mc-input"
              rows={2}
              placeholder="Any additional notes..."
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
            />
          </FormRow>
        </div>
      </Modal>
    </Layout>
  );
}