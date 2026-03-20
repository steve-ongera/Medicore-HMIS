import { useState } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, useToast, ToastContainer, FormRow, Tabs } from "../../components/common/index.jsx";

export default function AdminSettings() {
  const [tab, setTab] = useState("hospital");
  const [saving, setSaving] = useState(false);
  const [hospital, setHospital] = useState({
    name: "MediCore Hospital", code: "MCH", address: "", county: "", country: "Kenya",
    phone: "", email: "", website: "", keph_level: "", nhif_code: "", logo_url: "",
  });
  const [system, setSystem] = useState({
    currency: "KSh", timezone: "Africa/Nairobi",
    consultation_fee: "500", enable_insurance: true, enable_sha: true,
    enable_etims: false, require_triage: true, auto_queue: true,
    session_timeout: "480",
  });
  const { toasts, showToast, removeToast } = useToast();

  async function saveSettings() {
    setSaving(true);
    await new Promise(r => setTimeout(r, 800));
    showToast("Settings saved successfully", "success");
    setSaving(false);
  }

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="System Settings"
        subtitle="Configure hospital and system preferences"
        actions={
          <button className="btn btn-mc-primary" onClick={saveSettings} disabled={saving}>
            {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-save me-2" />}
            Save Changes
          </button>
        }
      />

      <div className="mc-card mb-3">
        <Tabs
          tabs={[
            { key: "hospital", label: "Hospital Info" },
            { key: "system", label: "System Config" },
            { key: "billing", label: "Billing & Fees" },
            { key: "integrations", label: "Integrations" },
          ]}
          active={tab}
          onChange={setTab}
        />
      </div>

      {/* Hospital Info */}
      {tab === "hospital" && (
        <div className="mc-card">
          <h6 className="fw-semibold mb-4">Hospital Information</h6>
          <div className="row g-3">
            <FormRow label="Hospital Name" colClass="col-md-6">
              <input className="mc-input" value={hospital.name} onChange={e => setHospital(h => ({ ...h, name: e.target.value }))} />
            </FormRow>
            <FormRow label="Hospital Code" colClass="col-md-3">
              <input className="mc-input" value={hospital.code} onChange={e => setHospital(h => ({ ...h, code: e.target.value }))} />
            </FormRow>
            <FormRow label="KEPH Level" colClass="col-md-3">
              <select className="mc-select" value={hospital.keph_level} onChange={e => setHospital(h => ({ ...h, keph_level: e.target.value }))}>
                <option value="">Select Level</option>
                {["Level 1 (Community)","Level 2 (Dispensary)","Level 3 (Health Centre)","Level 4 (Sub-County Hospital)","Level 5 (County Referral)","Level 6 (National Referral)"].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </FormRow>
            <FormRow label="Address" colClass="col-md-8">
              <input className="mc-input" value={hospital.address} onChange={e => setHospital(h => ({ ...h, address: e.target.value }))} />
            </FormRow>
            <FormRow label="County" colClass="col-md-4">
              <input className="mc-input" value={hospital.county} onChange={e => setHospital(h => ({ ...h, county: e.target.value }))} placeholder="e.g. Nairobi" />
            </FormRow>
            <FormRow label="Phone" colClass="col-md-4">
              <input className="mc-input" value={hospital.phone} onChange={e => setHospital(h => ({ ...h, phone: e.target.value }))} />
            </FormRow>
            <FormRow label="Email" colClass="col-md-4">
              <input type="email" className="mc-input" value={hospital.email} onChange={e => setHospital(h => ({ ...h, email: e.target.value }))} />
            </FormRow>
            <FormRow label="Website" colClass="col-md-4">
              <input className="mc-input" value={hospital.website} onChange={e => setHospital(h => ({ ...h, website: e.target.value }))} />
            </FormRow>
            <FormRow label="NHIF / SHA Facility Code" colClass="col-md-4">
              <input className="mc-input" value={hospital.nhif_code} onChange={e => setHospital(h => ({ ...h, nhif_code: e.target.value }))} />
            </FormRow>
          </div>
        </div>
      )}

      {/* System Config */}
      {tab === "system" && (
        <div className="mc-card">
          <h6 className="fw-semibold mb-4">System Configuration</h6>
          <div className="row g-3">
            <FormRow label="Default Currency" colClass="col-md-4">
              <select className="mc-select" value={system.currency} onChange={e => setSystem(s => ({ ...s, currency: e.target.value }))}>
                <option value="KSh">KSh — Kenyan Shilling</option>
                <option value="USD">USD — US Dollar</option>
                <option value="UGX">UGX — Ugandan Shilling</option>
                <option value="TZS">TZS — Tanzanian Shilling</option>
              </select>
            </FormRow>
            <FormRow label="Timezone" colClass="col-md-4">
              <select className="mc-select" value={system.timezone} onChange={e => setSystem(s => ({ ...s, timezone: e.target.value }))}>
                <option value="Africa/Nairobi">Africa/Nairobi (EAT)</option>
                <option value="Africa/Kampala">Africa/Kampala</option>
                <option value="Africa/Dar_es_Salaam">Africa/Dar_es_Salaam</option>
              </select>
            </FormRow>
            <FormRow label="Session Timeout (minutes)" colClass="col-md-4">
              <input type="number" className="mc-input" value={system.session_timeout} onChange={e => setSystem(s => ({ ...s, session_timeout: e.target.value }))} />
            </FormRow>

            <div className="col-12">
              <h6 className="fw-semibold mt-2 mb-3">Feature Toggles</h6>
              <div className="row g-3">
                {[
                  { key: "require_triage", label: "Require Triage Before Consultation", icon: "bi-heart-pulse" },
                  { key: "auto_queue", label: "Auto-Add to Queue After Triage", icon: "bi-list-ol" },
                  { key: "enable_insurance", label: "Enable Insurance Module", icon: "bi-shield-check" },
                  { key: "enable_sha", label: "Enable SHA/Social Health Authority", icon: "bi-shield-plus" },
                  { key: "enable_etims", label: "Enable eTIMS (KRA Tax Integration)", icon: "bi-receipt" },
                ].map(({ key, label, icon }) => (
                  <div key={key} className="col-md-6">
                    <div className="d-flex align-items-center justify-content-between border rounded p-3">
                      <div className="d-flex align-items-center gap-2">
                        <i className={`bi ${icon} text-primary`} />
                        <span>{label}</span>
                      </div>
                      <div className="form-check form-switch mb-0">
                        <input
                          type="checkbox"
                          className="form-check-input"
                          checked={system[key]}
                          onChange={e => setSystem(s => ({ ...s, [key]: e.target.checked }))}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Billing */}
      {tab === "billing" && (
        <div className="mc-card">
          <h6 className="fw-semibold mb-4">Default Fees & Billing Configuration</h6>
          <div className="row g-3">
            <FormRow label="Default Consultation Fee (KSh)" colClass="col-md-4">
              <input type="number" className="mc-input" value={system.consultation_fee} onChange={e => setSystem(s => ({ ...s, consultation_fee: e.target.value }))} />
            </FormRow>
            <div className="col-12">
              <div className="mc-alert info">
                <i className="bi bi-info-circle me-2" />
                Specific consultation fees can be configured per doctor or specialized service in their respective settings.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Integrations */}
      {tab === "integrations" && (
        <div className="row g-3">
          {[
            { name: "NHIF / SHA", icon: "bi-shield-check", status: "configured", color: "green", desc: "National Hospital Insurance Fund integration for claims submission" },
            { name: "M-Pesa (Daraja API)", icon: "bi-phone", status: "not_configured", color: "orange", desc: "Safaricom M-Pesa STK push and payment confirmation" },
            { name: "eTIMS (KRA)", icon: "bi-receipt", status: "not_configured", color: "red", desc: "Kenya Revenue Authority electronic invoice management system" },
            { name: "SMS Gateway", icon: "bi-chat-text", status: "not_configured", color: "orange", desc: "Bulk SMS for appointment reminders and notifications" },
          ].map(integration => (
            <div key={integration.name} className="col-md-6">
              <div className="mc-card h-100">
                <div className="d-flex align-items-start gap-3">
                  <div className={`stat-icon ${integration.color}`} style={{ width: 48, height: 48, flexShrink: 0 }}>
                    <i className={integration.icon} />
                  </div>
                  <div className="flex-grow-1">
                    <div className="d-flex justify-content-between mb-1">
                      <h6 className="fw-semibold mb-0">{integration.name}</h6>
                      <span className={`badge ${integration.status === "configured" ? "bg-success" : "bg-warning text-dark"}`}>
                        {integration.status === "configured" ? "Configured" : "Not Configured"}
                      </span>
                    </div>
                    <p className="text-muted small mb-3">{integration.desc}</p>
                    <button className="btn btn-sm btn-mc-secondary">
                      <i className="bi bi-gear me-1" />{integration.status === "configured" ? "Update Settings" : "Configure"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}