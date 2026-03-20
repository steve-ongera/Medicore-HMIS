import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, FormRow, Badge } from "../../components/common/index.jsx";
import { inpatientApi } from "../../services/api";

export default function NurseInpatient() {
  const [admissions, setAdmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [requests, setRequests] = useState([]);
  const [requestForm, setRequestForm] = useState({ medicine: "", quantity_requested: "", dosage: "", route: "Oral", priority: "ROUTINE", clinical_notes: "" });
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchAdmissions(); }, []);

  async function fetchAdmissions() {
    setLoading(true);
    try {
      const res = await inpatientApi.list({ status: "ACTIVE", ordering: "-admission_datetime" });
      setAdmissions(res.data.results || res.data);
    } catch { showToast("Failed to load inpatients", "error"); }
    finally { setLoading(false); }
  }

  async function openDetail(admission) {
    setSelected(admission);
    setShowDetail(true);
    try {
      const res = await inpatientApi.getMedicineRequests(admission.id);
      setRequests(res.data.results || res.data);
    } catch {}
  }

  const columns = [
    { key: "admission_number", label: "Admission #", render: a => <code className="text-primary">{a.admission_number}</code> },
    { key: "patient", label: "Patient", render: a => <div><div className="fw-medium">{a.patient?.first_name} {a.patient?.last_name}</div><small className="text-muted">Ward: {a.bed?.ward?.ward_name} | Bed: {a.bed?.bed_number}</small></div> },
    { key: "doctor", label: "Doctor", render: a => a.attending_doctor ? `Dr. ${a.attending_doctor.first_name} ${a.attending_doctor.last_name}` : "—" },
    { key: "diagnosis", label: "Diagnosis", render: a => <small className="text-muted">{a.admitting_diagnosis?.substring(0, 60)}</small> },
    { key: "los", label: "LOS", render: a => `${a.length_of_stay || 0}d` },
    { key: "status", label: "Status", render: a => a.is_critical ? <span className="badge bg-danger">Critical</span> : <span className="badge bg-success">Stable</span> },
    { key: "actions", label: "", render: a => (
      <button className="btn btn-icon" onClick={() => openDetail(a)}>
        <i className="bi bi-eye" />
      </button>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Ward Rounds" subtitle={`${admissions.length} active inpatients`} />

      {/* Ward Summary */}
      {admissions.length > 0 && (
        <div className="row g-3 mb-4">
          {[...new Set(admissions.map(a => a.bed?.ward?.ward_name).filter(Boolean))].map(ward => {
            const wAdmissions = admissions.filter(a => a.bed?.ward?.ward_name === ward);
            const critical = wAdmissions.filter(a => a.is_critical).length;
            return (
              <div key={ward} className="col-6 col-md-3">
                <div className="mc-card text-center">
                  <div className="fw-semibold">{ward}</div>
                  <div className="display-6 fw-bold text-primary">{wAdmissions.length}</div>
                  {critical > 0 && <small className="text-danger">{critical} critical</small>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {loading ? <LoadingSpinner /> : admissions.length === 0 ? (
        <EmptyState icon="bi-hospital" title="No active inpatients" subtitle="All wards are currently empty" />
      ) : (
        <DataTable columns={columns} data={admissions} />
      )}

      {/* Patient Detail Modal */}
      <Modal
        show={showDetail && !!selected}
        onClose={() => { setShowDetail(false); setSelected(null); }}
        title={`${selected?.patient?.first_name} ${selected?.patient?.last_name} — ${selected?.admission_number}`}
        size="xl"
      >
        {selected && (
          <div className="row g-3">
            <div className="col-md-6">
              <div className="mc-card">
                <h6 className="fw-semibold mb-3">Admission Details</h6>
                {[
                  ["Ward", selected.bed?.ward?.ward_name],
                  ["Bed", selected.bed?.bed_number],
                  ["Doctor", selected.attending_doctor ? `Dr. ${selected.attending_doctor.first_name} ${selected.attending_doctor.last_name}` : "—"],
                  ["Admitted", new Date(selected.admission_datetime).toLocaleString("en-KE")],
                  ["LOS", `${selected.length_of_stay || 0} day(s)`],
                  ["Diet", selected.diet_order || "Regular"],
                  ["Mobility", selected.mobility_status || "As Tolerated"],
                ].map(([label, value]) => (
                  <div key={label} className="d-flex gap-2 mb-2">
                    <span className="text-muted" style={{ minWidth: 100 }}>{label}:</span>
                    <span className="fw-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="col-md-6">
              <div className="mc-card">
                <h6 className="fw-semibold mb-3">Diagnosis</h6>
                <p className="text-muted">{selected.admitting_diagnosis}</p>
                {selected.is_critical && <div className="mc-alert danger"><i className="bi bi-exclamation-triangle me-2" />Critical Condition — Continuous Monitoring Required</div>}
                {selected.requires_monitoring && <div className="mc-alert warning mt-2"><i className="bi bi-activity me-2" />Continuous Monitoring Required</div>}
              </div>
            </div>
            <div className="col-12">
              <div className="mc-card">
                <h6 className="fw-semibold mb-3">Medicine Requests ({requests.length})</h6>
                {requests.length === 0 ? (
                  <p className="text-muted">No medicine requests for this patient</p>
                ) : (
                  <div>
                    {requests.map(req => (
                      <div key={req.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                        <div>
                          <div className="fw-medium">{req.medicine?.name}</div>
                          <small className="text-muted">{req.dosage} — {req.route} — {req.frequency}</small>
                        </div>
                        <div className="d-flex align-items-center gap-2">
                          <span className={`badge ${req.status === "DISPENSED" ? "bg-success" : req.status === "APPROVED" ? "bg-primary" : req.status === "REJECTED" ? "bg-danger" : "bg-warning text-dark"}`}>{req.status}</span>
                          <span className="text-muted small">{req.priority}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}