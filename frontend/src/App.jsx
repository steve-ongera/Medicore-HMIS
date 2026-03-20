import React, { useState, useEffect, createContext, useContext } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import Layout from './components/layout/Layout.jsx'
import Login from './pages/Login.jsx'

// Admin Pages
import AdminDashboard from './pages/admin/Dashboard.jsx'
import AdminUsers from './pages/admin/Users.jsx'
import AdminSettings from './pages/admin/Settings.jsx'

// Receptionist Pages
import ReceptionDashboard from './pages/receptionist/Dashboard.jsx'
import ReceptionPatients from './pages/receptionist/Patients.jsx'
import ReceptionVisits from './pages/receptionist/Visits.jsx'
import ReceptionQueue from './pages/receptionist/Queue.jsx'
import ReceptionAppointments from './pages/receptionist/Appointments.jsx'

// Nurse Pages
import NurseDashboard from './pages/nurse/Dashboard.jsx'
import NurseTriage from './pages/nurse/Triage.jsx'
import NurseVitals from './pages/nurse/Vitals.jsx'
import NurseInpatient from './pages/nurse/Inpatient.jsx'

// Doctor Pages
import DoctorDashboard from './pages/doctor/Dashboard.jsx'
import DoctorConsultation from './pages/doctor/Consultation.jsx'
import DoctorPatients from './pages/doctor/Patients.jsx'
import DoctorLabOrders from './pages/doctor/LabOrders.jsx'
import DoctorImaging from './pages/doctor/Imaging.jsx'

// Pharmacy Pages
import PharmacyDashboard from './pages/pharmacy/Dashboard.jsx'
import PharmacyDispense from './pages/pharmacy/Dispense.jsx'
import PharmacyStock from './pages/pharmacy/Stock.jsx'
import PharmacyOTC from './pages/pharmacy/OTC.jsx'
import PharmacyInpatientRequests from './pages/pharmacy/InpatientRequests.jsx'

// Cashier Pages
import CashierDashboard from './pages/cashier/Dashboard.jsx'
import CashierPayments from './pages/cashier/Payments.jsx'
import CashierReports from './pages/cashier/Reports.jsx'

// Lab Pages
import LabDashboard from './pages/lab/Dashboard.jsx'
import LabOrders from './pages/lab/Orders.jsx'
import LabResults from './pages/lab/Results.jsx'

// Radiology Pages
import RadiologyDashboard from './pages/radiology/Dashboard.jsx'
import RadiologyStudies from './pages/radiology/Studies.jsx'

// Auth Context
export const AuthContext = createContext(null)

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

// Role → Default Route Map
const ROLE_HOME = {
  ADMIN: '/admin/dashboard',
  RECEPTIONIST: '/reception/dashboard',
  NURSE: '/nurse/dashboard',
  DOCTOR: '/doctor/dashboard',
  PHARMACIST: '/pharmacy/dashboard',
  CASHIER: '/cashier/dashboard',
  LAB_TECH: '/lab/dashboard',
  PROCUREMENT: '/admin/dashboard',
  ACCOUNTANT: '/cashier/dashboard',
  INSURANCE: '/cashier/dashboard',
  HR: '/admin/dashboard',
}

function RequireAuth({ children, allowedRoles }) {
  const { user, token } = useAuth()
  const location = useLocation()

  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.user_type)) {
    const home = ROLE_HOME[user.user_type] || '/login'
    return <Navigate to={home} replace />
  }

  return children
}

