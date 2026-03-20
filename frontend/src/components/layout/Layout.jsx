import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../App.jsx'

// Role-based navigation config
const NAV_CONFIG = {
  admin: [
    { section: 'Main', items: [
      { to: '/admin/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/admin/users', icon: 'bi-people', label: 'Staff Users' },
      { to: '/admin/settings', icon: 'bi-gear', label: 'Settings' },
    ]},
  ],
  reception: [
    { section: 'Main', items: [
      { to: '/reception/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/reception/visits', icon: 'bi-door-open', label: 'Register Visit' },
      { to: '/reception/patients', icon: 'bi-person-lines-fill', label: 'Patients' },
      { to: '/reception/queue', icon: 'bi-list-ol', label: 'Queue' },
      { to: '/reception/appointments', icon: 'bi-calendar-check', label: 'Appointments' },
    ]},
  ],
  nurse: [
    { section: 'Main', items: [
      { to: '/nurse/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/nurse/triage', icon: 'bi-heart-pulse', label: 'Triage' },
      { to: '/nurse/vitals', icon: 'bi-activity', label: 'Vitals' },
      { to: '/nurse/inpatient', icon: 'bi-hospital', label: 'Inpatient' },
    ]},
  ],
  doctor: [
    { section: 'Main', items: [
      { to: '/doctor/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/doctor/consultation', icon: 'bi-clipboard2-pulse', label: 'Consultations' },
      { to: '/doctor/patients', icon: 'bi-person-lines-fill', label: 'Patients' },
    ]},
    { section: 'Orders', items: [
      { to: '/doctor/lab-orders', icon: 'bi-eyedropper', label: 'Lab Orders' },
      { to: '/doctor/imaging', icon: 'bi-radioactive', label: 'Imaging' },
    ]},
  ],
  pharmacy: [
    { section: 'Main', items: [
      { to: '/pharmacy/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/pharmacy/dispense', icon: 'bi-capsule', label: 'Dispense Rx' },
      { to: '/pharmacy/otc', icon: 'bi-cart3', label: 'OTC Sales' },
      { to: '/pharmacy/inpatient-requests', icon: 'bi-hospital', label: 'Inpatient Requests' },
    ]},
    { section: 'Inventory', items: [
      { to: '/pharmacy/stock', icon: 'bi-box-seam', label: 'Stock Management' },
    ]},
  ],
  cashier: [
    { section: 'Main', items: [
      { to: '/cashier/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/cashier/payments', icon: 'bi-cash-coin', label: 'Payments' },
      { to: '/cashier/reports', icon: 'bi-bar-chart-line', label: 'Reports' },
    ]},
  ],
  lab: [
    { section: 'Main', items: [
      { to: '/lab/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/lab/orders', icon: 'bi-clipboard2-data', label: 'Lab Orders' },
      { to: '/lab/results', icon: 'bi-file-earmark-medical', label: 'Results' },
    ]},
  ],
  radiology: [
    { section: 'Main', items: [
      { to: '/radiology/dashboard', icon: 'bi-speedometer2', label: 'Dashboard' },
      { to: '/radiology/studies', icon: 'bi-image', label: 'Imaging Studies' },
    ]},
  ],
}

const ROLE_LABELS = {
  ADMIN: 'Administrator',
  RECEPTIONIST: 'Receptionist',
  NURSE: 'Nurse',
  DOCTOR: 'Doctor',
  PHARMACIST: 'Pharmacist',
  CASHIER: 'Cashier',
  LAB_TECH: 'Lab Technician',
  PROCUREMENT: 'Procurement',
  ACCOUNTANT: 'Accountant',
  INSURANCE: 'Claims Officer',
  HR: 'HR Officer',
}

function Sidebar({ role, mobileOpen, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const navGroups = NAV_CONFIG[role] || NAV_CONFIG.admin

  const initials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || user.username?.[0]?.toUpperCase()
    : 'U'

  return (
    <>
      {mobileOpen && (
        <div
          className="position-fixed inset-0 bg-dark bg-opacity-50"
          style={{ zIndex: 999 }}
          onClick={onClose}
        />
      )}
      <aside className={`app-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <i className="bi bi-plus-circle-fill"></i>
          </div>
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-name">MediCore</span>
            <span className="sidebar-logo-sub">HMS v2.0</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          {navGroups.map((group) => (
            <div key={group.section}>
              <div className="sidebar-section-title">{group.section}</div>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `sidebar-link ${isActive ? 'active' : ''}`
                  }
                  onClick={mobileOpen ? onClose : undefined}
                >
                  <i className={`bi ${item.icon} sidebar-link-icon`}></i>
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="sidebar-badge">{item.badge}</span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* User Footer */}
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">
              {user?.first_name} {user?.last_name}
            </div>
            <div className="sidebar-user-role">
              {ROLE_LABELS[user?.user_type] || user?.user_type}
            </div>
          </div>
          <button
            className="topbar-icon-btn ms-1"
            onClick={logout}
            title="Logout"
            style={{ color: '#ef4444' }}
          >
            <i className="bi bi-box-arrow-right"></i>
          </button>
        </div>
      </aside>
    </>
  )
}

function Topbar({ title, onMenuToggle }) {
  const { user } = useAuth()
  const [showNotif, setShowNotif] = useState(false)

  return (
    <header className="app-topbar">
      <button
        className="topbar-icon-btn d-md-none"
        onClick={onMenuToggle}
      >
        <i className="bi bi-list"></i>
      </button>
      <div className="topbar-title">{title}</div>
      <div className="topbar-actions">
        <button
          className="topbar-icon-btn"
          onClick={() => setShowNotif(!showNotif)}
          title="Notifications"
        >
          <i className="bi bi-bell"></i>
          <span className="topbar-notif-badge"></span>
        </button>
        <button className="topbar-icon-btn" title="Help">
          <i className="bi bi-question-circle"></i>
        </button>
        <div
          className="avatar sm cursor-pointer"
          title={`${user?.first_name} ${user?.last_name}`}
          style={{ cursor: 'pointer' }}
        >
          {user?.first_name?.[0]}{user?.last_name?.[0]}
        </div>
      </div>
    </header>
  )
}

// Map paths to page titles
function usePageTitle() {
  const titles = {
    dashboard: 'Dashboard',
    patients: 'Patient Records',
    visits: 'Register Visit',
    queue: 'Patient Queue',
    appointments: 'Appointments',
    triage: 'Triage Assessment',
    vitals: 'Patient Vitals',
    inpatient: 'Inpatient Management',
    consultation: 'Consultations',
    'lab-orders': 'Lab Orders',
    imaging: 'Imaging & Radiology',
    dispense: 'Dispense Prescriptions',
    stock: 'Stock Management',
    otc: 'OTC Sales',
    'inpatient-requests': 'Inpatient Medicine Requests',
    payments: 'Payments',
    reports: 'Financial Reports',
    orders: 'Lab Orders',
    results: 'Lab Results',
    studies: 'Imaging Studies',
    users: 'User Management',
    settings: 'System Settings',
  }
  const path = window.location.pathname.split('/').pop()
  return titles[path] || 'MediCore HMS'
}

export default function Layout({ children, role }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const title = usePageTitle()

  return (
    <div className="app-shell">
      <Sidebar
        role={role}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />
      <main className="app-main">
        <Topbar
          title={title}
          onMenuToggle={() => setMobileOpen(!mobileOpen)}
        />
        <div className="app-content fade-in">
          {children}
        </div>
      </main>
    </div>
  )
}