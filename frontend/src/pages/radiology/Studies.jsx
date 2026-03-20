import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, Modal, useToast, ToastContainer, DataTable, FormRow, Tabs } from "../../components/common/index.jsx";
import { imagingApi } from "../../services/api";

const STATUS_FLOW = {
  PENDING: { next: "IN_PROGRESS", label: "Start Study", cls: "btn-mc-primary" },
  IN_PROGRESS: { next: "COMPLETED", label: "Mark Done", cls: "btn-mc-success" },
};

const MODALITY_ICONS = { XRAY: "bi-x-ray", CT: "bi-layers", MRI: "bi-magnet", ULTRASOUND: "bi-soundwave" };
const STATUS_BADGE = { PENDING: "bg-secondary", IN_PROGRESS: "bg-warning text-dark", COMPLETED: "bg-primary", REPORTED: "bg-success", CANCELLED: "bg-danger" };

export default function RadiologyStudies() {
  const [studies, setStudies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("active");
  const [selected, setSelected] = useState(null);
  const [showReport, setShowReport] = useState(false);
  const [reportForm, setReportForm] = useState({ findings: "", impression: "", recommendations: "", is_normal: false });
  const [processing, setProcessing] = useState(null);
  const [saving, setSaving] = useState(false);
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchStudies(); }, [tab]);

  async function fetchStudies() {
    setLoading(true);
    try {
      const params = { ordering: "-created_at" };
      if (tab === "active") params.status = "PENDING,IN_PROGRESS,COMPLETED";
      else if (tab === "reported") params.status = "REPORTED";
      const res = await imagingApi.list(params);
      setStudies(res.data.results || res.data);
    } catch { showToast("Failed to load studies", "error"); }
    finally { setLoading(false); }
  }

  async function updateStatus(studyId, status) {
    setProcessing(studyId);
    try {
      await imagingApi.updateStatus(studyId, { status });
      showToast("Status updated", "success");
      fetchStudies();
    } catch { showToast("Failed to update status", "error"); }
    finally { setProcessing(null); }
  }

  async function submitReport() {
    if (!reportForm.findings || !reportForm.impression) {
      showToast("Findings and impression are required", "error"); return;
    }
    setSaving(true);
    try {
      await imagingApi.submitReport(selected.id, reportForm);
      await imagingApi.updateStatus(selected.id, { status: "REPORTED" });
      showToast("Radiology report submitted", "success");
      setShowReport(false);
      setSelected(null);
      setReportForm({ findings: "", impression: "", recommendations: "", is_normal: false });
      fetchStudies();
    } catch { showToast("Failed to submit report", "error"); }
    finally { setSaving(false); }
  }

  const columns = [
    { key: "modality", label: "Study", render: s => (
      <div className="d-flex align-items-center gap-2">
        <i className={`bi ${MODALITY_ICONS[s.modality] || "bi-image"} text-primary`} style={{ fontSize: 20 }} />
        <div><div className="fw-medium">{s.modality} — {s.body_part}</div><small className="text-muted">{s.study_description?.substring(0, 40)}</small></div>
      </div>
    )},
    { key: "patient", label: "Patient", render: s => <div><div className="fw-medium">{s.patient?.first_name} {s.patient?.last_name}</div><small className="text-muted">{new Date(s.created_at).toLocaleDateString("en-KE")}</small></div> },
    { key: "priority", label: "Priority", render: s => s.is_urgent ? <span className="badge bg-danger">Urgent</span> : <span className="badge bg-secondary">Routine</span> },
    { key: "status", label: "Status", render: s => <span className={`badge ${STATUS_BADGE[s.status]}`}>{s.status}</span> },
    { key: "actions", label: "Action", render: s => {
      const flow = STATUS_FLOW[s.status];
      return (
        <div className="d-flex gap-1">
          {flow && (
            <button className={`btn btn-sm ${flow.cls}`} onClick={() => updateStatus(s.id, flow.next)} disabled={processing === s.id}>
              {processing === s.id ? <span className="spinner-border spinner-border-sm" /> : flow.label}
            </button>
          )}
          {s.status === "COMPLETED" && (
            <button className="btn btn-sm btn-mc-primary" onClick={() => { setSelected(s); setShowReport(true); }}>
              <i className="bi bi-file-medical me-1" />Report
            </button>
          )}
          {s.status === "REPORTED" && <span className="badge bg-success">Reported</span>}
        </div>
      );
    }},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Imaging Studies" subtitle="Process radiology studies and submit reports" />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[{ key: "active", label: `Active (${tab === "active" ? studies.length : "?"})` }, { key: "reported", label: "Reported" }, { key: "all", label: "All" }]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {loading ? <LoadingSpinner /> : studies.length === 0 ? (
        <EmptyState icon="bi-x-ray" title="No imaging studies found" />
      ) : <DataTable columns={columns} data={studies} />}

      {/* Report Modal */}
      <Modal
        show={showReport && !!selected}
        onClose={() => { setShowReport(false); setSelected(null); }}
        title={`Radiology Report — ${selected?.modality} ${selected?.body_part}`}
        size="lg"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowReport(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={submitReport} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-send me-2" />}
              Submit Report
            </button>
          </>
        }
      >
        {selected && (
          <div className="row g-3">
            <div className="col-12">
              <div className="mc-alert info">
                <strong>Patient:</strong> {selected.patient?.first_name} {selected.patient?.last_name} &nbsp;|&nbsp;
                <strong>Study:</strong> {selected.study_description} &nbsp;|&nbsp;
                <strong>Indication:</strong> {selected.clinical_indication}
              </div>
            </div>

            <div className="col-12">
              <div className="form-check mb-3">
                <input type="checkbox" className="form-check-input" id="normal" checked={reportForm.is_normal} onChange={e => setReportForm(f => ({ ...f, is_normal: e.target.checked }))} />
                <label className="form-check-label fw-medium text-success" htmlFor="normal">
                  <i className="bi bi-check-circle me-2" />Normal Study — No significant abnormality detected
                </label>
              </div>
            </div>

            <FormRow label="Findings *" colClass="col-12">
              <textarea className="mc-input" rows={5} value={reportForm.findings} onChange={e => setReportForm(f => ({ ...f, findings: e.target.value }))} placeholder="Detailed radiological findings..." />
            </FormRow>

            <FormRow label="Impression *" colClass="col-12">
              <textarea className="mc-input" rows={3} value={reportForm.impression} onChange={e => setReportForm(f => ({ ...f, impression: e.target.value }))} placeholder="Clinical impression and diagnosis..." />
            </FormRow>

            <FormRow label="Recommendations" colClass="col-12">
              <textarea className="mc-input" rows={2} value={reportForm.recommendations} onChange={e => setReportForm(f => ({ ...f, recommendations: e.target.value }))} placeholder="Further investigations or follow-up recommended..." />
            </FormRow>
          </div>
        )}
      </Modal>
    </Layout>
  );
}