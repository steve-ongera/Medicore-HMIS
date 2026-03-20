import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import {
  PageHeader, LoadingSpinner, EmptyState, Modal, useToast,
  ToastContainer, DataTable, FormRow, Tabs, SectionCard, VitalBox, TriageBadge
} from "../../components/common/index.jsx";
import { visitApi, consultationApi, prescriptionApi, medicineApi, labApi, imagingApi } from "../../services/api";

const EMPTY_CONSULTATION = {
  diagnosis: "", notes: "", follow_up_date: "", follow_up_notes: "",
};

const EMPTY_RX = {
  medicine: "", quantity: "", dosage_text: "", duration: "", instructions: "", is_insured: false, insurance_provider: "",
};

const EMPTY_LAB = {
  test: "", priority: "ROUTINE", clinical_notes: "", special_instructions: "",
};

export default function DoctorConsultation() {
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [activeSection, setActiveSection] = useState("consultation");
  const [consultForm, setConsultForm] = useState(EMPTY_CONSULTATION);
  const [prescriptions, setPrescriptions] = useState([]);
  const [rxForm, setRxForm] = useState(EMPTY_RX);
  const [labForm, setLabForm] = useState(EMPTY_LAB);
  const [medicines, setMedicines] = useState([]);
  const [labTests, setLabTests] = useState([]);
  const [saving, setSaving] = useState(false);
  const [existingConsultation, setExistingConsultation] = useState(null);
  const { toasts, showToast, removeToast } = useToast();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchWaiting();
    fetchMedicines();
    fetchLabTests();
    const vid = searchParams.get("visit");
    if (vid) loadVisit(vid);
  }, []);

  async function fetchWaiting() {
    setLoading(true);
    try {
      const res = await visitApi.list({ status: "WAITING,IN_CONSULTATION", ordering: "arrival_time" });
      setVisits(res.data.results || res.data);
    } catch { showToast("Failed to load queue", "error"); }
    finally { setLoading(false); }
  }

  async function fetchMedicines() {
    try {
      const res = await medicineApi.list({ limit: 200 });
      setMedicines(res.data.results || res.data);
    } catch {}
  }

  async function fetchLabTests() {
    try {
      const res = await labApi.tests({ limit: 200 });
      setLabTests(res.data.results || res.data);
    } catch {}
  }

  async function loadVisit(visitId) {
    try {
      const res = await visitApi.get(visitId);
      selectVisit(res.data);
    } catch {}
  }

  async function selectVisit(visit) {
    setSelectedVisit(visit);
    await visitApi.updateStatus(visit.id, { status: "IN_CONSULTATION" });
    // Try load existing consultation
    try {
      const res = await consultationApi.list({ patient: visit.patient?.id });
      const existing = (res.data.results || res.data).find(c => c.appointment?.patient === visit.patient?.id);
      if (existing) setExistingConsultation(existing);
    } catch {}
    fetchWaiting();
  }

  async function saveConsultation() {
    if (!consultForm.diagnosis) { showToast("Diagnosis is required", "error"); return; }
    setSaving(true);
    try {
      // Create appointment link first if needed
      let apptId;
      if (selectedVisit.appointment) apptId = selectedVisit.appointment;
      // Create consultation
      const res = await consultationApi.create({ appointment: apptId, visit: selectedVisit.id, ...consultForm });
      setExistingConsultation(res.data);
      await visitApi.updateStatus(selectedVisit.id, { status: "COMPLETED" });
      showToast("Consultation saved successfully", "success");
      setActiveSection("prescriptions");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to save consultation", "error");
    } finally { setSaving(false); }
  }

  async function addPrescription() {
    if (!rxForm.medicine || !rxForm.quantity || !rxForm.dosage_text) { showToast("Medicine, quantity and dosage are required", "error"); return; }
    if (!existingConsultation) { showToast("Please save consultation first", "error"); return; }
    setSaving(true);
    try {
      const res = await consultationApi.addPrescription(existingConsultation.id, rxForm);
      setPrescriptions(p => [...p, res.data]);
      setRxForm(EMPTY_RX);
      showToast("Prescription added", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to add prescription", "error");
    } finally { setSaving(false); }
  }

  async function orderLabTest() {
    if (!labForm.test) { showToast("Select a lab test", "error"); return; }
    if (!existingConsultation) { showToast("Please save consultation first", "error"); return; }
    setSaving(true);
    try {
      await labApi.createOrder({
        ...labForm,
        patient: selectedVisit.patient?.id,
        consultation: existingConsultation.id,
      });
      setLabForm(EMPTY_LAB);
      showToast("Lab order created", "success");
    } catch {
      showToast("Failed to create lab order", "error");
    } finally { setSaving(false); }
  }

  const TRIAGE_COLORS = { RED: "#dc2626", ORANGE: "#f97316", YELLOW: "#eab308", GREEN: "#16a34a", BLUE: "#2563eb" };

  // If no visit selected, show waiting list
  if (!selectedVisit) {
    return (
      <Layout>
        <ToastContainer toasts={toasts} removeToast={removeToast} />
        <PageHeader title="Consultations" subtitle="Select a patient to start consultation" />
        {loading ? <LoadingSpinner /> : visits.length === 0 ? (
          <EmptyState icon="bi-check2-all" title="No patients waiting" subtitle="Your queue is clear" />
        ) : (
          <div className="row g-3">
            {visits.map((visit, idx) => {
              const tc = visit.triage?.category;
              return (
                <div key={visit.id} className="col-12 col-md-6 col-xl-4">
                  <div className="mc-card" style={{ borderLeft: `4px solid ${TRIAGE_COLORS[tc?.color_code] || "#ccc"}`, cursor: "pointer" }} onClick={() => selectVisit(visit)}>
                    <div className="d-flex align-items-start justify-content-between mb-2">
                      <div>
                        <div className="fw-bold">#{idx + 1} — {visit.visit_number}</div>
                        <div className="fw-medium">{visit.patient_name || "Patient"}</div>
                      </div>
                      {tc && <span className="badge" style={{ background: TRIAGE_COLORS[tc.color_code], color: "white" }}>{tc.name || tc.color_code}</span>}
                    </div>
                    <p className="text-muted small mb-2">{visit.chief_complaint}</p>
                    {visit.triage && (
                      <div className="row g-1 text-center">
                        {[
                          ["Temp", visit.triage.temperature, "°C"],
                          ["Pulse", visit.triage.pulse_rate, "bpm"],
                          ["BP", `${visit.triage.blood_pressure_systolic||"?"}/${visit.triage.blood_pressure_diastolic||"?"}`, "mmHg"],
                          ["SpO2", visit.triage.oxygen_saturation, "%"],
                        ].map(([label, val, unit]) => (
                          <div key={label} className="col-3">
                            <div className="border rounded p-1">
                              <div className="small fw-semibold">{val || "—"}<span className="text-muted">{val ? unit : ""}</span></div>
                              <div style={{ fontSize: 10 }} className="text-muted">{label}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    <button className="btn btn-mc-primary w-100 mt-2">
                      <i className="bi bi-person-badge me-2" />See Patient
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Layout>
    );
  }

  // Consultation workspace
  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title={`Consulting: ${selectedVisit.patient_name || "Patient"}`}
        subtitle={`Visit ${selectedVisit.visit_number} • ${selectedVisit.visit_type?.replace("_", " ")}`}
        actions={
          <button className="btn btn-mc-secondary" onClick={() => setSelectedVisit(null)}>
            <i className="bi bi-arrow-left me-2" />Back to Queue
          </button>
        }
      />

      {/* Patient & Triage Summary */}
      {selectedVisit.triage && (
        <div className="mc-card mb-3">
          <div className="row g-3 align-items-center">
            <div className="col-md-6">
              <h6 className="fw-semibold mb-2">Chief Complaint</h6>
              <p className="text-muted mb-0">{selectedVisit.chief_complaint}</p>
            </div>
            <div className="col-md-6">
              <div className="row g-2 text-center">
                {[
                  ["Temp", `${selectedVisit.triage.temperature || "—"}°C`, selectedVisit.triage.temperature > 37.5 ? "danger" : "success"],
                  ["Pulse", `${selectedVisit.triage.pulse_rate || "—"} bpm`, ""],
                  ["BP", `${selectedVisit.triage.blood_pressure_systolic || "?"}/${selectedVisit.triage.blood_pressure_diastolic || "?"}`, ""],
                  ["SpO2", `${selectedVisit.triage.oxygen_saturation || "—"}%`, selectedVisit.triage.oxygen_saturation < 95 ? "danger" : "success"],
                  ["Pain", `${selectedVisit.triage.pain_score || 0}/10`, selectedVisit.triage.pain_score > 7 ? "danger" : ""],
                ].map(([label, value, alert]) => (
                  <div key={label} className="col">
                    <div className={`border rounded p-2 ${alert === "danger" ? "border-danger bg-danger bg-opacity-10" : ""}`}>
                      <div className={`fw-semibold ${alert === "danger" ? "text-danger" : "text-primary"}`}>{value}</div>
                      <div className="text-muted" style={{ fontSize: 11 }}>{label}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mc-card mb-3">
        <Tabs
          tabs={[
            { key: "consultation", label: existingConsultation ? "✓ Consultation" : "Consultation" },
            { key: "prescriptions", label: `Prescriptions (${prescriptions.length})` },
            { key: "lab", label: "Lab Orders" },
            { key: "imaging", label: "Imaging" },
          ]}
          active={activeSection}
          onChange={setActiveSection}
        />
      </div>

      {/* Consultation Tab */}
      {activeSection === "consultation" && (
        <div className="mc-card">
          {existingConsultation && (
            <div className="mc-alert success mb-3"><i className="bi bi-check-circle me-2" />Consultation saved. Consultation code: <strong>{existingConsultation.consultation_code}</strong></div>
          )}
          <div className="row g-3">
            <FormRow label="Diagnosis *" colClass="col-12">
              <textarea className="mc-input" rows={3} placeholder="Clinical diagnosis..." value={consultForm.diagnosis} onChange={e => setConsultForm(f => ({ ...f, diagnosis: e.target.value }))} />
            </FormRow>
            <FormRow label="Clinical Notes" colClass="col-12">
              <textarea className="mc-input" rows={4} placeholder="Examination findings, clinical notes, management plan..." value={consultForm.notes} onChange={e => setConsultForm(f => ({ ...f, notes: e.target.value }))} />
            </FormRow>
            <FormRow label="Follow-up Date" colClass="col-md-6">
              <input type="date" className="mc-input" value={consultForm.follow_up_date} onChange={e => setConsultForm(f => ({ ...f, follow_up_date: e.target.value }))} />
            </FormRow>
            <FormRow label="Follow-up Notes" colClass="col-md-6">
              <input className="mc-input" placeholder="Instructions for follow-up..." value={consultForm.follow_up_notes} onChange={e => setConsultForm(f => ({ ...f, follow_up_notes: e.target.value }))} />
            </FormRow>
            <div className="col-12">
              <button className="btn btn-mc-primary" onClick={saveConsultation} disabled={saving || !!existingConsultation}>
                {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check2 me-2" />}
                {existingConsultation ? "Consultation Saved" : "Save Consultation"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Prescriptions Tab */}
      {activeSection === "prescriptions" && (
        <div>
          {prescriptions.length > 0 && (
            <div className="mc-card mb-3">
              <h6 className="fw-semibold mb-3">Current Prescriptions</h6>
              {prescriptions.map(rx => (
                <div key={rx.id} className="d-flex align-items-center justify-content-between py-2 border-bottom">
                  <div>
                    <div className="fw-medium">{rx.medicine?.name || rx.medicine_name}</div>
                    <small className="text-muted">{rx.dosage_text} — {rx.duration}</small>
                  </div>
                  <div className="text-end">
                    <div className="fw-semibold">{rx.quantity} units</div>
                    <span className={`badge ${rx.is_dispensed ? "bg-success" : "bg-warning text-dark"}`}>{rx.is_dispensed ? "Dispensed" : "Pending"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mc-card">
            <h6 className="fw-semibold mb-3">Add Prescription</h6>
            <div className="row g-3">
              <FormRow label="Medicine *" colClass="col-md-6">
                <select className="mc-select" value={rxForm.medicine} onChange={e => setRxForm(f => ({ ...f, medicine: e.target.value }))}>
                  <option value="">Select Medicine</option>
                  {medicines.map(m => <option key={m.id} value={m.id}>{m.name} — Stock: {m.quantity_in_stock}</option>)}
                </select>
              </FormRow>
              <FormRow label="Quantity (units) *" colClass="col-md-3">
                <input type="number" className="mc-input" value={rxForm.quantity} onChange={e => setRxForm(f => ({ ...f, quantity: e.target.value }))} placeholder="e.g. 30" />
              </FormRow>
              <FormRow label="Dosage *" colClass="col-md-3">
                <input className="mc-input" value={rxForm.dosage_text} onChange={e => setRxForm(f => ({ ...f, dosage_text: e.target.value }))} placeholder="e.g. 2 tabs BD" />
              </FormRow>
              <FormRow label="Duration *" colClass="col-md-4">
                <input className="mc-input" value={rxForm.duration} onChange={e => setRxForm(f => ({ ...f, duration: e.target.value }))} placeholder="e.g. 7 days" />
              </FormRow>
              <FormRow label="Instructions" colClass="col-md-8">
                <input className="mc-input" value={rxForm.instructions} onChange={e => setRxForm(f => ({ ...f, instructions: e.target.value }))} placeholder="e.g. Take after meals" />
              </FormRow>
              <div className="col-12">
                <button className="btn btn-mc-primary" onClick={addPrescription} disabled={saving}>
                  <i className="bi bi-plus-circle me-2" />Add Prescription
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lab Orders Tab */}
      {activeSection === "lab" && (
        <div className="mc-card">
          <h6 className="fw-semibold mb-3">Order Lab Test</h6>
          <div className="row g-3">
            <FormRow label="Lab Test *" colClass="col-md-6">
              <select className="mc-select" value={labForm.test} onChange={e => setLabForm(f => ({ ...f, test: e.target.value }))}>
                <option value="">Select Test</option>
                {labTests.map(t => <option key={t.id} value={t.id}>{t.test_code} — {t.test_name} (KSh {t.cost})</option>)}
              </select>
            </FormRow>
            <FormRow label="Priority" colClass="col-md-3">
              <select className="mc-select" value={labForm.priority} onChange={e => setLabForm(f => ({ ...f, priority: e.target.value }))}>
                <option value="ROUTINE">Routine</option>
                <option value="URGENT">Urgent</option>
                <option value="EMERGENCY">Emergency</option>
                <option value="STAT">STAT</option>
              </select>
            </FormRow>
            <FormRow label="Clinical Notes" colClass="col-12">
              <textarea className="mc-input" rows={2} value={labForm.clinical_notes} onChange={e => setLabForm(f => ({ ...f, clinical_notes: e.target.value }))} placeholder="Clinical indication for this test..." />
            </FormRow>
            <div className="col-12">
              <button className="btn btn-mc-primary" onClick={orderLabTest} disabled={saving}>
                <i className="bi bi-eyedropper me-2" />Order Lab Test
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Imaging Tab */}
      {activeSection === "imaging" && (
        <div className="mc-card">
          <h6 className="fw-semibold mb-3">Request Imaging Study</h6>
          <ImagingOrderForm consultationId={existingConsultation?.id} patientId={selectedVisit.patient?.id} onSuccess={() => showToast("Imaging request sent", "success")} />
        </div>
      )}
    </Layout>
  );
}

function ImagingOrderForm({ consultationId, patientId, onSuccess }) {
  const [form, setForm] = useState({ modality: "XRAY", body_part: "CHEST", study_description: "", clinical_indication: "", is_urgent: false });
  const [saving, setSaving] = useState(false);
  const { showToast } = useToast();

  async function submit() {
    if (!form.study_description || !form.clinical_indication) { showToast("Description and indication required", "error"); return; }
    setSaving(true);
    try {
      await imagingApi.create({ ...form, consultation: consultationId, patient: patientId });
      setForm({ modality: "XRAY", body_part: "CHEST", study_description: "", clinical_indication: "", is_urgent: false });
      onSuccess();
    } catch { showToast("Failed to create imaging request", "error"); }
    finally { setSaving(false); }
  }

  return (
    <div className="row g-3">
      <FormRow label="Modality" colClass="col-md-4">
        <select className="mc-select" value={form.modality} onChange={e => setForm(f => ({ ...f, modality: e.target.value }))}>
          {[["XRAY","X-Ray"],["CT","CT Scan"],["MRI","MRI"],["ULTRASOUND","Ultrasound"],["MAMMOGRAPHY","Mammography"]].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </FormRow>
      <FormRow label="Body Part" colClass="col-md-4">
        <select className="mc-select" value={form.body_part} onChange={e => setForm(f => ({ ...f, body_part: e.target.value }))}>
          {[["CHEST","Chest"],["ABDOMEN","Abdomen"],["HEAD","Head/Skull"],["SPINE","Spine"],["PELVIS","Pelvis"],["EXTREMITIES","Extremities"]].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </FormRow>
      <div className="col-md-4 d-flex align-items-end">
        <div className="form-check">
          <input type="checkbox" className="form-check-input" id="urgent" checked={form.is_urgent} onChange={e => setForm(f => ({ ...f, is_urgent: e.target.checked }))} />
          <label className="form-check-label text-danger fw-medium" htmlFor="urgent">Mark as Urgent</label>
        </div>
      </div>
      <FormRow label="Study Description *" colClass="col-md-6">
        <input className="mc-input" value={form.study_description} onChange={e => setForm(f => ({ ...f, study_description: e.target.value }))} placeholder="e.g. Chest X-Ray PA and Lateral" />
      </FormRow>
      <FormRow label="Clinical Indication *" colClass="col-md-6">
        <input className="mc-input" value={form.clinical_indication} onChange={e => setForm(f => ({ ...f, clinical_indication: e.target.value }))} placeholder="Reason for imaging..." />
      </FormRow>
      <div className="col-12">
        <button className="btn btn-mc-primary" onClick={submit} disabled={saving}>
          <i className="bi bi-x-ray me-2" />Submit Imaging Request
        </button>
      </div>
    </div>
  );
}