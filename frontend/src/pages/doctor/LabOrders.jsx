import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, DataTable, useToast, ToastContainer, Tabs } from "../../components/common/index.jsx";
import { labApi } from "../../services/api";

export default function DoctorLabOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pending");
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchOrders(); }, [tab]);

  async function fetchOrders() {
    setLoading(true);
    try {
      const params = tab === "pending" ? { status: "PENDING,SAMPLE_COLLECTED,IN_PROGRESS" } : tab === "ready" ? { status: "REPORTED,COMPLETED" } : {};
      const res = await labApi.orders({ ...params, ordering: "-ordered_at" });
      setOrders(res.data.results || res.data);
    } catch { showToast("Failed to load lab orders", "error"); }
    finally { setLoading(false); }
  }

  const STATUS_BADGE = {
    PENDING: "bg-secondary", SAMPLE_COLLECTED: "bg-info text-dark",
    IN_PROGRESS: "bg-warning text-dark", COMPLETED: "bg-primary",
    REPORTED: "bg-success", CANCELLED: "bg-danger",
  };

  const PRIORITY_BADGE = {
    ROUTINE: "bg-secondary", URGENT: "bg-warning text-dark",
    EMERGENCY: "bg-danger", STAT: "bg-danger",
  };

  const columns = [
    { key: "order_number", label: "Order #", render: o => <code className="text-primary">{o.order_number}</code> },
    { key: "patient", label: "Patient", render: o => <div><div className="fw-medium">{o.patient?.first_name} {o.patient?.last_name}</div><small className="text-muted">{new Date(o.ordered_at).toLocaleDateString("en-KE")}</small></div> },
    { key: "tests", label: "Tests", render: o => <span>{o.test_items?.length || 0} test(s)</span> },
    { key: "priority", label: "Priority", render: o => <span className={`badge ${PRIORITY_BADGE[o.priority]}`}>{o.priority}</span> },
    { key: "status", label: "Status", render: o => <span className={`badge ${STATUS_BADGE[o.status]}`}>{o.status?.replace("_", " ")}</span> },
    { key: "result", label: "Results", render: o => o.result ? (
      <div className="small">
        <div className="fw-medium">{o.result.summary?.substring(0, 60)}</div>
        {o.result.is_critical && <span className="badge bg-danger">Critical</span>}
      </div>
    ) : <span className="text-muted">—</span> },
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Lab Orders" subtitle="Track laboratory test orders and results" />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[
            { key: "pending", label: "In Progress" },
            { key: "ready", label: "Results Ready" },
            { key: "all", label: "All Orders" },
          ]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : orders.length === 0 ? (
        <EmptyState icon="bi-eyedropper" title="No lab orders found" subtitle="" />
      ) : <DataTable columns={columns} data={orders} />}
    </Layout>
  );
}