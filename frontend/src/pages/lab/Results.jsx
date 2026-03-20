import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, FormRow, Tabs } from "../../components/common/index.jsx";
import { labApi } from "../../services/api";

export default function LabResults() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [tab, setTab] = useState("pending_results");
  const [resultForm, setResultForm] = useState({
    summary: "", findings: "", reference_ranges: "", methodology: "",
    is_critical: false, critical_notes: "", status: "REPORTED",
  });
  const [saving, setSaving] = useState(false);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchOrders(); }, [tab]);

  async function fetchOrders() {
    setLoading(true);
    try {
      const params = { ordering: "-ordered_at" };
      if (tab === "pending_results") params.status = "IN_PROGRESS,COMPLETED";
      else if (tab === "reported") params.status = "REPORTED";
      const res = await labApi.orders(params);
      setOrders(res.data.results || res.data);
    } catch { showToast("Failed to load orders", "error"); }
    finally { setLoading(false); }
  }

  async function submitResult() {
    if (!resultForm.summary || !resultForm.findings) {
      showToast("Summary and findings are required", "error"); return;
    }
    setSaving(true);
    try {
      await labApi.createResult({ ...resultForm, order: selected.id });
      await labApi.updateOrderStatus(selected.id, { status: "REPORTED" });
      showToast("Results submitted and report generated", "success");
      setShowModal(false);
      setSelected(null);
      setResultForm({ summary: "", findings: "", reference_ranges: "", methodology: "", is_critical: false, critical_notes: "", status: "REPORTED" });
      fetchOrders();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to submit results", "error");
    } finally { setSaving(false); }
  }

  const STATUS_BADGE = { IN_PROGRESS: "bg-warning text-dark", COMPLETED: "bg-primary", REPORTED: "bg-success" };

  const columns = [
    { key: "order_number", label: "Order #", render: o => <code className="text-primary">{o.order_number}</code> },
    { key: "patient", label: "Patient", render: o => <div><div className="fw-medium">{o.patient?.first_name} {o.patient?.last_name}</div><small className="text-muted">{new Date(o.ordered_at).toLocaleDateString("en-KE")}</small></div> },
    { key: "tests", label: "Tests", render: o => <small>{o.test_items?.length || 0} test(s)</small> },
    { key: "priority", label: "Priority", render: o => <span className={`badge ${o.priority === "URGENT" || o.priority === "STAT" ? "bg-danger" : "bg-secondary"}`}>{o.priority}</span> },
    { key: "status", label: "Status", render: o => <span className={`badge ${STATUS_BADGE[o.status] || "bg-secondary"}`}>{o.status?.replace("_", " ")}</span> },
    { key: "actions", label: "", render: o => o.status !== "REPORTED" ? (
      <button className="btn btn-sm btn-mc-primary" onClick={() => { setSelected(o); setShowModal(true); }}>
        <i className="bi bi-clipboard2-pulse me-1" />Enter Results
      </button>
    ) : <span className="text-muted small">Results submitted</span> },
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Lab Results" subtitle="Enter and report test results" />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[{ key: "pending_results", label: "Awaiting Results" }, { key: "reported", label: "Reported" }]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : orders.length === 0 ? (
        <EmptyState icon="bi-clipboard2-pulse" title="No orders awaiting results" />
      ) : <DataTable columns={columns} data={orders} />}

      {/* Enter Results Modal */}
      <Modal
        show={showModal && !!selected}
        onClose={() => { setShowModal(false); setSelected(null); }}
        title={`Enter Results — ${selected?.order_number}`}
        size="lg"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={submitResult} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-send me-2" />}
              Submit Results
            </button>
          </>
        }
      >
        {selected && (
          <div className="row g-3">
            <div className="col-12">
              <div className="mc-alert info">
                <strong>Patient:</strong> {selected.patient?.first_name} {selected.patient?.last_name} &nbsp;|&nbsp;
                Tests: {selected.test_items?.map(t => t.test?.test_name).join(", ")}
              </div>
            </div>

            <FormRow label="Result Summary *" colClass="col-12">
              <textarea className="mc-input" rows={3} value={resultForm.summary} onChange={e => setResultForm(f => ({ ...f, summary: e.target.value }))} placeholder="Brief summary of results..." />
            </FormRow>

            <FormRow label="Detailed Findings *" colClass="col-12">
              <textarea className="mc-input" rows={5} value={resultForm.findings} onChange={e => setResultForm(f => ({ ...f, findings: e.target.value }))} placeholder="Detailed findings and values with units...&#10;e.g. Hb: 12.5 g/dL (Normal: 11.5-16.5)&#10;WBC: 7.2 x10³/µL (Normal: 4.0-11.0)" />
            </FormRow>

            <FormRow label="Reference Ranges" colClass="col-md-6">
              <textarea className="mc-input" rows={3} value={resultForm.reference_ranges} onChange={e => setResultForm(f => ({ ...f, reference_ranges: e.target.value }))} placeholder="Reference ranges used..." />
            </FormRow>

            <FormRow label="Methodology" colClass="col-md-6">
              <textarea className="mc-input" rows={3} value={resultForm.methodology} onChange={e => setResultForm(f => ({ ...f, methodology: e.target.value }))} placeholder="Testing methodology used..." />
            </FormRow>

            <div className="col-12">
              <div className="form-check mb-2">
                <input type="checkbox" className="form-check-input" id="critical" checked={resultForm.is_critical} onChange={e => setResultForm(f => ({ ...f, is_critical: e.target.checked }))} />
                <label className="form-check-label text-danger fw-medium" htmlFor="critical">
                  <i className="bi bi-exclamation-octagon me-2" />Mark as Critical — Requires Immediate Physician Attention
                </label>
              </div>
              {resultForm.is_critical && (
                <textarea className="mc-input" rows={2} value={resultForm.critical_notes} onChange={e => setResultForm(f => ({ ...f, critical_notes: e.target.value }))} placeholder="Critical notes and immediate actions required..." />
              )}
            </div>
          </div>
        )}
      </Modal>
    </Layout>
  );
}