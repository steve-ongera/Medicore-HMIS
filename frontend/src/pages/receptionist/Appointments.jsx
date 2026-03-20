import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import {
  PageHeader, LoadingSpinner, EmptyState, Modal, useToast,
  ToastContainer, DataTable, FormRow, Tabs, SearchInput
} from "../../components/common/index.jsx";
import { appointmentApi, patientApi, userApi } from "../../services/api";

const EMPTY_FORM = {
  patient: "", doctor: "", scheduled_time: "", reason: "", symptoms: "",
};

export default function ReceptionAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("today");
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [patientSearch, setPatientSearch] = useState("");
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchAppointments(); fetchDoctors(); }, [activeTab]);

  async function fetchAppointments() {
    setLoading(true);
    try {
      const today = new Date().toISOString().split("T")[0];
      let params = { ordering: "scheduled_time" };
      if (activeTab === "today") params.date = today;
      else if (activeTab === "upcoming") params.status = "SCHEDULED";
      const res = await appointmentApi.list(params);
      setAppointments(res.data.results || res.data);
    } catch { showToast("Failed to load appointments", "error"); }
    finally { setLoading(false); }
  }

  async function fetchDoctors() {
    try {
      const res = await userApi.list({ user_type: "DOCTOR" });
      setDoctors(res.data.results || res.data);
    } catch {}
  }

  async function searchPatients(q) {
    if (!q || q.length < 2) { setPatients([]); return; }
    try {
      const res = await patientApi.list({ search: q });
      setPatients(res.data.results || res.data);
    } catch {}
  }

  async function handleBook() {
    if (!form.patient || !form.doctor || !form.scheduled_time || !form.reason) {
      showToast("Please fill all required fields", "error"); return;
    }
    setSaving(true);
    try {
      await appointmentApi.create(form);
      showToast("Appointment booked successfully", "success");
      setShowModal(false);
      setForm(EMPTY_FORM);
      setPatientSearch("");
      fetchAppointments();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to book appointment", "error");
    } finally { setSaving(false); }
  }

  async function cancelAppointment(id) {
    if (!confirm("Cancel this appointment?")) return;
    try {
      await appointmentApi.updateStatus(id, { status: "CANCELLED" });
      showToast("Appointment cancelled", "success");
      fetchAppointments();
    } catch { showToast("Failed to cancel", "error"); }
  }

  const STATUS_BADGE = {
    SCHEDULED: "bg-primary", IN_PROGRESS: "bg-warning text-dark",
    COMPLETED: "bg-success", CANCELLED: "bg-danger", NO_SHOW: "bg-secondary",
  };

  const columns = [
    { key: "time", label: "Date & Time", render: a => (
      <div>
        <div className="fw-medium">{new Date(a.scheduled_time).toLocaleDateString("en-KE")}</div>
        <small className="text-muted">{new Date(a.scheduled_time).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" })}</small>
      </div>
    )},
    { key: "patient", label: "Patient", render: a => (
      <div>
        <div className="fw-medium">{a.patient?.first_name} {a.patient?.last_name}</div>
        <small className="text-muted">{a.patient?.phone_number}</small>
      </div>
    )},
    { key: "doctor", label: "Doctor", render: a => `Dr. ${a.doctor?.first_name || ""} ${a.doctor?.last_name || ""}` },
    { key: "reason", label: "Reason", render: a => <span className="text-muted small">{a.reason?.substring(0, 60)}{a.reason?.length > 60 ? "..." : ""}</span> },
    { key: "status", label: "Status", render: a => <span className={`badge ${STATUS_BADGE[a.status] || "bg-secondary"}`}>{a.status}</span> },
    { key: "actions", label: "", render: a => (
      a.status === "SCHEDULED" ? (
        <button className="btn btn-icon text-danger" onClick={() => cancelAppointment(a.id)}>
          <i className="bi bi-x-circle" />
        </button>
      ) : null
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="Appointments"
        subtitle="Book and manage patient appointments"
        actions={
          <button className="btn btn-mc-primary" onClick={() => setShowModal(true)}>
            <i className="bi bi-calendar-plus me-2" />Book Appointment
          </button>
        }
      />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[
            { key: "today", label: "Today" },
            { key: "upcoming", label: "Upcoming" },
            { key: "all", label: "All" },
          ]}
          active={activeTab}
          onChange={setActiveTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : appointments.length === 0 ? (
        <EmptyState icon="bi-calendar-x" title="No appointments found" subtitle="Book a new appointment to get started" />
      ) : (
        <DataTable columns={columns} data={appointments} />
      )}

      {/* Book Appointment Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setForm(EMPTY_FORM); setPatientSearch(""); }}
        title="Book Appointment"
        size="lg"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={handleBook} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : null}Book Appointment
            </button>
          </>
        }
      >
        <div className="row g-3">
          <FormRow label="Search Patient *" colClass="col-12">
            <input
              className="mc-input mb-2"
              placeholder="Type patient name..."
              value={patientSearch}
              onChange={e => { setPatientSearch(e.target.value); searchPatients(e.target.value); }}
            />
            {patients.length > 0 && (
              <div className="border rounded" style={{ maxHeight: 160, overflowY: "auto" }}>
                {patients.map(p => (
                  <div
                    key={p.id}
                    className="px-3 py-2 d-flex align-items-center justify-content-between"
                    style={{ cursor: "pointer" }}
                    onClick={() => { setForm(f => ({ ...f, patient: p.id })); setPatientSearch(`${p.first_name} ${p.last_name}`); setPatients([]); }}
                  >
                    <strong>{p.first_name} {p.last_name}</strong>
                    <small className="text-muted">{p.phone_number}</small>
                  </div>
                ))}
              </div>
            )}
            {form.patient && <small className="text-success"><i className="bi bi-check-circle me-1" />Patient selected</small>}
          </FormRow>

          <FormRow label="Doctor *" colClass="col-md-6">
            <select className="mc-select" value={form.doctor} onChange={e => setForm(f => ({ ...f, doctor: e.target.value }))}>
              <option value="">Select Doctor</option>
              {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.first_name} {d.last_name} - {d.specialization || "General"}</option>)}
            </select>
          </FormRow>

          <FormRow label="Scheduled Date & Time *" colClass="col-md-6">
            <input
              type="datetime-local"
              className="mc-input"
              value={form.scheduled_time}
              onChange={e => setForm(f => ({ ...f, scheduled_time: e.target.value }))}
            />
          </FormRow>

          <FormRow label="Reason for Visit *" colClass="col-12">
            <textarea className="mc-input" rows={3} value={form.reason} onChange={e => setForm(f => ({ ...f, reason: e.target.value }))} placeholder="Reason for appointment..." />
          </FormRow>

          <FormRow label="Symptoms" colClass="col-12">
            <textarea className="mc-input" rows={2} value={form.symptoms} onChange={e => setForm(f => ({ ...f, symptoms: e.target.value }))} placeholder="Presenting symptoms..." />
          </FormRow>
        </div>
      </Modal>
    </Layout>
  );
}