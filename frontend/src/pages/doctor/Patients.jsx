import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, SearchInput } from "../../components/common/index.jsx";
import { patientApi } from "../../services/api";

export default function DoctorPatients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);
  const [history, setHistory] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchPatients(); }, [search]);

  async function fetchPatients() {
    setLoading(true);
    try {
      const res = await patientApi.list({ search, ordering: "-created_at" });
      setPatients(res.data.results || res.data);
    } catch { showToast("Failed to load patients", "error"); }
    finally { setLoading(false); }
  }

  async function openPatient(patient) {
    setSelected(patient);
    setShowModal(true);
    try {
      const [histRes, visitRes] = await Promise.all([
        patientApi.medicalHistory(patient.id),
        patientApi.visits(patient.id),
      ]);
      setHistory(histRes.data.results || histRes.data);
      setConsultations(visitRes.data.results || visitRes.data);
    } catch {}
  }

  const calcAge = dob => {
    const birth = new Date(dob);
    const today = new Date();
    return today.getFullYear() - birth.getFullYear();
  };

  const columns = [
    { key: "name", label: "Patient", render: p => <div><div className="fw-medium">{p.first_name} {p.last_name}</div><small className="text-muted">{p.id_number}</small></div> },
    { key: "age", label: "Age", render: p => p.date_of_birth ? `${calcAge(p.date_of_birth)} yrs` : "—" },
    { key: "gender", label: "Gender", render: p => p.gender === "M" ? "Male" : p.gender === "F" ? "Female" : "Other" },
    { key: "blood_type", label: "Blood", render: p => p.blood_type || "—" },
    { key: "phone", label: "Phone", render: p => p.phone_number },
    { key: "actions", label: "", render: p => (
      <button className="btn btn-icon" onClick={() => openPatient(p)}>
        <i className="bi bi-folder2-open" />
      </button>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Patient Records" subtitle="View patient history and records" />
      <div className="mc-card mb-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Search patients..." />
      </div>
      {loading ? <LoadingSpinner /> : patients.length === 0 ? (
        <EmptyState icon="bi-person-x" title="No patients found" />
      ) : <DataTable columns={columns} data={patients} />}

      <Modal show={showModal} onClose={() => setShowModal(false)} title={`${selected?.first_name} ${selected?.last_name} — Medical Record`} size="xl">
        {selected && (
          <div className="row g-3">
            {/* Patient Info */}
            <div className="col-md-4">
              <div className="mc-card text-center mb-3">
                <div className="rounded-circle bg-primary bg-opacity-10 d-inline-flex align-items-center justify-content-center mb-2" style={{ width: 64, height: 64 }}>
                  <i className="bi bi-person-fill text-primary" style={{ fontSize: 28 }} />
                </div>
                <div className="fw-bold">{selected.first_name} {selected.last_name}</div>
                <div className="text-muted small">{selected.id_number}</div>
                <div className="d-flex justify-content-center gap-3 mt-2">
                  <div><span className="text-muted small">Age</span><div className="fw-medium">{selected.date_of_birth ? calcAge(selected.date_of_birth) : "?"}</div></div>
                  <div><span className="text-muted small">Gender</span><div className="fw-medium">{selected.gender === "M" ? "Male" : "Female"}</div></div>
                  <div><span className="text-muted small">Blood</span><div className="fw-medium">{selected.blood_type || "?"}</div></div>
                </div>
              </div>
              {selected.allergies && (
                <div className="mc-alert danger">
                  <i className="bi bi-exclamation-triangle me-2" /><strong>Allergies:</strong> {selected.allergies}
                </div>
              )}
            </div>
            <div className="col-md-8">
              <h6 className="fw-semibold mb-3">Recent Visits ({consultations.length})</h6>
              {consultations.length === 0 ? <p className="text-muted">No previous visits</p> : (
                <div style={{ maxHeight: 300, overflowY: "auto" }}>
                  {consultations.map(visit => (
                    <div key={visit.id} className="border rounded p-3 mb-2">
                      <div className="d-flex justify-content-between mb-1">
                        <span className="fw-medium">{visit.visit_number}</span>
                        <small className="text-muted">{new Date(visit.arrival_time).toLocaleDateString("en-KE")}</small>
                      </div>
                      <p className="text-muted small mb-0">{visit.chief_complaint}</p>
                    </div>
                  ))}
                </div>
              )}
              <h6 className="fw-semibold mb-3 mt-4">Medical History ({history.length})</h6>
              {history.length === 0 ? <p className="text-muted">No medical history recorded</p> : (
                <div style={{ maxHeight: 200, overflowY: "auto" }}>
                  {history.map(h => (
                    <div key={h.id} className="border-bottom py-2">
                      <div className="d-flex gap-2">
                        <span className="badge bg-secondary">{h.record_type}</span>
                        <small className="text-muted">{h.date_recorded}</small>
                      </div>
                      <p className="small mb-0 mt-1">{h.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}