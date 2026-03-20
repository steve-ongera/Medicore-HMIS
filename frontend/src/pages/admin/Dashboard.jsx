import React, { useState, useEffect } from 'react'
import { dashboardApi, userApi } from '../../services/api.js'
import { StatCard, LoadingSpinner, SectionCard, DataTable, StatusBadge, PageHeader } from '../../components/common/index.jsx'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      dashboardApi.stats(),
      userApi.list(),
    ]).then(([s, u]) => {
      setStats(s.data)
      setUsers(u.data.results || u.data)
    }).finally(() => setLoading(false))
  }, [])

  const userTypeColors = {
    ADMIN: 'red', DOCTOR: 'blue', NURSE: 'teal',
    RECEPTIONIST: 'green', PHARMACIST: 'purple',
    CASHIER: 'orange', LAB_TECH: 'blue', HR: 'gray',
  }

  const userColumns = [
    { label: 'Name', render: (r) => (
      <div className="d-flex align-items-center gap-2">
        <div className="avatar sm">{r.first_name?.[0]}{r.last_name?.[0]}</div>
        <div>
          <div className="fw-600">{r.full_name}</div>
          <div className="text-muted-sm">{r.username}</div>
        </div>
      </div>
    )},
    { label: 'Role', render: (r) => (
      <span className={`mc-badge ${userTypeColors[r.user_type] || 'gray'}`}>{r.user_type}</span>
    )},
    { label: 'Email', key: 'email' },
    { label: 'Status', render: (r) => (
      <StatusBadge status={r.is_active ? 'ACTIVE' : 'CANCELLED'} />
    )},
  ]

  return (
    <div className="slide-up">
      <PageHeader
        title="System Dashboard"
        subtitle="Hospital overview and key metrics"
      />

      {/* Stats Grid */}
      <div className="row g-3 mb-4">
        {[
          { icon: 'bi-people-fill', label: 'Total Patients', value: stats?.total_patients, color: 'blue' },
          { icon: 'bi-door-open-fill', label: "Today's Visits", value: stats?.today_visits, color: 'teal' },
          { icon: 'bi-hospital-fill', label: 'Active Admissions', value: stats?.active_admissions, color: 'purple' },
          { icon: 'bi-bed-fill', label: 'Available Beds', value: stats?.available_beds, color: 'green' },
          { icon: 'bi-cash-coin', label: 'Today Revenue', value: stats ? `KSh ${Number(stats.today_revenue).toLocaleString()}` : null, color: 'orange' },
          { icon: 'bi-eyedropper', label: 'Pending Lab', value: stats?.pending_lab_orders, color: 'red' },
          { icon: 'bi-capsule', label: 'Low Stock Items', value: stats?.low_stock_medicines, color: 'orange' },
          { icon: 'bi-shield-check', label: 'Pending Claims', value: stats?.pending_claims, color: 'blue' },
        ].map((s) => (
          <div key={s.label} className="col-6 col-md-4 col-xl-3">
            <StatCard {...s} loading={loading} />
          </div>
        ))}
      </div>

      {/* Staff List */}
      <SectionCard
        title="Staff Users"
        icon="bi-people"
        actions={
          <a href="/admin/users" className="btn-mc-primary" style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}>
            <i className="bi bi-plus"></i> Add User
          </a>
        }
        loading={loading}
      >
        <DataTable
          columns={userColumns}
          data={users.slice(0, 10)}
          emptyTitle="No users found"
          emptyIcon="bi-people"
        />
      </SectionCard>
    </div>
  )
}