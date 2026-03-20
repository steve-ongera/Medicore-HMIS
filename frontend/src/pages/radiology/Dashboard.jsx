import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { imagingApi } from "../../services/api";

export default function RadiologyDashboard() {
  const [studies, setStudies] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchStudies();
    const interval = setInterval(fetchStudies, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchStudies() {
    setLoading(true);
    try {
      const res = await imagingApi.list({ ordering: "-created_at" });
      setStudies(res.data.results || res.data);
    } catch { showToast("Failed to load studies", "error"); }
    finally { setLoading(false); }
  }

  const pending = studies.filter(s => s.status === "PENDING").length;
  const inProgress = studies.filter(s => s.status === "IN_PROGRESS").length;
  const reported = studies.filter(s => s.status === "REPORTED" || s.status === "COMPLETED").length;
  const urgent = studies.filter(s => s.is_urgent && !["REPORTED","COMPLETED","CANCELLED"].includes(s.status)).length;

  const MODALITY_ICONS = { XRAY: "bi-x-ray", CT: "bi-layers", MRI: "bi-magnet", ULTRASOUND: "bi-soundwave" };

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Radiology Dashboard" subtitle="Imaging studies and report management" />

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3"><StatCard label="Pending Studies" value={pending} icon="bi-hourglass-split" color="orange" /></div>
        <div className="col-6 col-md-3"><StatCard label="In Progress" value={inProgress} icon="bi-x-ray" color="blue" /></div>
        <div className="col-6 col-md-3"><StatCard label="Reported Today" value={reported} icon="bi-file-medical" color="green" /></div>
        <div className="col-6 col-md-3"><StatCard label="Urgent Studies" value={urgent} icon="bi-exclamation-triangle" color="red" /></div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-xl-8">
          <div className="mc-card h-100">
            <div className="d-flex justify-content-between mb-3">
              <h6 className="fw-semibold mb-0">Active Studies</h6>
              <Link to="/radiology/studies" className="btn btn-sm btn-mc-primary">View All</Link>
            </div>
            {studies.filter(s => !["REPORTED","COMPLETED","CANCELLED"].includes(s.status)).slice(0, 8).map(s => (
              <div key={s.id} className="d-flex align-items-center gap-3 py-2 border-bottom">
                <i className={`bi ${MODALITY_ICONS[s.modality] || "bi-image"} text-primary`} style={{ fontSize: 22 }} />
                <div className="flex-grow-1">
                  <div className="fw-medium">{s.patient?.first_name} {s.patient?.last_name}</div>
                  <small className="text-muted">{s.modality} — {s.body_part} — {s.study_description}</small>
                </div>
                <div className="d-flex align-items-center gap-2">
                  {s.is_urgent && <span className="badge bg-danger">Urgent</span>}
                  <span className="badge bg-secondary">{s.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-12 col-xl-4">
          <div className="mc-card mb-3">
            <h6 className="fw-semibold mb-3">Quick Actions</h6>
            <div className="d-grid gap-2">
              <Link to="/radiology/studies" className="btn btn-mc-primary"><i className="bi bi-x-ray me-2" />Process Studies</Link>
            </div>
          </div>

          <div className="mc-card">
            <h6 className="fw-semibold mb-3">Modality Breakdown</h6>
            {["XRAY","CT","MRI","ULTRASOUND","MAMMOGRAPHY","OTHER"].map(mod => {
              const count = studies.filter(s => s.modality === mod).length;
              if (!count) return null;
              return (
                <div key={mod} className="d-flex justify-content-between py-2 border-bottom">
                  <div className="d-flex align-items-center gap-2">
                    <i className={`bi ${MODALITY_ICONS[mod] || "bi-image"} text-primary`} />
                    <small>{mod}</small>
                  </div>
                  <span className="fw-semibold">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Layout>
  );
}