import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, useToast, ToastContainer, DataTable, FormRow, SearchInput } from "../../components/common/index.jsx";
import { otcApi, medicineApi } from "../../services/api";

export default function PharmacyOTC() {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [medicines, setMedicines] = useState([]);
  const [cart, setCart] = useState([]);
  const [medSearch, setMedSearch] = useState("");
  const [medResults, setMedResults] = useState([]);
  const [saving, setSaving] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const { toasts, showToast, removeToast } = useToast();

  useEffect(() => { fetchSales(); }, []);

  async function fetchSales() {
    setLoading(true);
    try {
      const res = await otcApi.list({ ordering: "-created_at" });
      setSales(res.data.results || res.data);
    } catch { showToast("Failed to load OTC sales", "error"); }
    finally { setLoading(false); }
  }

  async function searchMedicines(q) {
    if (!q || q.length < 2) { setMedResults([]); return; }
    try {
      const res = await medicineApi.list({ search: q, limit: 10 });
      setMedResults(res.data.results || res.data);
    } catch {}
  }

  function addToCart(medicine, qty = 1) {
    const existing = cart.find(c => c.medicine.id === medicine.id);
    if (existing) {
      setCart(cart.map(c => c.medicine.id === medicine.id ? { ...c, qty: c.qty + qty } : c));
    } else {
      setCart([...cart, { medicine, qty }]);
    }
    setMedSearch("");
    setMedResults([]);
  }

  function removeFromCart(medicineId) {
    setCart(cart.filter(c => c.medicine.id !== medicineId));
  }

  function updateQty(medicineId, qty) {
    if (qty <= 0) { removeFromCart(medicineId); return; }
    setCart(cart.map(c => c.medicine.id === medicineId ? { ...c, qty } : c));
  }

  const cartTotal = cart.reduce((sum, c) => sum + (parseFloat(c.medicine.selling_price || 0) * c.qty), 0);

  async function processSale() {
    if (cart.length === 0) { showToast("Add at least one item to cart", "error"); return; }
    setSaving(true);
    try {
      await otcApi.dispense({
        customer_name: customerName || "Walk-in Customer",
        customer_phone: customerPhone,
        items: cart.map(c => ({ medicine: c.medicine.id, quantity: c.qty })),
      });
      showToast("OTC sale processed successfully", "success");
      setCart([]);
      setCustomerName("");
      setCustomerPhone("");
      fetchSales();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to process sale", "error");
    } finally { setSaving(false); }
  }

  const saleColumns = [
    { key: "sale_number", label: "Sale #", render: s => <code className="text-primary">{s.sale_number}</code> },
    { key: "customer", label: "Customer", render: s => s.customer_name || "Walk-in" },
    { key: "items", label: "Items", render: s => `${s.items?.length || 0} item(s)` },
    { key: "total", label: "Total", render: s => `KSh ${parseFloat(s.total_amount || 0).toLocaleString()}` },
    { key: "time", label: "Time", render: s => new Date(s.created_at).toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" }) },
    { key: "status", label: "Status", render: s => <span className={`badge ${s.is_paid ? "bg-success" : "bg-warning text-dark"}`}>{s.is_paid ? "Paid" : "Unpaid"}</span> },
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="OTC Sales" subtitle="Over-the-counter medicine dispensing" />

      <div className="row g-3">
        {/* Sale Form */}
        <div className="col-12 col-xl-5">
          <div className="mc-card">
            <h6 className="fw-semibold mb-3"><i className="bi bi-cart3 text-primary me-2" />New OTC Sale</h6>

            {/* Customer */}
            <div className="row g-2 mb-3">
              <div className="col-7">
                <input className="mc-input" placeholder="Customer name (optional)" value={customerName} onChange={e => setCustomerName(e.target.value)} />
              </div>
              <div className="col-5">
                <input className="mc-input" placeholder="Phone (optional)" value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} />
              </div>
            </div>

            {/* Medicine Search */}
            <div className="mb-3 position-relative">
              <input
                className="mc-input"
                placeholder="Search and add medicine..."
                value={medSearch}
                onChange={e => { setMedSearch(e.target.value); searchMedicines(e.target.value); }}
              />
              {medResults.length > 0 && (
                <div className="border rounded shadow-sm bg-white position-absolute w-100" style={{ zIndex: 100, top: "100%", maxHeight: 200, overflowY: "auto" }}>
                  {medResults.map(m => (
                    <div key={m.id} className="px-3 py-2 d-flex justify-content-between align-items-center" style={{ cursor: "pointer" }}
                      onClick={() => addToCart(m)}>
                      <div>
                        <div className="fw-medium">{m.name}</div>
                        <small className="text-muted">Stock: {m.quantity_in_stock}</small>
                      </div>
                      <span className="text-primary fw-semibold">KSh {parseFloat(m.selling_price || 0).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Cart */}
            {cart.length === 0 ? (
              <div className="text-center py-4 text-muted border-dashed rounded">
                <i className="bi bi-cart2 mb-2" style={{ fontSize: 32 }} /><br />Cart is empty
              </div>
            ) : (
              <>
                {cart.map(c => (
                  <div key={c.medicine.id} className="d-flex align-items-center gap-2 py-2 border-bottom">
                    <div className="flex-grow-1">
                      <div className="fw-medium">{c.medicine.name}</div>
                      <small className="text-muted">KSh {parseFloat(c.medicine.selling_price || 0).toLocaleString()} each</small>
                    </div>
                    <div className="d-flex align-items-center gap-1">
                      <button className="btn btn-sm btn-outline-secondary px-2 py-0" onClick={() => updateQty(c.medicine.id, c.qty - 1)}>−</button>
                      <span className="fw-semibold px-2">{c.qty}</span>
                      <button className="btn btn-sm btn-outline-secondary px-2 py-0" onClick={() => updateQty(c.medicine.id, c.qty + 1)}>+</button>
                    </div>
                    <div className="text-end" style={{ minWidth: 80 }}>
                      <div className="fw-semibold">KSh {(parseFloat(c.medicine.selling_price || 0) * c.qty).toLocaleString()}</div>
                    </div>
                    <button className="btn btn-icon text-danger" onClick={() => removeFromCart(c.medicine.id)}><i className="bi bi-trash" /></button>
                  </div>
                ))}

                <div className="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                  <span className="fw-bold">Total</span>
                  <span className="fw-bold text-primary" style={{ fontSize: 20 }}>KSh {cartTotal.toLocaleString()}</span>
                </div>

                <button className="btn btn-mc-primary w-100 mt-3" onClick={processSale} disabled={saving}>
                  {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check-circle me-2" />}
                  Process Sale — KSh {cartTotal.toLocaleString()}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Recent Sales */}
        <div className="col-12 col-xl-7">
          <div className="mc-card h-100">
            <h6 className="fw-semibold mb-3"><i className="bi bi-clock-history text-primary me-2" />Today's OTC Sales</h6>
            {loading ? <LoadingSpinner /> : sales.length === 0 ? (
              <EmptyState icon="bi-bag" title="No OTC sales today" />
            ) : <DataTable columns={saleColumns} data={sales} />}
          </div>
        </div>
      </div>
    </Layout>
  );
}