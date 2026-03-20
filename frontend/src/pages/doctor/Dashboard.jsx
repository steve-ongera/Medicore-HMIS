import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../App";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { dashboardApi, appointmentApi, visitApi } from "../../services/api";

export default function DoctorDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [todayAppointments, setTodayAppointments] = useState([]);
  const [waitingQueue, setWaitingQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [apptRes, queueRes] = await Promise.all([
        appointmentApi.today(),
        visitApi.list({ status: "WAITING", ordering: "arrival_time" }),
      ]);
      setTodayAppointments(apptRes.data.results || apptRes.data);
      setWaitingQueue(queueRes.data.results || queueRes.data);
    } catch {
      showToast("Failed to load data", "error");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  const completed = todayAppointments.filter(a => a.status === "COMPLETED").length;
  const pending = todayAppointments.filter(a => a.status === "SCHEDULED").length;

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title={`Good ${getGreeting()}, Dr. ${user?.last_name || ""}!`}
        subtitle="Here's your day at a glance"
      />

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <StatCard label="Today's Appointments" value={todayAppointments.length} icon="bi-calendar-check" color="blue" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Waiting for You" value={waitingQueue.length} icon="bi-hourglass-split" color="orange" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Completed Today" value={completed} icon="bi-check-circle" color="green" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Pending" value={pending} icon="bi-clock" color="purple" />
        </div>
      </div>

      <div className="row g-3">
        {/* Waiting Queue */}
        <div className="col-12 col-xl-7">
          <div className="mc-card h-100">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h6 className="fw-semibold mb-0"><i className="bi bi-hourglass-split text-warning me-2" />Patients Waiting ({waitingQueue.length})</h6>
              <Link to="/doctor/consultation" className="btn btn-sm btn-mc-primary">Start Consultations</Link>
            </div>
            {waitingQueue.length === 0 ? (
              <EmptyState icon="bi-check2-all" title="No patients waiting" subtitle="Your queue is empty" />
            ) : (
              <div>
                {waitingQueue.map((visit, idx) => {
                  const triage = visit.triage;
                  const TRIAGE_COLORS = { RED: "#dc2626", ORANGE: "#f97316", YELLOW: "#eab308", GREEN: "#16a34a", BLUE: "#2563eb" };
                  const triageColor = TRIAGE_COLORS[triage?.category?.color_code] || "#6b7280";
                  return (
                    <div key={visit.id} className="d-flex align-items-center gap-3 py-3 border-bottom">
                      <div className="fw-bold text-muted" style={{ minWidth: 28 }}>#{idx + 1}</div>
                      <div className="rounded-circle" style={{ width: 12, height: 12, background: triageColor, flexShrink: 0 }} />
                      <div className="flex-grow-1">
                        <div className="fw-medium">{visit.patient_name || "Patient"}</div>
                        <small className="text-muted">{visit.chief_complaint?.substring(0, 50)}</small>
                      </div>
                      <div className="text-end">
                        <small className="text-muted d-block">
                          {Math.round((Date.now() - new Date(visit.arrival_time)) / 60000)} min
                        </small>
                        <Link to={`/doctor/consultation?visit=${visit.id}`} className="btn btn-sm btn-mc-primary">
                          See Patient
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Today's Schedule */}
        <div className="col-12 col-xl-5">
          <div className="mc-card h-100">
            <h6 className="fw-semibold mb-3"><i className="bi bi-calendar3 text-primary me-2" />Today's Appointments</h6>
            {todayAppointments.length === 0 ? (
              <EmptyState icon="bi-calendar-x" title="No appointments today" subtitle="" />
            ) : (
              <div>
                {todayAppointments.map(appt => (
                  <div key={appt.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div>
                      <div className="fw-medium">{appt.patient?.first_name} {appt.patient?.last_name}</div>
                      <small className="text-muted">{new Date(appt.scheduled_time).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" })} — {appt.reason?.substring(0, 30)}</small>
                    </div>
                    <span className={`badge ${appt.status === "COMPLETED" ? "bg-success" : appt.status === "IN_PROGRESS" ? "bg-primary" : appt.status === "CANCELLED" ? "bg-danger" : "bg-secondary"}`}>
                      {appt.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  return h < 12 ? "Morning" : h < 17 ? "Afternoon" : "Evening";
}