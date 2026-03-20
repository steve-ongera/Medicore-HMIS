import React, { useState } from 'react'
import { useAuth } from '../App.jsx'
import { authApi } from '../services/api.js'

export default function Login() {
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPass, setShowPass] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await authApi.login(form)
      login(data.user, data.access, data.refresh)
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card slide-up">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">
            <i className="bi bi-plus-circle-fill text-white fs-3"></i>
          </div>
          <h1 className="login-title">MediCore HMS</h1>
          <p className="login-subtitle">Hospital Management System</p>
        </div>

        {/* Error */}
        {error && (
          <div className="mc-alert danger mb-3">
            <i className="bi bi-exclamation-circle-fill"></i>
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="mc-label">Username</label>
            <div className="position-relative">
              <input
                type="text"
                className="mc-input"
                placeholder="Enter your username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
                autoFocus
                style={{ paddingLeft: '2.25rem' }}
              />
              <i
                className="bi bi-person position-absolute"
                style={{ left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--mc-gray-400)' }}
              ></i>
            </div>
          </div>

          <div className="form-group">
            <label className="mc-label">Password</label>
            <div className="position-relative">
              <input
                type={showPass ? 'text' : 'password'}
                className="mc-input"
                placeholder="Enter your password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                style={{ paddingLeft: '2.25rem', paddingRight: '2.5rem' }}
              />
              <i
                className="bi bi-lock position-absolute"
                style={{ left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--mc-gray-400)' }}
              ></i>
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                className="position-absolute btn p-0 border-0"
                style={{ right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--mc-gray-400)' }}
              >
                <i className={`bi ${showPass ? 'bi-eye-slash' : 'bi-eye'}`}></i>
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn-mc-primary w-100 justify-content-center mt-1"
            style={{ padding: '0.65rem', fontSize: '0.9rem' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2"></span>
                Signing in...
              </>
            ) : (
              <>
                <i className="bi bi-box-arrow-in-right"></i>
                Sign In
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center mt-3">
          <small className="text-muted">
            <i className="bi bi-shield-check me-1"></i>
            Secure Hospital Information System
          </small>
        </div>

        {/* Demo credentials hint */}
        <div className="mc-alert info mt-3 mb-0" style={{ fontSize: '0.72rem' }}>
          <i className="bi bi-info-circle-fill flex-shrink-0"></i>
          <span>Contact your system administrator for login credentials.</span>
        </div>
      </div>
    </div>
  )
}