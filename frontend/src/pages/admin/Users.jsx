import React, { useState, useEffect } from 'react'
import { userApi } from '../../services/api.js'
import { PageHeader, SearchInput, DataTable, StatusBadge, Modal, Alert } from '../../components/common/index.jsx'

const USER_TYPES = [
  { value: 'ADMIN', label: 'Administrator' },
  { value: 'DOCTOR', label: 'Doctor' },
  { value: 'NURSE', label: 'Nurse' },
  { value: 'RECEPTIONIST', label: 'Receptionist' },
  { value: 'PHARMACIST', label: 'Pharmacist' },
  { value: 'CASHIER', label: 'Cashier' },
  { value: 'LAB_TECH', label: 'Lab Technician' },
  { value: 'PROCUREMENT', label: 'Procurement Officer' },
  { value: 'ACCOUNTANT', label: 'Accountant' },
  { value: 'INSURANCE', label: 'Claims Officer' },
  { value: 'HR', label: 'HR Officer' },
]

const INITIAL_FORM = {
  username: '', first_name: '', last_name: '', email: '',
  phone_number: '', user_type: 'RECEPTIONIST',
  password: '', confirm_password: '', specialization: '', license_number: ''
}

export default function AdminUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState(INITIAL_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await userApi.list({ search, user_type: filterType })
      setUsers(data.results || data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search, filterType])

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await userApi.create(form)
      setSuccess('User created successfully!')
      setShowModal(false)
      setForm(INITIAL_FORM)
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { label: 'User', render: (r) => (
      <div className="d-flex align-items-center gap-2">
        <div className="avatar sm" style={{ background: r.is_active ? 'var(--mc-blue)' : 'var(--mc-gray-400)' }}>
          {r.first_name?.[0]}{r.last_name?.[0]}
        </div>
        <div>
          <div className="fw-600">{r.full_name}</div>
          <div className="text-muted-sm">@{r.username}</div>
        </div>
      </div>
    )},
    { label: 'Role', render: (r) => (
      <span className="mc-badge blue">{r.user_type}</span>
    )},
    { label: 'Email', key: 'email' },
    { label: 'Phone', key: 'phone_number' },
    { label: 'Status', render: (r) => (
      <StatusBadge status={r.is_active ? 'ACTIVE' : 'CANCELLED'} />
    )},
  ]

  return (
    <div className="slide-up">
      <PageHeader title="Staff Management" subtitle="Manage system users and roles">
        <button className="btn-mc-primary" onClick={() => setShowModal(true)}>
          <i className="bi bi-person-plus"></i> Add User
        </button>
      </PageHeader>

      {success && <Alert type="success" onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Filters */}
      <div className="mc-card mb-3">
        <div className="filter-bar">
          <SearchInput value={search} onChange={setSearch} placeholder="Search users..." />
          <select
            className="mc-select"
            style={{ maxWidth: 200 }}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Roles</option>
            {USER_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <DataTable
          columns={columns}
          data={users}
          loading={loading}
          emptyTitle="No users found"
          emptyIcon="bi-people"
        />
      </div>

      {/* Create Modal */}
      <Modal
        show={showModal}
        onClose={() => { setShowModal(false); setError('') }}
        title="Create New User"
        size="lg"
        footer={
          <>
            <button className="btn-mc-secondary" onClick={() => setShowModal(false)}>Cancel</button>
            <button className="btn-mc-primary" onClick={handleCreate} disabled={saving}>
              {saving ? <span className="spinner-border spinner-border-sm me-1"></span> : null}
              Create User
            </button>
          </>
        }
      >
        {error && <Alert type="danger">{error}</Alert>}
        <form onSubmit={handleCreate}>
          <div className="row g-3">
            <div className="col-md-6">
              <label className="mc-label">First Name *</label>
              <input className="mc-input" required value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="mc-label">Last Name *</label>
              <input className="mc-input" required value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="mc-label">Username *</label>
              <input className="mc-input" required value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="mc-label">Email</label>
              <input type="email" className="mc-input" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="mc-label">Phone Number</label>
              <input className="mc-input" value={form.phone_number}
                onChange={(e) => setForm({ ...form, phone_number: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="mc-label">Role *</label>
              <select className="mc-select" value={form.user_type}
                onChange={(e) => setForm({ ...form, user_type: e.target.value })}>
                {USER_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            {['DOCTOR'].includes(form.user_type) && (
              <>
                <div className="col-md-6">
                  <label className="mc-label">Specialization</label>
                  <input className="mc-input" value={form.specialization}
                    onChange={(e) => setForm({ ...form, specialization: e.target.value })} />
                </div>
                <div className="col-md-6">
                  <label className="mc-label">License Number</label>
                  <input className="mc-input" value={form.license_number}
                    onChange={(e) => setForm({ ...form, license_number: e.target.value })} />
                </div>
              </>
            )}
            <div className="col-md-6">
              <label className="mc-label">Password *</label>
              <input type="password" className="mc-input" required value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="mc-label">Confirm Password *</label>
              <input type="password" className="mc-input" required value={form.confirm_password}
                onChange={(e) => setForm({ ...form, confirm_password: e.target.value })} />
            </div>
          </div>
        </form>
      </Modal>
    </div>
  )
}