import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { visitApi, queueApi } from "../../services/api";

export default function NurseDashboard() {
  const [waiting, setWaiting] = useState([]);
  const [triaged, setTriaged] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 20000);
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [waitRes, triageRes] = await Promise.all([
        visitApi.list({ status: "REGISTERED", ordering: "-arrival_time" }),
        visitApi.list({ status: "TRIAGED,WAITING", ordering: "-arrival_time" }),
      ]);
      setWaiting(waitRes.data.results || waitRes.data);
      setTriaged(triageRes.data.results || triageRes.data);
    } catch {
      showToast("Failed to load data", "error");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Nurse Dashboard" subtitle="Triage and vitals management" />

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <StatCard label="Awaiting Triage" value={waiting.length} icon="bi-clock" color="orange" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Triaged Today" value={triaged.length} icon="bi-heart-pulse" color="blue" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="In Consultation" value={triaged.filter(v => v.status === "IN_CONSULTATION").length} icon="bi-person-badge" color="teal" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Waiting Room" value={triaged.filter(v => v.status === "WAITING").length} icon="bi-hourglass-split" color="purple" />
        </div>
      </div>

      <div className="row g-3">
        {/* Awaiting Triage */}
        <div className="col-12 col-xl-6">
          <div className="mc-card h-100">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h6 className="fw-semibold mb-0">
                <i className="bi bi-clock text-warning me-2" />Awaiting Triage ({waiting.length})
              </h6>
              <Link to="/nurse/triage" className="btn btn-sm btn-mc-primary">Open Triage</Link>
            </div>
            {waiting.length === 0 ? (
              <EmptyState icon="bi-check2-all" title="No patients waiting for triage" subtitle="All patients have been assessed" />
            ) : (
              <div>
                {waiting.slice(0, 8).map(visit => (
                  <div key={visit.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div>
                      <div className="fw-medium">{visit.patient_name || "Patient"}</div>
                      <small className="text-muted">{visit.chief_complaint?.substring(0, 50)}</small>
                    </div>
                    <div className="text-end">
                      <small className="text-muted d-block">
                        {Math.round((Date.now() - new Date(visit.arrival_time)) / 60000)} min ago
                      </small>
                      <Link to={`/nurse/triage?visit=${visit.id}`} className="btn btn-sm btn-mc-primary mt-1">
                        Triage
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions & Inpatient */}
        <div className="col-12 col-xl-6">
          <div className="mc-card mb-3">
            <h6 className="fw-semibold mb-3">Quick Actions</h6>
            <div className="d-grid gap-2">
              <Link to="/nurse/triage" className="btn btn-mc-primary">
                <i className="bi bi-heart-pulse me-2" />Start Triage Assessment
              </Link>
              <Link to="/nurse/vitals" className="btn btn-mc-secondary">
                <i className="bi bi-activity me-2" />Record Patient Vitals
              </Link>
              <Link to="/nurse/inpatient" className="btn btn-mc-secondary">
                <i className="bi bi-hospital me-2" />Inpatient Ward Rounds
              </Link>
            </div>
          </div>

          {/* Triage Priority Summary */}
          <div className="mc-card">
            <h6 className="fw-semibold mb-3">Triage Priority Queue</h6>
            {[
              { color: "RED", label: "Red (Emergency)", bg: "#dc2626" },
              { color: "ORANGE", label: "Orange (Very Urgent)", bg: "#f97316" },
              { color: "YELLOW", label: "Yellow (Urgent)", bg: "#eab308" },
              { color: "GREEN", label: "Green (Standard)", bg: "#16a34a" },
            ].map(({ color, label, bg }) => {
              const count = triaged.filter(v => v.triage?.category?.color_code === color).length;
              return (
                <div key={color} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                  <div className="d-flex align-items-center gap-2">
                    <span className="rounded-circle" style={{ width: 12, height: 12, background: bg, display: "inline-block" }} />
                    <span className="small">{label}</span>
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