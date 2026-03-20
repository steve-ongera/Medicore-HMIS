import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, FormRow, Tabs } from "../../components/common/index.jsx";
import { labApi } from "../../services/api";

const STATUS_FLOW = {
  PENDING: { next: "SAMPLE_COLLECTED", label: "Collect Sample", cls: "btn-mc-primary" },
  SAMPLE_COLLECTED: { next: "IN_PROGRESS", label: "Start Processing", cls: "btn-mc-primary" },
  IN_PROGRESS: { next: "COMPLETED", label: "Complete", cls: "btn-mc-success" },
};

const STATUS_BADGE = {
  PENDING: "bg-secondary", SAMPLE_COLLECTED: "bg-info text-dark",
  IN_PROGRESS: "bg-warning text-dark", COMPLETED: "bg-success",
  REPORTED: "bg-primary", CANCELLED: "bg-danger",
};

export default function LabOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("active");
  const [selected, setSelected] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [processing, setProcessing] = useState(null);
  const { toasts, showToast, removeToast } = useToast();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchOrders();
    const oid = searchParams.get("order");
    if (oid) loadOrder(oid);
  }, [tab]);

  async function fetchOrders() {
    setLoading(true);
    try {
      const params = { ordering: "-ordered_at" };
      if (tab === "active") params.status = "PENDING,SAMPLE_COLLECTED,IN_PROGRESS";
      else if (tab === "completed") params.status = "COMPLETED,REPORTED";
      const res = await labApi.orders(params);
      setOrders(res.data.results || res.data);
    } catch { showToast("Failed to load orders", "error"); }
    finally { setLoading(false); }
  }

  async function loadOrder(id) {
    try {
      const res = await labApi.getOrder(id);
      setSelected(res.data);
      setShowDetail(true);
    } catch {}
  }

  async function updateStatus(orderId, status) {
    setProcessing(orderId);
    try {
      await labApi.updateOrderStatus(orderId, { status });
      showToast("Status updated", "success");
      fetchOrders();
    } catch { showToast("Failed to update status", "error"); }
    finally { setProcessing(null); }
  }

  const columns = [
    { key: "order_number", label: "Order #", render: o => <code className="text-primary">{o.order_number}</code> },
    { key: "patient", label: "Patient", render: o => (
      <div><div className="fw-medium">{o.patient?.first_name} {o.patient?.last_name}</div>
        <small className="text-muted">{new Date(o.ordered_at).toLocaleString("en-KE", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</small>
      </div>
    )},
    { key: "tests", label: "Tests", render: o => <small>{o.test_items?.map(t => t.test?.test_name).join(", ") || `${o.test_items?.length} test(s)`}</small> },
    { key: "priority", label: "Priority", render: o => (
      <span className={`badge ${o.priority === "STAT" || o.priority === "EMERGENCY" ? "bg-danger" : o.priority === "URGENT" ? "bg-warning text-dark" : "bg-secondary"}`}>{o.priority}</span>
    )},
    { key: "status", label: "Status", render: o => <span className={`badge ${STATUS_BADGE[o.status]}`}>{o.status?.replace("_", " ")}</span> },
    { key: "actions", label: "Action", render: o => {
      const flow = STATUS_FLOW[o.status];
      return (
        <div className="d-flex gap-1">
          <button className="btn btn-icon" onClick={() => { setSelected(o); setShowDetail(true); }}><i className="bi bi-eye" /></button>
          {flow && (
            <button className={`btn btn-sm ${flow.cls}`} onClick={() => updateStatus(o.id, flow.next)} disabled={processing === o.id}>
              {processing === o.id ? <span className="spinner-border spinner-border-sm" /> : flow.label}
            </button>
          )}
        </div>
      );
    }},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Lab Orders" subtitle="Process and track laboratory test orders" />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[{ key: "active", label: `Active (${tab === "active" ? orders.length : "?"})` }, { key: "completed", label: "Completed" }, { key: "all", label: "All" }]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : orders.length === 0 ? (
        <EmptyState icon="bi-eyedropper" title="No lab orders found" />
      ) : <DataTable columns={columns} data={orders} />}

      {/* Order Detail */}
      <Modal
        show={showDetail && !!selected}
        onClose={() => { setShowDetail(false); setSelected(null); }}
        title={`Lab Order — ${selected?.order_number}`}
        size="lg"
      >
        {selected && (
          <div>
            <div className="mc-alert info mb-3">
              <strong>Patient:</strong> {selected.patient?.first_name} {selected.patient?.last_name} &nbsp;|&nbsp;
              <strong>Status:</strong> {selected.status?.replace("_", " ")} &nbsp;|&nbsp;
              <strong>Priority:</strong> {selected.priority}
            </div>
            <h6 className="fw-semibold mb-2">Ordered Tests</h6>
            {(selected.test_items || []).map(item => (
              <div key={item.id} className="d-flex justify-content-between py-2 border-bottom">
                <div>
                  <div className="fw-medium">{item.test?.test_name}</div>
                  <small className="text-muted">{item.test?.test_code} — {item.test?.sample_type}</small>
                </div>
                <div className="text-end">
                  <div>KSh {item.test?.cost}</div>
                  <span className={`badge ${item.status === "COMPLETED" ? "bg-success" : "bg-secondary"}`}>{item.status}</span>
                </div>
              </div>
            ))}
            {selected.clinical_notes && (
              <div className="mt-3">
                <h6 className="fw-semibold mb-1">Clinical Notes</h6>
                <p className="text-muted">{selected.clinical_notes}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </Layout>
  );
}