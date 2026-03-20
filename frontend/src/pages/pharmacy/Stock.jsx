import { useState, useEffect, useRef } from "react";
import Layout from "../../components/layout/Layout";
import {
  PageHeader, LoadingSpinner, EmptyState, Modal, useToast,
  ToastContainer, DataTable, FormRow, Tabs, SearchInput, SectionCard
} from "../../components/common/index.jsx";
import { medicineApi } from "../../services/api";

const EMPTY_FORM = {
  name: "", generic_name: "", medicine_code: "", category: "", manufacturer: "",
  unit_type: "TABLETS", quantity_in_stock: "", reorder_level: "50",
  buying_price: "", selling_price: "", insurance_price: "",
  expiry_date: "", shelf_location: "", description: "",
};

export default function PharmacyStock() {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const [showAdjust, setShowAdjust] = useState(false);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [adjustForm, setAdjustForm] = useState({ adjustment_type: "ADD", quantity: "", reason: "", batch_number: "", expiry_date: "" });
  const [saving, setSaving] = useState(false);
  const { toasts, showToast, removeToast } = useToast();
  const searchTimeout = useRef(null);

  useEffect(() => {
    clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(fetchMedicines, 350);
  }, [search, tab]);

  async function fetchMedicines() {
    setLoading(true);
    try {
      const params = { search, ordering: "name" };
      if (tab === "low") params.low_stock = true;
      if (tab === "expired") params.expired = true;
      const res = await medicineApi.list(params);
      setMedicines(res.data.results || res.data);
    } catch { showToast("Failed to load medicines", "error"); }
    finally { setLoading(false); }
  }

  async function saveMedicine() {
    if (!form.name || !form.selling_price) { showToast("Name and selling price are required", "error"); return; }
    setSaving(true);
    try {
      if (selected) await medicineApi.update(selected.id, form);
      else await medicineApi.create(form);
      showToast(selected ? "Medicine updated" : "Medicine added", "success");
      setShowModal(false);
      setSelected(null);
      setForm(EMPTY_FORM);
      fetchMedicines();
    } catch (err) { showToast(err.response?.data?.detail || "Failed to save", "error"); }
    finally { setSaving(false); }
  }

  async function submitAdjust() {
    if (!adjustForm.quantity || !adjustForm.reason) { showToast("Quantity and reason are required", "error"); return; }
    setSaving(true);
    try {
      await medicineApi.adjustStock(selected.id, adjustForm);
      showToast("Stock adjusted successfully", "success");
      setShowAdjust(false);
      fetchMedicines();
    } catch { showToast("Failed to adjust stock", "error"); }
    finally { setSaving(false); }
  }

  function openEdit(m) {
    setSelected(m);
    setForm({
      name: m.name, generic_name: m.generic_name || "", medicine_code: m.medicine_code || "",
      category: m.category || "", manufacturer: m.manufacturer || "",
      unit_type: m.unit_type || "TABLETS", quantity_in_stock: m.quantity_in_stock,
      reorder_level: m.reorder_level, buying_price: m.buying_price || "",
      selling_price: m.selling_price, insurance_price: m.insurance_price || "",
      expiry_date: m.expiry_date || "", shelf_location: m.shelf_location || "",
      description: m.description || "",
    });
    setShowModal(true);
  }

  function getStockStatus(m) {
    if (m.quantity_in_stock <= 0) return { label: "Out of Stock", cls: "bg-danger" };
    if (m.quantity_in_stock <= m.reorder_level) return { label: "Low Stock", cls: "bg-warning text-dark" };
    return { label: "In Stock", cls: "bg-success" };
  }

  const columns = [
    { key: "code", label: "Code", render: m => <code className="text-primary">{m.medicine_code || "—"}</code> },
    { key: "name", label: "Medicine", render: m => (
      <div>
        <div className="fw-semibold">{m.name}</div>
        <small className="text-muted">{m.generic_name || m.category}</small>
      </div>
    )},
    { key: "unit", label: "Unit", render: m => <small>{m.unit_type}</small> },
    { key: "qty", label: "Stock", render: m => {
      const s = getStockStatus(m);
      return (
        <div>
          <span className="fw-semibold">{m.quantity_in_stock}</span>
          <span className={`badge ms-2 ${s.cls}`}>{s.label}</span>
        </div>
      );
    }},
    { key: "reorder", label: "Reorder Level", render: m => m.reorder_level },
    { key: "price", label: "Selling Price", render: m => `KSh ${parseFloat(m.selling_price || 0).toLocaleString()}` },
    { key: "expiry", label: "Expiry", render: m => m.expiry_date ? (
      <span className={new Date(m.expiry_date) < new Date() ? "text-danger fw-medium" : ""}>{m.expiry_date}</span>
    ) : "—" },
    { key: "actions", label: "", render: m => (
      <div className="d-flex gap-1">
        <button className="btn btn-icon" title="Edit" onClick={() => openEdit(m)}><i className="bi bi-pencil" /></button>
        <button className="btn btn-icon text-primary" title="Adjust Stock" onClick={() => { setSelected(m); setShowAdjust(true); }}>
          <i className="bi bi-arrow-left-right" />
        </button>
      </div>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader
        title="Stock Management"
        subtitle={`${medicines.length} medicines in formulary`}
        actions={
          <button className="btn btn-mc-primary" onClick={() => { setSelected(null); setForm(EMPTY_FORM); setShowModal(true); }}>
            <i className="bi bi-plus-circle me-2" />Add Medicine
          </button>
        }
      />

      <div className="mc-card mb-3">
        <div className="d-flex flex-wrap gap-3 align-items-center">
          <Tabs
            tabs={[{ key: "all", label: "All Medicines" }, { key: "low", label: "Low Stock" }, { key: "expired", label: "Expired" }]}
            active={tab}
            onChange={setTab}
          />
          <div className="ms-auto" style={{ minWidth: 260 }}>
            <SearchInput value={search} onChange={setSearch} placeholder="Search medicines..." />
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : medicines.length === 0 ? (
        <EmptyState icon="bi-capsule" title="No medicines found" subtitle="Add medicines to the formulary" />
      ) : <DataTable columns={columns} data={medicines} />}

      {/* Add/Edit Medicine Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setSelected(null); setForm(EMPTY_FORM); }}
        title={selected ? "Edit Medicine" : "Add Medicine"}
        size="xl"
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={saveMedicine} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : null}Save Medicine
            </button>
          </>
        }
      >
        <div className="row g-3">
          <FormRow label="Medicine Name *" colClass="col-md-6">
            <input className="mc-input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. Amoxicillin 500mg" />
          </FormRow>
          <FormRow label="Generic Name" colClass="col-md-6">
            <input className="mc-input" value={form.generic_name} onChange={e => setForm(f => ({ ...f, generic_name: e.target.value }))} placeholder="Generic / INN name" />
          </FormRow>
          <FormRow label="Medicine Code" colClass="col-md-4">
            <input className="mc-input" value={form.medicine_code} onChange={e => setForm(f => ({ ...f, medicine_code: e.target.value }))} placeholder="e.g. AMX500" />
          </FormRow>
          <FormRow label="Category" colClass="col-md-4">
            <input className="mc-input" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} placeholder="e.g. Antibiotics" />
          </FormRow>
          <FormRow label="Unit Type" colClass="col-md-4">
            <select className="mc-select" value={form.unit_type} onChange={e => setForm(f => ({ ...f, unit_type: e.target.value }))}>
              {["TABLETS","CAPSULES","SYRUP","INJECTION","CREAM","DROPS","INHALER","PATCH","SUPPOSITORY","OTHER"].map(u =>
                <option key={u} value={u}>{u}</option>
              )}
            </select>
          </FormRow>
          <FormRow label="Current Stock (units)" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.quantity_in_stock} onChange={e => setForm(f => ({ ...f, quantity_in_stock: e.target.value }))} />
          </FormRow>
          <FormRow label="Reorder Level" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.reorder_level} onChange={e => setForm(f => ({ ...f, reorder_level: e.target.value }))} />
          </FormRow>
          <FormRow label="Expiry Date" colClass="col-md-4">
            <input type="date" className="mc-input" value={form.expiry_date} onChange={e => setForm(f => ({ ...f, expiry_date: e.target.value }))} />
          </FormRow>
          <FormRow label="Buying Price (KSh)" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.buying_price} onChange={e => setForm(f => ({ ...f, buying_price: e.target.value }))} />
          </FormRow>
          <FormRow label="Selling Price (KSh) *" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.selling_price} onChange={e => setForm(f => ({ ...f, selling_price: e.target.value }))} />
          </FormRow>
          <FormRow label="Insurance Price (KSh)" colClass="col-md-4">
            <input type="number" className="mc-input" value={form.insurance_price} onChange={e => setForm(f => ({ ...f, insurance_price: e.target.value }))} />
          </FormRow>
          <FormRow label="Manufacturer" colClass="col-md-6">
            <input className="mc-input" value={form.manufacturer} onChange={e => setForm(f => ({ ...f, manufacturer: e.target.value }))} />
          </FormRow>
          <FormRow label="Shelf Location" colClass="col-md-6">
            <input className="mc-input" value={form.shelf_location} onChange={e => setForm(f => ({ ...f, shelf_location: e.target.value }))} placeholder="e.g. Shelf A3" />
          </FormRow>
        </div>
      </Modal>

      {/* Adjust Stock Modal */}
      <Modal
        show={showAdjust && !!selected}
        onClose={() => setShowAdjust(false)}
        title={`Adjust Stock — ${selected?.name}`}
        footer={
          <>
            <button className="btn btn-mc-secondary" onClick={() => setShowAdjust(false)}>Cancel</button>
            <button className="btn btn-mc-primary" onClick={submitAdjust} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-2" /> : null}Submit Adjustment
            </button>
          </>
        }
      >
        <div className="mc-alert info mb-3">
          <strong>Current stock:</strong> {selected?.quantity_in_stock} units
        </div>
        <div className="row g-3">
          <FormRow label="Adjustment Type" colClass="col-md-6">
            <select className="mc-select" value={adjustForm.adjustment_type} onChange={e => setAdjustForm(f => ({ ...f, adjustment_type: e.target.value }))}>
              <option value="ADD">Stock In (Add)</option>
              <option value="REMOVE">Stock Out (Remove)</option>
              <option value="RETURN">Return / Reversal</option>
              <option value="EXPIRED">Expired / Wastage</option>
              <option value="DAMAGE">Damaged / Lost</option>
            </select>
          </FormRow>
          <FormRow label="Quantity *" colClass="col-md-6">
            <input type="number" className="mc-input" value={adjustForm.quantity} onChange={e => setAdjustForm(f => ({ ...f, quantity: e.target.value }))} placeholder="Units" />
          </FormRow>
          <FormRow label="Batch Number" colClass="col-md-6">
            <input className="mc-input" value={adjustForm.batch_number} onChange={e => setAdjustForm(f => ({ ...f, batch_number: e.target.value }))} />
          </FormRow>
          <FormRow label="Reason *" colClass="col-12">
            <textarea className="mc-input" rows={2} value={adjustForm.reason} onChange={e => setAdjustForm(f => ({ ...f, reason: e.target.value }))} placeholder="Reason for stock adjustment..." />
          </FormRow>
        </div>
      </Modal>
    </Layout>
  );
}