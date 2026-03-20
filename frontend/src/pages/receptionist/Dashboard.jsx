import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, Badge, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { dashboardApi, visitApi, appointmentApi, queueApi } from "../../services/api";

export default function ReceptionDashboard() {
  const [stats, setStats] = useState(null);
  const [todayVisits, setTodayVisits] = useState([]);
  const [waitingQueue, setWaitingQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchDashboardData() {
    try {
      const [statsRes, visitsRes] = await Promise.all([
        dashboardApi.getStats(),
        visitApi.list({ status: "REGISTERED,TRIAGED,WAITING", ordering: "-arrival_time", limit: 10 }),
      ]);
      setStats(statsRes.data);
      setTodayVisits(visitsRes.data.results || visitsRes.data);
    } catch {
      showToast("Failed to load dashboard data", "error");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  const activeVisits = todayVisits.filter(v => !["COMPLETED","CANCELLED"].includes(v.status));

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="Reception Dashboard"
        subtitle={`${new Date().toLocaleDateString("en-KE", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}`}
        actions={
          <Link to="/reception/visits/new" className="btn btn-mc-primary">
            <i className="bi bi-person-plus me-2" />Register Patient
          </Link>
        }
      />

      {/* Stats */}
      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <StatCard label="Today's Visits" value={stats?.today_visits ?? 0} icon="bi-person-check" color="blue" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="In Queue" value={activeVisits.length} icon="bi-list-ol" color="orange" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Appointments Today" value={stats?.today_appointments ?? 0} icon="bi-calendar-check" color="teal" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Registered This Week" value={stats?.week_visits ?? 0} icon="bi-graph-up" color="purple" />
        </div>
      </div>

      <div className="row g-3">
        {/* Today's Active Visits */}
        <div className="col-12 col-xl-8">
          <div className="mc-card h-100">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h6 className="fw-semibold mb-0">Active Visits Today</h6>
              <Link to="/reception/visits" className="btn btn-sm btn-mc-secondary">View All</Link>
            </div>
            {activeVisits.length === 0 ? (
              <EmptyState icon="bi-person-x" title="No active visits" subtitle="Register a patient to get started" />
            ) : (
              <div className="mc-table-wrapper">
                <table className="mc-table">
                  <thead>
                    <tr>
                      <th>Visit #</th>
                      <th>Patient</th>
                      <th>Type</th>
                      <th>Arrival</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeVisits.map(visit => (
                      <tr key={visit.id}>
                        <td><code className="text-primary">{visit.visit_number}</code></td>
                        <td>
                          <div className="fw-medium">{visit.patient_name || `${visit.patient?.first_name} ${visit.patient?.last_name}`}</div>
                          <small className="text-muted">{visit.visit_type}</small>
                        </td>
                        <td><Badge text={visit.visit_type} variant="info" /></td>
                        <td>
                          <small>{new Date(visit.arrival_time).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" })}</small>
                        </td>
                        <td><VisitStatusBadge status={visit.status} /></td>
                        <td>
                          <Link to={`/reception/visits/${visit.id}`} className="btn btn-icon">
                            <i className="bi bi-eye" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="col-12 col-xl-4">
          <div className="mc-card mb-3">
            <h6 className="fw-semibold mb-3">Quick Actions</h6>
            <div className="d-grid gap-2">
              <Link to="/reception/visits/new" className="btn btn-mc-primary">
                <i className="bi bi-person-plus me-2" />Register New Patient
              </Link>
              <Link to="/reception/patients" className="btn btn-mc-secondary">
                <i className="bi bi-search me-2" />Search Patient
              </Link>
              <Link to="/reception/appointments" className="btn btn-mc-secondary">
                <i className="bi bi-calendar-plus me-2" />Book Appointment
              </Link>
              <Link to="/reception/queue" className="btn btn-mc-secondary">
                <i className="bi bi-list-ol me-2" />View Queue
              </Link>
            </div>
          </div>

          {/* Visit Type Breakdown */}
          <div className="mc-card">
            <h6 className="fw-semibold mb-3">Today's Visit Types</h6>
            {[
              { type: "OUTPATIENT", label: "Outpatient", color: "blue" },
              { type: "EMERGENCY", label: "Emergency", color: "red" },
              { type: "FOLLOW_UP", label: "Follow-up", color: "green" },
              { type: "INPATIENT", label: "Inpatient", color: "purple" },
            ].map(({ type, label, color }) => {
              const count = todayVisits.filter(v => v.visit_type === type).length;
              return (
                <div key={type} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                  <div className="d-flex align-items-center gap-2">
                    <span className={`badge bg-${color === "blue" ? "primary" : color === "red" ? "danger" : color === "green" ? "success" : "secondary"}`} style={{ width: 10, height: 10, borderRadius: "50%", padding: 0 }}>&nbsp;</span>
                    <span className="text-muted small">{label}</span>
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

function VisitStatusBadge({ status }) {
  const map = {
    REGISTERED: { label: "Registered", cls: "bg-secondary" },
    TRIAGED: { label: "Triaged", cls: "bg-warning text-dark" },
    WAITING: { label: "Waiting", cls: "bg-info text-dark" },
    IN_CONSULTATION: { label: "In Consult", cls: "bg-primary" },
    COMPLETED: { label: "Completed", cls: "bg-success" },
    CANCELLED: { label: "Cancelled", cls: "bg-danger" },
  };
  const s = map[status] || { label: status, cls: "bg-secondary" };
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}