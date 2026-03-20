import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { StatCard, LoadingSpinner, EmptyState, PageHeader, useToast, ToastContainer } from "../../components/common/index.jsx";
import { prescriptionApi, medicineApi, inpatientApi } from "../../services/api";

export default function PharmacyDashboard() {
  const [pending, setPending] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [inpatientRequests, setInpatientRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [rxRes, stockRes, ipRes] = await Promise.all([
        prescriptionApi.list({ is_dispensed: false }),
        medicineApi.lowStock(),
        inpatientApi.medicineRequests({ status: "PENDING" }),
      ]);
      setPending(rxRes.data.results || rxRes.data);
      setLowStock(stockRes.data.results || stockRes.data);
      setInpatientRequests(ipRes.data.results || ipRes.data);
    } catch { showToast("Failed to load data", "error"); }
    finally { setLoading(false); }
  }

  if (loading) return <Layout><LoadingSpinner /></Layout>;

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Pharmacy Dashboard" subtitle="Dispense, stock management and inpatient requests" />

      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <StatCard label="Pending Prescriptions" value={pending.length} icon="bi-prescription2" color="orange" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Inpatient Requests" value={inpatientRequests.length} icon="bi-hospital" color="blue" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Low Stock Items" value={lowStock.length} icon="bi-exclamation-triangle" color="red" />
        </div>
        <div className="col-6 col-md-3">
          <StatCard label="Total Medicines" value={"—"} icon="bi-capsule-pill" color="teal" />
        </div>
      </div>

      <div className="row g-3">
        {/* Pending Prescriptions */}
        <div className="col-12 col-xl-6">
          <div className="mc-card h-100">
            <div className="d-flex justify-content-between mb-3">
              <h6 className="fw-semibold mb-0"><i className="bi bi-prescription2 text-warning me-2" />Pending Prescriptions ({pending.length})</h6>
              <Link to="/pharmacy/dispense" className="btn btn-sm btn-mc-primary">Dispense</Link>
            </div>
            {pending.length === 0 ? (
              <EmptyState icon="bi-check2-all" title="No pending prescriptions" />
            ) : pending.slice(0, 6).map(rx => (
              <div key={rx.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                <div>
                  <div className="fw-medium">{rx.medicine?.name || rx.medicine_name}</div>
                  <small className="text-muted">{rx.consultation?.appointment?.patient?.first_name || "Patient"} — {rx.quantity} units</small>
                </div>
                <Link to={`/pharmacy/dispense?rx=${rx.id}`} className="btn btn-sm btn-mc-primary">Dispense</Link>
              </div>
            ))}
          </div>
        </div>

        {/* Low Stock Alert */}
        <div className="col-12 col-xl-6">
          <div className="mc-card mb-3">
            <div className="d-flex justify-content-between mb-3">
              <h6 className="fw-semibold mb-0"><i className="bi bi-exclamation-triangle text-danger me-2" />Low Stock Alert</h6>
              <Link to="/pharmacy/stock" className="btn btn-sm btn-mc-secondary">View Stock</Link>
            </div>
            {lowStock.length === 0 ? (
              <p className="text-muted small">All stock levels are adequate</p>
            ) : lowStock.slice(0, 5).map(m => (
              <div key={m.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                <div>
                  <div className="fw-medium">{m.name}</div>
                  <small className="text-danger">Stock: {m.quantity_in_stock} / Reorder: {m.reorder_level}</small>
                </div>
                <span className="badge bg-danger">Low</span>
              </div>
            ))}
          </div>

          {/* Inpatient Requests */}
          <div className="mc-card">
            <div className="d-flex justify-content-between mb-3">
              <h6 className="fw-semibold mb-0"><i className="bi bi-hospital text-primary me-2" />Inpatient Requests ({inpatientRequests.length})</h6>
              <Link to="/pharmacy/inpatient-requests" className="btn btn-sm btn-mc-primary">View All</Link>
            </div>
            {inpatientRequests.slice(0, 4).map(req => (
              <div key={req.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                <div>
                  <div className="fw-medium">{req.medicine?.name}</div>
                  <small className="text-muted">{req.patient_name} — Ward: {req.ward_name} — Bed: {req.bed_number}</small>
                </div>
                <span className={`badge ${req.priority === "EMERGENCY" ? "bg-danger" : req.priority === "URGENT" ? "bg-warning text-dark" : "bg-secondary"}`}>{req.priority}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}