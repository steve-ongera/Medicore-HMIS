import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, useToast, ToastContainer } from "../../components/common/index.jsx";
import { queueApi } from "../../services/api";

const DEPARTMENTS = [
  { value: "TRIAGE", label: "Triage", icon: "bi-heart-pulse" },
  { value: "CONSULTATION", label: "Consultation", icon: "bi-person-badge" },
  { value: "LABORATORY", label: "Laboratory", icon: "bi-eyedropper" },
  { value: "PHARMACY", label: "Pharmacy", icon: "bi-capsule" },
  { value: "RADIOLOGY", label: "Radiology", icon: "bi-x-ray" },
];

const TRIAGE_COLORS = { RED: "#dc2626", ORANGE: "#f97316", YELLOW: "#eab308", GREEN: "#16a34a", BLUE: "#2563eb" };

export default function ReceptionQueue() {
  const [queues, setQueues] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeDept, setActiveDept] = useState("CONSULTATION");
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 15000);
    return () => clearInterval(interval);
  }, [activeDept]);

  async function fetchQueue() {
    try {
      const res = await queueApi.list({ department: activeDept, is_active: true, ordering: "queue_number" });
      setQueues(prev => ({ ...prev, [activeDept]: res.data.results || res.data }));
    } catch {
      showToast("Failed to load queue", "error");
    } finally {
      setLoading(false);
    }
  }

  async function callPatient(queueId) {
    try {
      await queueApi.callPatient(queueId);
      showToast("Patient called", "success");
      fetchQueue();
    } catch { showToast("Failed to call patient", "error"); }
  }

  const currentQueue = queues[activeDept] || [];
  const serving = currentQueue.filter(q => q.is_serving);
  const waiting = currentQueue.filter(q => !q.is_serving && !q.is_completed);

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Queue Management" subtitle="Monitor and manage patient queues" />

      {/* Department Tabs */}
      <div className="mc-card mb-3">
        <div className="d-flex gap-2 overflow-x-auto pb-1">
          {DEPARTMENTS.map(dept => (
            <button
              key={dept.value}
              className={`btn ${activeDept === dept.value ? "btn-mc-primary" : "btn-mc-secondary"} d-flex align-items-center gap-2`}
              onClick={() => setActiveDept(dept.value)}
            >
              <i className={dept.icon} />
              <span>{dept.label}</span>
              {queues[dept.value] && (
                <span className="badge bg-white text-dark">{queues[dept.value].filter(q => !q.is_completed).length}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="row g-3">
          {/* Now Serving */}
          <div className="col-12 col-md-4">
            <div className="mc-card h-100" style={{ borderLeft: "4px solid var(--mc-blue)" }}>
              <h6 className="fw-semibold mb-3 d-flex align-items-center gap-2">
                <span className="badge bg-primary rounded-circle p-2"><i className="bi bi-person-check" /></span>
                Now Serving
              </h6>
              {serving.length === 0 ? (
                <EmptyState icon="bi-person-dash" title="No one being served" subtitle="Call next patient" />
              ) : serving.map(q => <QueueCard key={q.id} queue={q} serving />)}
            </div>
          </div>

          {/* Waiting */}
          <div className="col-12 col-md-8">
            <div className="mc-card h-100">
              <h6 className="fw-semibold mb-3 d-flex align-items-center gap-2">
                <span className="badge bg-warning text-dark rounded-circle p-2"><i className="bi bi-hourglass-split" /></span>
                Waiting ({waiting.length})
              </h6>
              {waiting.length === 0 ? (
                <EmptyState icon="bi-check2-all" title="Queue is empty" subtitle="All patients have been served" />
              ) : (
                <div className="row g-2">
                  {waiting.map(q => (
                    <div key={q.id} className="col-12 col-sm-6 col-lg-4">
                      <QueueCard queue={q} onCall={() => callPatient(q.id)} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}

function QueueCard({ queue, onCall, serving }) {
  const waitMins = Math.round(queue.wait_time || 0);
  const triageColor = queue.visit?.triage?.category?.color_code;
  return (
    <div className={`border rounded p-3 mb-2 ${serving ? "border-primary bg-primary bg-opacity-10" : ""}`}>
      <div className="d-flex align-items-start justify-content-between">
        <div>
          <div className="d-flex align-items-center gap-2 mb-1">
            {triageColor && (
              <span className="rounded-circle" style={{ width: 10, height: 10, background: TRIAGE_COLORS[triageColor] || "#ccc", display: "inline-block" }} />
            )}
            <span className="fw-bold text-primary" style={{ fontSize: 20 }}>#{queue.queue_number}</span>
          </div>
          <div className="fw-medium">{queue.visit?.patient_name || "Patient"}</div>
          <small className="text-muted">{queue.visit?.visit_type?.replace("_", " ")}</small>
        </div>
        <div className="text-end">
          <div className="text-muted small">{waitMins} min wait</div>
          {!serving && onCall && (
            <button className="btn btn-sm btn-mc-primary mt-1" onClick={onCall}>
              <i className="bi bi-megaphone me-1" />Call
            </button>
          )}
        </div>
      </div>
    </div>
  );
}