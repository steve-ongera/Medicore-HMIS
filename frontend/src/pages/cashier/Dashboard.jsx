import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { paymentApi, dashboardApi } from "../../services/api";

export default function CashierDashboard() {
  const [stats, setStats] = useState(null);
  const [recentPayments, setRecentPayments] = useState([]);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionLoading, setSessionLoading] = useState(false);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchData(); }, []);

  async function fetchData() {
    try {
      const [statsRes, paymentsRes, sessionRes] = await Promise.all([
        dashboardApi.getStats(),
        paymentApi.list({ ordering: "-created_at", limit: 10 }),
        paymentApi.activeSession(),
      ]);
      setStats(statsRes.data);
      setRecentPayments(paymentsRes.data.results || paymentsRes.data);
      setSession(sessionRes.data);
    } catch {
      showToast("Failed to load data", "error");
    } finally { setLoading(false); }
  }

  async function openSession() {
    setSessionLoading(true);
    try {
      await paymentApi.openSession({ opening_balance: 0 });
      showToast("Session opened", "success");
      fetchData();
    } catch { showToast("Failed to open session", "error"); }
    finally { setSessionLoading(false); }
  }

  async function closeSession() {
    if (!confirm("Close cashier session?")) return;
    setSessionLoading(true);
    try {
      await paymentApi.closeSession(session.id);
      showToast("Session closed", "success");
      fetchData();
    } catch { showToast("Failed to close session", "error"); }
    finally { setSessionLoading(false); }
  }

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  const todayRevenue = stats?.today_revenue || 0;

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Cashier Dashboard" subtitle="Revenue collection and payment tracking" />

      {/* Session Banner */}
      <div className={`mc-alert ${session?.is_active ? "success" : "warning"} mb-4 d-flex align-items-center justify-content-between`}>
        <div>
          {session?.is_active
            ? <><i className="bi bi-check-circle me-2" /><strong>Session Active</strong> — Opened at {new Date(session.opened_at).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" })}</>
            : <><i className="bi bi-exclamation-triangle me-2" />No active session. Open a session to start collecting payments.</>}
        </div>
        {session?.is_active
          ? <button className="btn btn-sm btn-outline-danger" onClick={closeSession} disabled={sessionLoading}>Close Session</button>
          : <button className="btn btn-sm btn-mc-primary" onClick={openSession} disabled={sessionLoading}>Open Session</button>}
      </div>

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <StatCard label="Today's Revenue" value={`KSh ${parseFloat(todayRevenue).toLocaleString()}`} icon="bi-cash-stack" color="green" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Today's Transactions" value={recentPayments.length} icon="bi-receipt" color="blue" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Cash Payments" value={recentPayments.filter(p => p.payment_method === "CASH").length} icon="bi-cash" color="teal" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Insurance Claims" value={recentPayments.filter(p => p.payment_method === "INSURANCE").length} icon="bi-shield-check" color="purple" />
        </div>
      </div>

      <div className="row g-3">
        {/* Recent Transactions */}
        <div className="col-12 col-xl-8">
          <div className="mc-card h-100">
            <div className="d-flex justify-content-between mb-3">
              <h6 className="fw-semibold mb-0">Recent Transactions</h6>
              <Link to="/cashier/payments" className="btn btn-sm btn-mc-secondary">View All</Link>
            </div>
            {recentPayments.length === 0 ? (
              <EmptyState icon="bi-receipt" title="No transactions today" />
            ) : (
              <div>
                {recentPayments.map(tx => (
                  <div key={tx.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div>
                      <div className="fw-medium">{tx.patient_name || tx.invoice_number}</div>
                      <small className="text-muted">{tx.payment_type?.replace("_", " ")} • {tx.payment_method}</small>
                    </div>
                    <div className="text-end">
                      <div className="fw-semibold text-success">KSh {parseFloat(tx.amount_paid || 0).toLocaleString()}</div>
                      <small className="text-muted">{new Date(tx.created_at).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" })}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="col-12 col-xl-4">
          <div className="mc-card">
            <h6 className="fw-semibold mb-3">Quick Actions</h6>
            <div className="d-grid gap-2">
              <Link to="/cashier/payments" className="btn btn-mc-primary">
                <i className="bi bi-cash-coin me-2" />Process Payment
              </Link>
              <Link to="/cashier/reports" className="btn btn-mc-secondary">
                <i className="bi bi-file-bar-graph me-2" />Daily Report
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}