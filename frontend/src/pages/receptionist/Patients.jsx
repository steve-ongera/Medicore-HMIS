import { useState, useEffect, useRef } from "react";
import Layout from "../../components/layout/Layout";
import {
  PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer,
  SearchInput, DataTable, FormRow
} from "../../components/common/index.jsx";
import { patientApi } from "../../services/api";

const EMPTY_FORM = {
  first_name: "", last_name: "", date_of_birth: "", gender: "",
  id_number: "", phone_number: "", email: "", address: "",
  blood_type: "", allergies: "",
};

export default function ReceptionPatients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const { toasts, showToast, removeToast } = useToast();
  const searchTimeout = useRef(null);

  useEffect(() => { fetchPatients(); }, [page]);

  useEffect(() => {
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => { setPage(1); fetchPatients(search); }, 400);
  }, [search]);

  async function fetchPatients(q = search) {
    setLoading(true);
    try {
      const res = await patientApi.list({ search: q, page, ordering: "-created_at" });
      setPatients(res.data.results || res.data);
      setCount(res.data.count || 0);
    } catch {
      showToast("Failed to load patients", "error");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!form.first_name || !form.last_name || !form.date_of_birth || !form.gender || !form.phone_number) {
      showToast("Please fill all required fields", "error"); return;
    }
    setSaving(true);
    try {
      if (selectedPatient) {
        await patientApi.update(selectedPatient.id, form);
        showToast("Patient updated successfully", "success");
      } else {
        await patientApi.create(form);
        showToast("Patient registered successfully", "success");
      }
      setShowModal(false);
      setForm(EMPTY_FORM);
      setSelectedPatient(null);
      fetchPatients();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to save patient", "error");
    } finally {
      setSaving(false);
    }
  }

  function openEdit(patient) {
    setSelectedPatient(patient);
    setForm({
      first_name: patient.first_name, last_name: patient.last_name,
      date_of_birth: patient.date_of_birth, gender: patient.gender,
      id_number: patient.id_number, phone_number: patient.phone_number,
      email: patient.email || "", address: patient.address || "",
      blood_type: patient.blood_type || "", allergies: patient.allergies || "",
    });
    setShowModal(true);
  }

  const columns = [
    { key: "name", label: "Patient Name", render: p => (
      <div>
        <div className="fw-medium">{p.first_name} {p.last_name}</div>
        <small className="text-muted">{p.id_number}</small>
      </div>
    )},
    { key: "phone_number", label: "Phone" },
    { key: "gender", label: "Gender", render: p => p.gender === "M" ? "Male" : p.gender === "F" ? "Female" : "Other" },
    { key: "date_of_birth", label: "Date of Birth" },
    { key: "blood_type", label: "Blood Type", render: p => p.blood_type || "-" },
    { key: "actions", label: "Actions", render: p => (
      <div className="d-flex gap-1">
        <button className="btn btn-icon" onClick={() => openEdit(p)} title="Edit">
          <i className="bi bi-pencil" />
        </button>
        <button className="btn btn-icon text-primary" onClick={() => window.location.href=`/reception/visits/new?patient=${p.id}`} title="Register Visit">
          <i className="bi bi-hospital" />
        </button>
      </div>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="Patients"
        subtitle={`${count} total patients`}
        actions={
          <button className="btn btn-mc-primary" onClick={() => { setSelectedPatient(null); setForm(EMPTY_FORM); setShowModal(true); }}>
            <i className="bi bi-person-plus me-2" />Register Patient
          </button>
        }
      />

      <div className="mc-card mb-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Search by name, phone, or ID number..." />
      </div>

      {loading ? <LoadingSpinner /> : (
        patients.length === 0 ? (
          <EmptyState icon="bi-person-x" title="No patients found" subtitle="Register a new patient or adjust your search" />
        ) : (
          <DataTable columns={columns} data={patients} />
        )
      )}

      {count > 20 && (
        <div className="d-flex justify-content-center mt-3 gap-2">
          <button className="btn btn-mc-secondary btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button>
          <span className="align-self-center text-muted small">Page {page} of {Math.ceil(count / 20)}</span>
          <button className="btn btn-mc-secondary btn-sm" disabled={page * 20 >= count} onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      )}

      {/* Register/Edit Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setSelectedPatient(null); setForm(EMPTY_FORM); }}
        title={selectedPatient ? "Edit Patient" : "Register New Patient"}
        size="lg"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={handleSave} disabled={saving}>
              {saving ? <><span className="spinner-border spinner-border-sm me-2" />Saving...</> : "Save Patient"}
            </button>
          </>
        }
      >
        <div className="row g-3">
          <FormRow label="First Name *" colClass="col-md-6">
            <input className="mc-input" value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} placeholder="First name" />
          </FormRow>
          <FormRow label="Last Name *" colClass="col-md-6">
            <input className="mc-input" value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} placeholder="Last name" />
          </FormRow>
          <FormRow label="Date of Birth *" colClass="col-md-6">
            <input type="date" className="mc-input" value={form.date_of_birth} onChange={e => setForm(f => ({ ...f, date_of_birth: e.target.value }))} />
          </FormRow>
          <FormRow label="Gender *" colClass="col-md-6">
            <select className="mc-select" value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}>
              <option value="">Select Gender</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </FormRow>
          <FormRow label="ID/Passport Number" colClass="col-md-6">
            <input className="mc-input" value={form.id_number} onChange={e => setForm(f => ({ ...f, id_number: e.target.value }))} placeholder="National ID or Passport" />
          </FormRow>
          <FormRow label="Phone Number *" colClass="col-md-6">
            <input className="mc-input" value={form.phone_number} onChange={e => setForm(f => ({ ...f, phone_number: e.target.value }))} placeholder="e.g. 0712345678" />
          </FormRow>
          <FormRow label="Email" colClass="col-md-6">
            <input type="email" className="mc-input" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} placeholder="Email address" />
          </FormRow>
          <FormRow label="Blood Type" colClass="col-md-6">
            <select className="mc-select" value={form.blood_type} onChange={e => setForm(f => ({ ...f, blood_type: e.target.value }))}>
              <option value="">Unknown</option>
              {["A+","A-","B+","B-","AB+","AB-","O+","O-"].map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </FormRow>
          <FormRow label="Address" colClass="col-12">
            <textarea className="mc-input" rows={2} value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} placeholder="Home address" />
          </FormRow>
          <FormRow label="Allergies" colClass="col-12">
            <textarea className="mc-input" rows={2} value={form.allergies} onChange={e => setForm(f => ({ ...f, allergies: e.target.value }))} placeholder="Known allergies (leave blank if none)" />
          </FormRow>
        </div>
      </Modal>
    </Layout>
  );
}