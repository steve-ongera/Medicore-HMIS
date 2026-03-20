import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, DataTable, useToast, ToastContainer, Tabs } from "../../components/common/index.jsx";
import { imagingApi } from "../../services/api";

export default function DoctorImaging() {
  const [studies, setStudies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pending");
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchStudies(); }, [tab]);

  async function fetchStudies() {
    setLoading(true);
    try {
      const params = tab === "pending"
        ? { status: "PENDING,IN_PROGRESS" }
        : tab === "reported" ? { status: "REPORTED,COMPLETED" } : {};
      const res = await imagingApi.list({ ...params, ordering: "-ordered_at" });
      setStudies(res.data.results || res.data);
    } catch { showToast("Failed to load imaging studies", "error"); }
    finally { setLoading(false); }
  }

  const MODALITY_ICONS = { XRAY: "bi-x-ray", CT: "bi-layers", MRI: "bi-magnet", ULTRASOUND: "bi-soundwave", OTHER: "bi-image" };
  const STATUS_BADGE = { PENDING: "bg-secondary", IN_PROGRESS: "bg-warning text-dark", COMPLETED: "bg-primary", REPORTED: "bg-success", CANCELLED: "bg-danger" };

  const columns = [
    { key: "modality", label: "Modality", render: s => (
      <div className="d-flex align-items-center gap-2">
        <i className={`bi ${MODALITY_ICONS[s.modality] || "bi-image"} text-primary`} style={{ fontSize: 20 }} />
        <div><div className="fw-medium">{s.get_modality_display || s.modality}</div><small className="text-muted">{s.body_part}</small></div>
      </div>
    )},
    { key: "patient", label: "Patient", render: s => <div><div className="fw-medium">{s.patient?.first_name} {s.patient?.last_name}</div><small className="text-muted">{new Date(s.ordered_at || s.created_at).toLocaleDateString("en-KE")}</small></div> },
    { key: "description", label: "Study", render: s => <small className="text-muted">{s.study_description}</small> },
    { key: "urgent", label: "Priority", render: s => s.is_urgent ? <span className="badge bg-danger">Urgent</span> : <span className="badge bg-secondary">Routine</span> },
    { key: "status", label: "Status", render: s => <span className={`badge ${STATUS_BADGE[s.status]}`}>{s.status}</span> },
    { key: "results", label: "Findings", render: s => s.findings ? (
      <small className="text-muted">{s.findings.substring(0, 60)}{s.findings.length > 60 ? "..." : ""}</small>
    ) : <span className="text-muted">Pending</span> },
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Imaging Studies" subtitle="View and track imaging/radiology requests" />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[{ key: "pending", label: "Pending" }, { key: "reported", label: "Reported" }, { key: "all", label: "All" }]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : studies.length === 0 ? (
        <EmptyState icon="bi-x-ray" title="No imaging studies found" subtitle="" />
      ) : <DataTable columns={columns} data={studies} />}
    </Layout>
  );
}