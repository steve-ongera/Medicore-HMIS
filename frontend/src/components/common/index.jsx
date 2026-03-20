/**
 * MediCore HMS — Common Reusable Components
 */
import React, { useState, useEffect, useRef } from 'react'

// ─── Stat Card ─────────────────────────────────────────────────
export function StatCard({ icon, label, value, color = 'blue', change, loading }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>
        <i className={`bi ${icon}`}></i>
      </div>
      <div className="stat-info">
        {loading ? (
          <div className="placeholder-glow">
            <span className="placeholder col-6"></span>
          </div>
        ) : (
          <div className="stat-value">{value ?? '—'}</div>
        )}
        <div className="stat-label">{label}</div>
        {change && (
          <div className={`stat-change ${change > 0 ? 'up' : 'down'}`}>
            <i className={`bi bi-arrow-${change > 0 ? 'up' : 'down'}`}></i>
            {Math.abs(change)}% today
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Loading Spinner ───────────────────────────────────────────
export function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="loading-spinner">
      <i className="bi bi-arrow-clockwise"></i>
      <span>{text}</span>
    </div>
  )
}

// ─── Empty State ───────────────────────────────────────────────
export function EmptyState({ icon = 'bi-inbox', title = 'No data', description, action }) {
  return (
    <div className="empty-state">
      <i className={`bi ${icon}`}></i>
      <h6>{title}</h6>
      {description && <p className="mb-2">{description}</p>}
      {action && action}
    </div>
  )
}

// ─── Badge ─────────────────────────────────────────────────────
export function Badge({ color = 'gray', children, dot }) {
  return (
    <span className={`mc-badge ${color}`}>
      {dot && <span className={`status-dot ${color}`}></span>}
      {children}
    </span>
  )
}

// ─── Alert ─────────────────────────────────────────────────────
export function Alert({ type = 'info', children, onClose }) {
  const icons = {
    info: 'bi-info-circle-fill',
    success: 'bi-check-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    danger: 'bi-x-circle-fill',
  }
  return (
    <div className={`mc-alert ${type}`}>
      <i className={`bi ${icons[type]} flex-shrink-0`}></i>
      <span className="flex-1">{children}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="btn p-0 border-0 ms-auto"
          style={{ color: 'inherit', fontSize: '0.9rem' }}
        >
          <i className="bi bi-x"></i>
        </button>
      )}
    </div>
  )
}

// ─── Modal ─────────────────────────────────────────────────────
export function Modal({ show, onClose, title, children, footer, size = '' }) {
  useEffect(() => {
    if (show) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [show])

  if (!show) return null

  return (
    <div className="mc-modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`mc-modal ${size}`}>
        <div className="mc-modal-header">
          <h5 className="mc-modal-title">{title}</h5>
          <button className="btn-close-mc" onClick={onClose}>
            <i className="bi bi-x"></i>
          </button>
        </div>
        <div className="mc-modal-body">{children}</div>
        {footer && <div className="mc-modal-footer">{footer}</div>}
      </div>
    </div>
  )
}

// ─── Confirm Dialog ────────────────────────────────────────────
export function ConfirmModal({ show, onClose, onConfirm, title, message, confirmLabel = 'Confirm', danger = false }) {
  return (
    <Modal
      show={show}
      onClose={onClose}
      title={title || 'Confirm Action'}
      footer={
        <>
          <button className="btn-mc-secondary" onClick={onClose}>Cancel</button>
          <button
            className={danger ? 'btn-mc-danger' : 'btn-mc-primary'}
            onClick={() => { onConfirm(); onClose(); }}
          >
            {confirmLabel}
          </button>
        </>
      }
    >
      <p className="mb-0 text-muted">{message}</p>
    </Modal>
  )
}

// ─── Search Input ──────────────────────────────────────────────
export function SearchInput({ value, onChange, placeholder = 'Search...', onEnter }) {
  return (
    <div className="search-bar">
      <i className="bi bi-search search-icon"></i>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        onKeyDown={(e) => e.key === 'Enter' && onEnter?.()}
      />
      {value && (
        <button
          onClick={() => onChange('')}
          style={{
            position: 'absolute', right: '0.6rem', top: '50%',
            transform: 'translateY(-50%)', border: 'none', background: 'none',
            color: 'var(--mc-gray-400)', cursor: 'pointer', fontSize: '0.9rem'
          }}
        >
          <i className="bi bi-x"></i>
        </button>
      )}
    </div>
  )
}

// ─── Page Header ───────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions, children }) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      <div className="d-flex align-items-center gap-2 flex-wrap">
        {children}
        {actions}
      </div>
    </div>
  )
}

