import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, FormRow, Tabs, SearchInput } from "../../components/common/index.jsx";
import { paymentApi, visitApi, patientApi } from "../../services/api";

const PAYMENT_METHODS = [
  { value: "CASH", label: "Cash" },
  { value: "MPESA", label: "M-Pesa" },
  { value: "CARD", label: "Card / Bank" },
  { value: "INSURANCE", label: "Insurance" },
  { value: "NHIF", label: "NHIF/SHA" },
  { value: "CHEQUE", label: "Cheque" },
];

const PAYMENT_TYPES = [
  { value: "CONSULTATION", label: "Consultation Fee" },
  { value: "PHARMACY", label: "Pharmacy / Medicines" },
  { value: "LAB", label: "Laboratory Tests" },
  { value: "IMAGING", label: "Radiology / Imaging" },
  { value: "INPATIENT", label: "Inpatient Charges" },
  { value: "EMERGENCY", label: "Emergency" },
  { value: "PROCEDURE", label: "Procedure" },
  { value: "OTHER", label: "Other" },
];

const EMPTY_FORM = {
  visit: "", payment_type: "CONSULTATION", amount_billed: "",
  amount_paid: "", payment_method: "CASH", mpesa_reference: "",
  insurance_reference: "", discount: "0", notes: "",
};