export default function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('medicore_token'))
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const storedUser = localStorage.getItem('medicore_user')
    const storedToken = localStorage.getItem('medicore_token')
    if (storedUser && storedToken) {
      setUser(JSON.parse(storedUser))
      setToken(storedToken)
    }
    setLoading(false)
  }, [])

  const login = (userData, accessToken, refreshToken) => {
    setUser(userData)
    setToken(accessToken)
    localStorage.setItem('medicore_token', accessToken)
    localStorage.setItem('medicore_refresh', refreshToken)
    localStorage.setItem('medicore_user', JSON.stringify(userData))
    const home = ROLE_HOME[userData.user_type] || '/login'
    navigate(home)
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('medicore_token')
    localStorage.removeItem('medicore_refresh')
    localStorage.removeItem('medicore_user')
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center vh-100">
        <div className="text-center">
          <div className="spinner-pulse mb-3"></div>
          <p className="text-muted">Loading MediCore...</p>
        </div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          token && user
            ? <Navigate to={ROLE_HOME[user.user_type] || '/login'} replace />
            : <Navigate to="/login" replace />
        } />

        {/* Admin Routes */}
        <Route path="/admin/*" element={
          <RequireAuth allowedRoles={['ADMIN', 'HR', 'PROCUREMENT']}>
            <Layout role="admin">
              <Routes>
                <Route path="dashboard" element={<AdminDashboard />} />
                <Route path="users" element={<AdminUsers />} />
                <Route path="settings" element={<AdminSettings />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Reception Routes */}
        <Route path="/reception/*" element={
          <RequireAuth allowedRoles={['RECEPTIONIST', 'ADMIN']}>
            <Layout role="reception">
              <Routes>
                <Route path="dashboard" element={<ReceptionDashboard />} />
                <Route path="patients" element={<ReceptionPatients />} />
                <Route path="visits" element={<ReceptionVisits />} />
                <Route path="queue" element={<ReceptionQueue />} />
                <Route path="appointments" element={<ReceptionAppointments />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Nurse Routes */}
        <Route path="/nurse/*" element={
          <RequireAuth allowedRoles={['NURSE', 'ADMIN']}>
            <Layout role="nurse">
              <Routes>
                <Route path="dashboard" element={<NurseDashboard />} />
                <Route path="triage" element={<NurseTriage />} />
                <Route path="vitals" element={<NurseVitals />} />
                <Route path="inpatient" element={<NurseInpatient />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Doctor Routes */}
        <Route path="/doctor/*" element={
          <RequireAuth allowedRoles={['DOCTOR', 'ADMIN']}>
            <Layout role="doctor">
              <Routes>
                <Route path="dashboard" element={<DoctorDashboard />} />
                <Route path="consultation" element={<DoctorConsultation />} />
                <Route path="patients" element={<DoctorPatients />} />
                <Route path="lab-orders" element={<DoctorLabOrders />} />
                <Route path="imaging" element={<DoctorImaging />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Pharmacy Routes */}
        <Route path="/pharmacy/*" element={
          <RequireAuth allowedRoles={['PHARMACIST', 'ADMIN']}>
            <Layout role="pharmacy">
              <Routes>
                <Route path="dashboard" element={<PharmacyDashboard />} />
                <Route path="dispense" element={<PharmacyDispense />} />
                <Route path="stock" element={<PharmacyStock />} />
                <Route path="otc" element={<PharmacyOTC />} />
                <Route path="inpatient-requests" element={<PharmacyInpatientRequests />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Cashier Routes */}
        <Route path="/cashier/*" element={
          <RequireAuth allowedRoles={['CASHIER', 'ACCOUNTANT', 'INSURANCE', 'ADMIN']}>
            <Layout role="cashier">
              <Routes>
                <Route path="dashboard" element={<CashierDashboard />} />
                <Route path="payments" element={<CashierPayments />} />
                <Route path="reports" element={<CashierReports />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Lab Routes */}
        <Route path="/lab/*" element={
          <RequireAuth allowedRoles={['LAB_TECH', 'ADMIN']}>
            <Layout role="lab">
              <Routes>
                <Route path="dashboard" element={<LabDashboard />} />
                <Route path="orders" element={<LabOrders />} />
                <Route path="results" element={<LabResults />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Radiology Routes */}
        <Route path="/radiology/*" element={
          <RequireAuth allowedRoles={['LAB_TECH', 'ADMIN', 'DOCTOR']}>
            <Layout role="radiology">
              <Routes>
                <Route path="dashboard" element={<RadiologyDashboard />} />
                <Route path="studies" element={<RadiologyStudies />} />
                <Route path="*" element={<Navigate to="dashboard" replace />} />
              </Routes>
            </Layout>
          </RequireAuth>
        } />

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthContext.Provider>
  )
}