// ─── Data Table ────────────────────────────────────────────────
export function DataTable({ columns, data, loading, onRowClick, emptyTitle, emptyIcon }) {
  if (loading) return <LoadingSpinner />

  return (
    <div className="mc-table-wrapper">
      <table className="mc-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key || col.label} style={col.style}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>
                <EmptyState
                  icon={emptyIcon || 'bi-inbox'}
                  title={emptyTitle || 'No records found'}
                />
              </td>
            </tr>
          ) : (
            data.map((row, idx) => (
              <tr
                key={row.id || idx}
                onClick={() => onRowClick?.(row)}
                style={onRowClick ? { cursor: 'pointer' } : {}}
              >
                {columns.map((col) => (
                  <td key={col.key || col.label}>
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

// ─── Patient Badge ─────────────────────────────────────────────
export function PatientChip({ patient }) {
  if (!patient) return null
  const initials = `${patient.first_name?.[0] || ''}${patient.last_name?.[0] || ''}`.toUpperCase()
  return (
    <div className="patient-chip">
      <div className="avatar sm">{initials}</div>
      <div>
        <div className="patient-chip-name">{patient.first_name} {patient.last_name}</div>
        <div className="patient-chip-id">ID: {patient.id_number}</div>
      </div>
    </div>
  )
}

// ─── Vital Box ─────────────────────────────────────────────────
export function VitalBox({ label, value, unit, critical }) {
  return (
    <div className={`vital-box ${critical ? 'critical' : ''}`}>
      <div className="vital-value">{value ?? '—'}</div>
      {unit && <div className="vital-unit">{unit}</div>}
      <div className="vital-label">{label}</div>
    </div>
  )
}

// ─── Triage Badge ──────────────────────────────────────────────
export function TriageBadge({ color }) {
  const labels = {
    RED: 'Emergency', ORANGE: 'Very Urgent',
    YELLOW: 'Urgent', GREEN: 'Standard', BLUE: 'Non-Urgent'
  }
  return (
    <span className={`mc-badge badge-triage-${color}`}>
      ● {labels[color] || color}
    </span>
  )
}

// ─── Status Badge ──────────────────────────────────────────────
export function StatusBadge({ status }) {
  const config = {
    PENDING: { color: 'orange', label: 'Pending' },
    APPROVED: { color: 'green', label: 'Approved' },
    REJECTED: { color: 'red', label: 'Rejected' },
    PAID: { color: 'blue', label: 'Paid' },
    COMPLETED: { color: 'green', label: 'Completed' },
    ACTIVE: { color: 'green', label: 'Active' },
    CANCELLED: { color: 'red', label: 'Cancelled' },
    IN_PROGRESS: { color: 'blue', label: 'In Progress' },
    DISPENSED: { color: 'teal', label: 'Dispensed' },
    SCHEDULED: { color: 'blue', label: 'Scheduled' },
    SUBMITTED: { color: 'orange', label: 'Submitted' },
    REPORTED: { color: 'purple', label: 'Reported' },
    REGISTERED: { color: 'gray', label: 'Registered' },
    TRIAGED: { color: 'orange', label: 'Triaged' },
    WAITING: { color: 'blue', label: 'Waiting' },
    DISCHARGED: { color: 'gray', label: 'Discharged' },
  }
  const { color, label } = config[status] || { color: 'gray', label: status }
  return <span className={`mc-badge ${color}`}>{label}</span>
}

// ─── Tabs ──────────────────────────────────────────────────────
export function Tabs({ tabs, active, onChange }) {
  return (
    <div className="mc-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={`mc-tab ${active === tab.key ? 'active' : ''}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.icon && <i className={`bi ${tab.icon}`}></i>}
          {tab.label}
          {tab.count !== undefined && (
            <span
              className="ms-1 rounded-circle px-1"
              style={{
                background: active === tab.key ? 'var(--mc-blue)' : 'var(--mc-gray-200)',
                color: active === tab.key ? 'white' : 'var(--mc-gray-600)',
                fontSize: '0.65rem',
                fontWeight: 700,
                minWidth: 18,
                textAlign: 'center'
              }}
            >
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}

// ─── Toast Notification ────────────────────────────────────────
let toastCallback = null

export function useToast() {
  const [toasts, setToasts] = useState([])

  const show = (message, type = 'success') => {
    const id = Date.now()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 3500)
  }

  return { toasts, show }
}

export function ToastContainer({ toasts }) {
  if (!toasts.length) return null
  return (
    <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {toasts.map((t) => (
        <div
          key={t.id}
          className="mc-alert slide-up mb-0"
          style={{ boxShadow: 'var(--shadow-lg)', minWidth: 240 }}
        >
          <i className={`bi ${t.type === 'success' ? 'bi-check-circle-fill' : t.type === 'danger' ? 'bi-x-circle-fill' : 'bi-info-circle-fill'}`}></i>
          {t.message}
        </div>
      ))}
    </div>
  )
}

// ─── Form Row ──────────────────────────────────────────────────
export function FormRow({ children, cols = 2 }) {
  return (
    <div className={`row g-3`}>
      {React.Children.map(children, (child) => (
        <div className={`col-md-${12 / cols}`}>{child}</div>
      ))}
    </div>
  )
}

// ─── Section Card ──────────────────────────────────────────────
export function SectionCard({ title, icon, actions, children, loading }) {
  return (
    <div className="mc-card mb-3">
      <div className="mc-card-header">
        {icon && <i className={`bi ${icon} text-blue`}></i>}
        <h6 className="mc-card-title">{title}</h6>
        {actions && <div className="ms-auto d-flex gap-2">{actions}</div>}
      </div>
      <div className="mc-card-body">
        {loading ? <LoadingSpinner /> : children}
      </div>
    </div>
  )
}