export default function CashierPayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState("today");
  const [search, setSearch] = useState("");
  const [visitSearch, setVisitSearch] = useState("");
  const [visitResults, setVisitResults] = useState([]);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchPayments(); }, [tab]);

  async function fetchPayments() {
    setLoading(true);
    try {
      const params = { ordering: "-created_at" };
      if (tab === "today") params.today = true;
      const res = await paymentApi.list(params);
      setPayments(res.data.results || res.data);
    } catch { showToast("Failed to load payments", "error"); }
    finally { setLoading(false); }
  }

  async function searchVisits(q) {
    if (!q || q.length < 2) { setVisitResults([]); return; }
    try {
      const res = await visitApi.list({ search: q, status: "COMPLETED,IN_CONSULTATION,WAITING", ordering: "-arrival_time" });
      setVisitResults(res.data.results || res.data);
    } catch {}
  }

  async function processPayment() {
    if (!form.visit || !form.amount_paid || !form.payment_type) {
      showToast("Visit, payment type and amount are required", "error"); return;
    }
    setSaving(true);
    try {
      await paymentApi.create(form);
      showToast("Payment processed successfully", "success");
      setShowModal(false);
      setForm(EMPTY_FORM);
      setVisitSearch("");
      fetchPayments();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to process payment", "error");
    } finally { setSaving(false); }
  }

  const balance = parseFloat(form.amount_billed || 0) - parseFloat(form.discount || 0) - parseFloat(form.amount_paid || 0);

  const STATUS_MAP = {
    PAID: "bg-success", PARTIAL: "bg-warning text-dark", PENDING: "bg-secondary", WAIVED: "bg-info text-dark",
  };

  const columns = [
    { key: "invoice", label: "Invoice #", render: p => <code className="text-primary">{p.invoice_number || p.id}</code> },
    { key: "patient", label: "Patient", render: p => p.patient_name || "—" },
    { key: "type", label: "Type", render: p => p.payment_type?.replace("_", " ") },
    { key: "method", label: "Method", render: p => (
      <div className="d-flex align-items-center gap-1">
        {p.payment_method === "MPESA" && <i className="bi bi-phone text-success" />}
        {p.payment_method === "INSURANCE" && <i className="bi bi-shield-check text-primary" />}
        {p.payment_method === "CASH" && <i className="bi bi-cash text-success" />}
        <small>{p.payment_method}</small>
      </div>
    )},
    { key: "billed", label: "Billed", render: p => `KSh ${parseFloat(p.amount_billed || 0).toLocaleString()}` },
    { key: "paid", label: "Paid", render: p => <span className="fw-semibold text-success">KSh {parseFloat(p.amount_paid || 0).toLocaleString()}</span> },
    { key: "status", label: "Status", render: p => <span className={`badge ${STATUS_MAP[p.payment_status] || "bg-secondary"}`}>{p.payment_status}</span> },
    { key: "time", label: "Time", render: p => new Date(p.created_at).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" }) },
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="Payments"
        subtitle="Process and track patient payments"
        actions={
          <button className="btn btn-mc-primary" onClick={() => setShowModal(true)}>
            <i className="bi bi-plus-circle me-2" />Process Payment
          </button>
        }
      />

      <div className="mc-card mb-3">
        <div className="d-flex flex-wrap gap-3 align-items-center">
          <Tabs
            tabs={[{ key: "today", label: "Today" }, { key: "all", label: "All Payments" }]}
            active={tab}
            onChange={setTab}
          />
          <div className="ms-auto" style={{ minWidth: 240 }}>
            <SearchInput value={search} onChange={setSearch} placeholder="Search payments..." />
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : payments.length === 0 ? (
        <EmptyState icon="bi-receipt" title="No payments found" />
      ) : (
        <DataTable columns={columns} data={payments.filter(p => {
          if (!search) return true;
          return (p.patient_name || "").toLowerCase().includes(search.toLowerCase()) || (p.invoice_number || "").toLowerCase().includes(search.toLowerCase());
        })} />
      )}

      {/* Process Payment Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setForm(EMPTY_FORM); setVisitSearch(""); }}
        title="Process Payment"
        size="lg"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={processPayment} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-cash-coin me-2" />}
              Process Payment
            </button>
          </>
        }
      >
        <div className="row g-3">
          {/* Visit Search */}
          <FormRow label="Search Visit / Patient *" colClass="col-12">
            <input
              className="mc-input mb-2"
              placeholder="Search by patient name or visit number..."
              value={visitSearch}
              onChange={e => { setVisitSearch(e.target.value); searchVisits(e.target.value); }}
            />
            {visitResults.length > 0 && (
              <div className="border rounded" style={{ maxHeight: 160, overflowY: "auto" }}>
                {visitResults.map(v => (
                  <div key={v.id} className="px-3 py-2 d-flex justify-content-between" style={{ cursor: "pointer" }}
                    onClick={() => { setForm(f => ({ ...f, visit: v.id })); setVisitSearch(`${v.visit_number} — ${v.patient_name || "Patient"}`); setVisitResults([]); }}>
                    <div><strong>{v.visit_number}</strong> — {v.patient_name}</div>
                    <small className="text-muted">{v.visit_type}</small>
                  </div>
                ))}
              </div>
            )}
            {form.visit && <small className="text-success"><i className="bi bi-check-circle me-1" />Visit selected</small>}
          </FormRow>

          <FormRow label="Payment Type *" colClass="col-md-6">
            <select className="mc-select" value={form.payment_type} onChange={e => setForm(f => ({ ...f, payment_type: e.target.value }))}>
              {PAYMENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </FormRow>

          <FormRow label="Payment Method *" colClass="col-md-6">
            <select className="mc-select" value={form.payment_method} onChange={e => setForm(f => ({ ...f, payment_method: e.target.value }))}>
              {PAYMENT_METHODS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </FormRow>

          <FormRow label="Amount Billed (KSh)" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.amount_billed} onChange={e => setForm(f => ({ ...f, amount_billed: e.target.value }))} placeholder="0.00" />
          </FormRow>

          <FormRow label="Discount (KSh)" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.discount} onChange={e => setForm(f => ({ ...f, discount: e.target.value }))} />
          </FormRow>

          <FormRow label="Amount Paid (KSh) *" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.amount_paid} onChange={e => setForm(f => ({ ...f, amount_paid: e.target.value }))} placeholder="0.00" />
          </FormRow>

          {(form.payment_method === "MPESA") && (
            <FormRow label="M-Pesa Reference" colClass="col-md-6">
              <input className="mc-input" value={form.mpesa_reference} onChange={e => setForm(f => ({ ...f, mpesa_reference: e.target.value }))} placeholder="e.g. QDE4XXXYYY" />
            </FormRow>
          )}

          {(form.payment_method === "INSURANCE" || form.payment_method === "NHIF") && (
            <FormRow label="Insurance Reference / Auth Code" colClass="col-md-6">
              <input className="mc-input" value={form.insurance_reference} onChange={e => setForm(f => ({ ...f, insurance_reference: e.target.value }))} />
            </FormRow>
          )}

          {/* Balance */}
          {(form.amount_billed || form.amount_paid) && (
            <div className="col-12">
              <div className={`mc-alert ${balance > 0 ? "warning" : balance < 0 ? "danger" : "success"}`}>
                <div className="d-flex justify-content-between">
                  <span>{balance > 0 ? "Balance Due" : balance < 0 ? "Change to Give" : "Fully Paid"}</span>
                  <span className="fw-bold">KSh {Math.abs(balance).toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}

          <FormRow label="Notes" colClass="col-12">
            <textarea className="mc-input" rows={2} value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Optional notes..." />
          </FormRow>
        </div>
      </Modal>
    </Layout>
  );
}