import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, useToast, ToastContainer, DataTable, Tabs } from "../../components/common/index.jsx";
import { inpatientApi } from "../../services/api";

export default function PharmacyInpatientRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pending");
  const [processing, setProcessing] = useState(null);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => {
    fetchRequests();
    const interval = setInterval(fetchRequests, 30000);
    return () => clearInterval(interval);
  }, [tab]);

  async function fetchRequests() {
    setLoading(true);
    try {
      const statusMap = { pending: "PENDING", approved: "APPROVED", dispensed: "DISPENSED" };
      const params = { ordering: "-requested_at" };
      if (statusMap[tab]) params.status = statusMap[tab];
      const res = await inpatientApi.medicineRequests(params);
      setRequests(res.data.results || res.data);
    } catch { showToast("Failed to load requests", "error"); }
    finally { setLoading(false); }
  }

  async function handleAction(requestId, action) {
    setProcessing(requestId);
    try {
      if (action === "approve") await inpatientApi.approveMedicineRequest(requestId);
      else if (action === "dispense") await inpatientApi.dispenseMedicineRequest(requestId);
      else if (action === "reject") await inpatientApi.rejectMedicineRequest(requestId);
      showToast(`Request ${action}d successfully`, "success");
      fetchRequests();
    } catch { showToast(`Failed to ${action} request`, "error"); }
    finally { setProcessing(null); }
  }

  const PRIORITY_BADGE = {
    ROUTINE: "bg-secondary", URGENT: "bg-warning text-dark", EMERGENCY: "bg-danger", STAT: "bg-danger",
  };

  const columns = [
    { key: "medicine", label: "Medicine", render: r => (
      <div>
        <div className="fw-semibold">{r.medicine?.name}</div>
        <small className="text-muted">{r.dosage} — {r.route} — {r.frequency}</small>
      </div>
    )},
    { key: "patient", label: "Patient / Bed", render: r => (
      <div>
        <div className="fw-medium">{r.admission?.patient?.first_name} {r.admission?.patient?.last_name}</div>
        <small className="text-muted">Ward: {r.admission?.bed?.ward?.ward_name} | Bed: {r.admission?.bed?.bed_number}</small>
      </div>
    )},
    { key: "qty", label: "Qty", render: r => `${r.quantity_requested} units` },
    { key: "priority", label: "Priority", render: r => <span className={`badge ${PRIORITY_BADGE[r.priority]}`}>{r.priority}</span> },
    { key: "notes", label: "Clinical Notes", render: r => <small className="text-muted">{r.clinical_notes?.substring(0, 60) || "—"}</small> },
    { key: "time", label: "Requested", render: r => new Date(r.requested_at).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" }) },
    { key: "actions", label: "Action", render: r => {
      const id = r.id;
      const loading = processing === id;
      if (r.status === "PENDING") return (
        <div className="d-flex gap-1">
          <button className="btn btn-sm btn-mc-primary" onClick={() => handleAction(id, "approve")} disabled={loading}>
            {loading ? <span className="spinner-border spinner-border-sm" /> : "Approve"}
          </button>
          <button className="btn btn-sm btn-outline-danger" onClick={() => handleAction(id, "reject")} disabled={loading}>Reject</button>
        </div>
      );
      if (r.status === "APPROVED") return (
        <button className="btn btn-sm btn-mc-primary" onClick={() => handleAction(id, "dispense")} disabled={loading}>
          {loading ? <span className="spinner-border spinner-border-sm" /> : <><i className="bi bi-bag-check me-1" />Dispense</>}
        </button>
      );
      if (r.status === "DISPENSED") return <span className="badge bg-success"><i className="bi bi-check2 me-1" />Dispensed</span>;
      if (r.status === "REJECTED") return <span className="badge bg-danger">Rejected</span>;
      return null;
    }},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Inpatient Medicine Requests" subtitle="Approve and dispense ward medicine requests" />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[{ key: "pending", label: `Pending (${tab === "pending" ? requests.length : "?"})` }, { key: "approved", label: "Approved" }, { key: "dispensed", label: "Dispensed" }, { key: "all", label: "All" }]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : requests.length === 0 ? (
        <EmptyState icon="bi-hospital" title={tab === "pending" ? "No pending requests" : "No records found"} />
      ) : <DataTable columns={columns} data={requests} />}
    </Layout>
  );
}