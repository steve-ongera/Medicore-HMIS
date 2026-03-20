import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { labApi } from "../../services/api";

export default function LabDashboard() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchOrders() {
    setLoading(true);
    try {
      const res = await labApi.orders({ ordering: "-ordered_at" });
      setOrders(res.data.results || res.data);
    } catch { showToast("Failed to load lab orders", "error"); }
    finally { setLoading(false); }
  }

  const pending = orders.filter(o => o.status === "PENDING").length;
  const inProgress = orders.filter(o => o.status === "SAMPLE_COLLECTED" || o.status === "IN_PROGRESS").length;
  const completed = orders.filter(o => o.status === "COMPLETED" || o.status === "REPORTED").length;
  const critical = orders.filter(o => o.result?.is_critical).length;

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Laboratory Dashboard" subtitle="Lab order and result management" />

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3"><StatCard label="Pending Orders" value={pending} icon="bi-hourglass-split" color="orange" /></div>
        <div className="col-6 col-md-3"><StatCard label="In Progress" value={inProgress} icon="bi-eyedropper" color="blue" /></div>
        <div className="col-6 col-md-3"><StatCard label="Completed Today" value={completed} icon="bi-check-circle" color="green" /></div>
        <div className="col-6 col-md-3"><StatCard label="Critical Results" value={critical} icon="bi-exclamation-octagon" color="red" /></div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-xl-8">
          <div className="mc-card h-100">
            <div className="d-flex justify-content-between mb-3">
              <h6 className="fw-semibold mb-0">Active Lab Orders</h6>
              <Link to="/lab/orders" className="btn btn-sm btn-mc-primary">View All Orders</Link>
            </div>
            {orders.filter(o => !["COMPLETED","REPORTED","CANCELLED"].includes(o.status)).slice(0, 8).map(order => (
              <div key={order.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                <div>
                  <code className="text-primary me-2">{order.order_number}</code>
                  <span className="fw-medium">{order.patient?.first_name} {order.patient?.last_name}</span>
                  <small className="text-muted ms-2">{order.test_items?.length || 0} test(s)</small>
                </div>
                <div className="d-flex align-items-center gap-2">
                  <span className={`badge ${order.priority === "STAT" || order.priority === "EMERGENCY" ? "bg-danger" : order.priority === "URGENT" ? "bg-warning text-dark" : "bg-secondary"}`}>
                    {order.priority}
                  </span>
                  <Link to={`/lab/orders?order=${order.id}`} className="btn btn-sm btn-mc-secondary">Process</Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-12 col-xl-4">
          <div className="mc-card mb-3">
            <h6 className="fw-semibold mb-3">Quick Actions</h6>
            <div className="d-grid gap-2">
              <Link to="/lab/orders" className="btn btn-mc-primary"><i className="bi bi-eyedropper me-2" />Process Lab Orders</Link>
              <Link to="/lab/results" className="btn btn-mc-secondary"><i className="bi bi-clipboard2-pulse me-2" />Enter Results</Link>
            </div>
          </div>

          <div className="mc-card">
            <h6 className="fw-semibold mb-3">Status Breakdown</h6>
            {[
              { label: "Pending", count: pending, cls: "bg-secondary" },
              { label: "Sample Collected", count: orders.filter(o => o.status === "SAMPLE_COLLECTED").length, cls: "bg-info text-dark" },
              { label: "In Progress", count: inProgress, cls: "bg-warning text-dark" },
              { label: "Completed", count: completed, cls: "bg-success" },
            ].map(s => (
              <div key={s.label} className="d-flex justify-content-between py-2 border-bottom">
                <span className="text-muted small">{s.label}</span>
                <span className={`badge ${s.cls}`}>{s.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}