import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import { PageHeader, LoadingSpinner, EmptyState, useToast, ToastContainer, DataTable, Tabs, SearchInput } from "../../components/common/index.jsx";
import { prescriptionApi, consultationApi } from "../../services/api";

export default function PharmacyDispense() {
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pending");
  const [search, setSearch] = useState("");
  const [dispensing, setDispensing] = useState(null);
  const { toasts, showToast, removeToast } = useToast();
  const [searchParams] = useSearchParams();

  useEffect(() => { fetchPrescriptions(); }, [tab]);

  async function fetchPrescriptions() {
    setLoading(true);
    try {
      const params = { ordering: "-prescribed_at" };
      if (tab === "pending") params.is_dispensed = false;
      if (tab === "dispensed") params.is_dispensed = true;
      const res = await prescriptionApi.list(params);
      setPrescriptions(res.data.results || res.data);
    } catch { showToast("Failed to load prescriptions", "error"); }
    finally { setLoading(false); }
  }

  async function dispense(prescription) {
    setDispensing(prescription.id);
    try {
      await prescriptionApi.dispense(prescription.id);
      showToast(`Dispensed: ${prescription.medicine?.name || "Medicine"}`, "success");
      fetchPrescriptions();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to dispense", "error");
    } finally { setDispensing(null); }
  }

  const filtered = prescriptions.filter(rx => {
    if (!search) return true;
    const name = `${rx.consultation?.appointment?.patient?.first_name || ""} ${rx.consultation?.appointment?.patient?.last_name || ""} ${rx.medicine?.name || ""}`.toLowerCase();
    return name.includes(search.toLowerCase());
  });

  const columns = [
    { key: "medicine", label: "Medicine", render: rx => (
      <div>
        <div className="fw-semibold">{rx.medicine?.name}</div>
        <small className="text-muted">{rx.medicine?.get_unit_type_display || rx.medicine?.unit_type}</small>
      </div>
    )},
    { key: "patient", label: "Patient", render: rx => (
      <div>
        <div className="fw-medium">{rx.consultation?.appointment?.patient?.first_name} {rx.consultation?.appointment?.patient?.last_name}</div>
        <small className="text-muted">Code: {rx.consultation?.consultation_code}</small>
      </div>
    )},
    { key: "dosage", label: "Dosage", render: rx => (
      <div>
        <div className="small">{rx.dosage_text}</div>
        <small className="text-muted">{rx.duration} — {rx.quantity} units</small>
      </div>
    )},
    { key: "insured", label: "Pay Type", render: rx => rx.is_insured
      ? <span className="badge bg-info text-dark"><i className="bi bi-shield-check me-1" />{rx.insurance_provider?.name || "Insurance"}</span>
      : <span className="badge bg-secondary">Cash</span>
    },
    { key: "stock", label: "In Stock", render: rx => (
      <span className={rx.medicine?.quantity_in_stock < rx.quantity ? "text-danger fw-semibold" : "text-success fw-semibold"}>
        {rx.medicine?.quantity_in_stock ?? "—"}
      </span>
    )},
    { key: "total", label: "Amount", render: rx => rx.total_price ? `KSh ${parseFloat(rx.total_price).toLocaleString()}` : "—" },
    { key: "actions", label: "", render: rx => rx.is_dispensed ? (
      <span className="badge bg-success"><i className="bi bi-check2 me-1" />Dispensed</span>
    ) : (
      <button
        className="btn btn-sm btn-mc-primary"
        onClick={() => dispense(rx)}
        disabled={dispensing === rx.id || (rx.medicine?.quantity_in_stock < rx.quantity)}
      >
        {dispensing === rx.id ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="bi bi-bag-check me-1" />}
        Dispense
      </button>
    )},
  ];

  return (
    <Layout>
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <PageHeader title="Dispense Prescriptions" subtitle="Review and dispense doctor prescriptions" />

      <div className="mc-card mb-3">
        <div className="d-flex flex-wrap gap-3 align-items-center">
          <Tabs
            tabs={[{ key: "pending", label: `Pending (${tab === "pending" ? filtered.length : "?"})` }, { key: "dispensed", label: "Dispensed" }, { key: "all", label: "All" }]}
            active={tab}
            onChange={setTab}
          />
          <div className="ms-auto" style={{ minWidth: 240 }}>
            <SearchInput value={search} onChange={setSearch} placeholder="Search patient or medicine..." />
          </div>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : filtered.length === 0 ? (
        <EmptyState icon="bi-prescription2" title={tab === "pending" ? "No pending prescriptions" : "No records found"} subtitle="" />
      ) : <DataTable columns={columns} data={filtered} />}
    </Layout>
  );
}