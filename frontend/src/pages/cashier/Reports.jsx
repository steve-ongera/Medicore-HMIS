import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, useToast, ToastContainer } from "../../components/common/index.jsx";
import { dashboardApi, paymentApi } from "../../services/api";

export default function CashierReports() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({
    from: new Date().toISOString().split("T")[0],
    to: new Date().toISOString().split("T")[0],
  });
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchReport(); }, [dateRange]);

  async function fetchReport() {
    setLoading(true);
    try {
      const [statsRes, paymentsRes] = await Promise.all([
        dashboardApi.revenueChart({ from: dateRange.from, to: dateRange.to }),
        paymentApi.list({ from_date: dateRange.from, to_date: dateRange.to, ordering: "-created_at" }),
      ]);
      setData({ revenue: statsRes.data, payments: paymentsRes.data.results || paymentsRes.data });
    } catch { showToast("Failed to load report data", "error"); }
    finally { setLoading(false); }
  }

  const payments = data?.payments || [];
  const totalBilled = payments.reduce((s, p) => s + parseFloat(p.amount_billed || 0), 0);
  const totalPaid = payments.reduce((s, p) => s + parseFloat(p.amount_paid || 0), 0);
  const totalDiscount = payments.reduce((s, p) => s + parseFloat(p.discount || 0), 0);
  const byMethod = PAYMENT_METHODS.map(m => ({
    method: m, count: payments.filter(p => p.payment_method === m).length,
    total: payments.filter(p => p.payment_method === m).reduce((s, p) => s + parseFloat(p.amount_paid || 0), 0),
  }));
  const byType = PAYMENT_TYPES.map(t => ({
    type: t, count: payments.filter(p => p.payment_type === t).length,
    total: payments.filter(p => p.payment_type === t).reduce((s, p) => s + parseFloat(p.amount_paid || 0), 0),
  })).filter(t => t.count > 0);

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Daily Reports" subtitle="Financial summary and revenue breakdown" />

      {/* Date Range */}
      <div className="mc-card mb-4">
        <div className="row g-3 align-items-end">
          <div className="col-auto">
            <label className="mc-label">From</label>
            <input type="date" className="mc-input" value={dateRange.from} onChange={e => setDateRange(d => ({ ...d, from: e.target.value }))} />
          </div>
          <div className="col-auto">
            <label className="mc-label">To</label>
            <input type="date" className="mc-input" value={dateRange.to} onChange={e => setDateRange(d => ({ ...d, to: e.target.value }))} />
          </div>
          <div className="col-auto">
            <button className="btn btn-mc-secondary" onClick={() => {
              const today = new Date().toISOString().split("T")[0];
              setDateRange({ from: today, to: today });
            }}>Today</button>
          </div>
          <div className="col-auto">
            <button className="btn btn-mc-secondary" onClick={() => {
              const today = new Date();
              const monday = new Date(today);
              monday.setDate(today.getDate() - today.getDay() + 1);
              setDateRange({ from: monday.toISOString().split("T")[0], to: today.toISOString().split("T")[0] });
            }}>This Week</button>
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          {/* Summary Cards */}
          <div className="row g-3 mb-4">
            {[
              { label: "Total Billed", value: `KSh ${totalBilled.toLocaleString()}`, icon: "bi-receipt", color: "blue" },
              { label: "Total Collected", value: `KSh ${totalPaid.toLocaleString()}`, icon: "bi-cash-stack", color: "green" },
              { label: "Total Discounts", value: `KSh ${totalDiscount.toLocaleString()}`, icon: "bi-tag", color: "orange" },
              { label: "Transactions", value: payments.length, icon: "bi-list-check", color: "teal" },
            ].map(s => (
              <div key={s.label} className="col-6 col-md-3">
                <div className="mc-card text-center">
                  <div className={`stat-icon mb-2 mx-auto ${s.color}`} style={{ width: 48, height: 48 }}>
                    <i className={s.icon} />
                  </div>
                  <div className="fw-bold" style={{ fontSize: 18 }}>{s.value}</div>
                  <div className="text-muted small">{s.label}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="row g-3">
            {/* By Payment Method */}
            <div className="col-md-6">
              <div className="mc-card h-100">
                <h6 className="fw-semibold mb-3">By Payment Method</h6>
                {byMethod.map(m => m.count > 0 && (
                  <div key={m.method} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div>
                      <span className="fw-medium">{m.method}</span>
                      <small className="text-muted ms-2">{m.count} transaction(s)</small>
                    </div>
                    <span className="fw-semibold text-success">KSh {m.total.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Payment Type */}
            <div className="col-md-6">
              <div className="mc-card h-100">
                <h6 className="fw-semibold mb-3">By Revenue Category</h6>
                {byType.length === 0 ? <p className="text-muted">No data available</p> : byType.map(t => (
                  <div key={t.type} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                    <div>
                      <span className="fw-medium">{t.type.replace("_", " ")}</span>
                      <small className="text-muted ms-2">{t.count} tx</small>
                    </div>
                    <span className="fw-semibold">KSh {t.total.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}

const PAYMENT_METHODS = ["CASH", "MPESA", "CARD", "INSURANCE", "NHIF", "CHEQUE"];
const PAYMENT_TYPES = ["CONSULTATION", "PHARMACY", "LAB", "IMAGING", "INPATIENT", "EMERGENCY", "PROCEDURE", "OTHER"];