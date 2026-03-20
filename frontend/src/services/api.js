/**
 * MediCore HMS - API Service Layer
 * Centralized axios instance with JWT auth + auto-refresh
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// ─── Axios Instance ────────────────────────────────────────────
const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// ─── Request Interceptor (attach token) ───────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('medicore_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─── Response Interceptor (auto refresh) ──────────────────────
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }
      originalRequest._retry = true
      isRefreshing = true
      const refreshToken = localStorage.getItem('medicore_refresh')
      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh: refreshToken })
        localStorage.setItem('medicore_token', data.access)
        api.defaults.headers.common.Authorization = `Bearer ${data.access}`
        processQueue(null, data.access)
        return api(originalRequest)
      } catch (err) {
        processQueue(err, null)
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

// ─── Helper ───────────────────────────────────────────────────
const handleError = (error) => {
  const msg =
    error.response?.data?.detail ||
    error.response?.data?.error ||
    Object.values(error.response?.data || {})[0]?.[0] ||
    error.message ||
    'Something went wrong'
  throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
}

// ─── Auth ─────────────────────────────────────────────────────
export const authApi = {
  login: (data) => api.post('/auth/login/', data).catch(handleError),
  logout: (refresh) => api.post('/auth/logout/', { refresh }).catch(handleError),
  me: () => api.get('/auth/me/').catch(handleError),
  changePassword: (data) => api.post('/auth/change_password/', data).catch(handleError),
}

// ─── Dashboard ────────────────────────────────────────────────
export const dashboardApi = {
  stats: () => api.get('/dashboard/stats/').catch(handleError),
  recentActivity: () => api.get('/dashboard/recent_activity/').catch(handleError),
  revenueChart: (days = 7) => api.get(`/dashboard/revenue_chart/?days=${days}`).catch(handleError),
  insuranceSummary: () => api.get('/dashboard/insurance_summary/').catch(handleError),
}

// ─── Patients ─────────────────────────────────────────────────
export const patientApi = {
  list: (params = {}) => api.get('/patients/', { params }).catch(handleError),
  get: (id) => api.get(`/patients/${id}/`).catch(handleError),
  create: (data) => api.post('/patients/', data).catch(handleError),
  update: (id, data) => api.patch(`/patients/${id}/`, data).catch(handleError),
  delete: (id) => api.delete(`/patients/${id}/`).catch(handleError),
  medicalHistory: (id) => api.get(`/patients/${id}/medical_history/`).catch(handleError),
  visits: (id) => api.get(`/patients/${id}/visits/`).catch(handleError),
  prescriptions: (id) => api.get(`/patients/${id}/prescriptions/`).catch(handleError),
  search: (q) => api.get('/patients/', { params: { search: q } }).catch(handleError),
}

// ─── Users ────────────────────────────────────────────────────
export const userApi = {
  list: (params = {}) => api.get('/users/', { params }).catch(handleError),
  get: (id) => api.get(`/users/${id}/`).catch(handleError),
  create: (data) => api.post('/users/', data).catch(handleError),
  update: (id, data) => api.patch(`/users/${id}/`, data).catch(handleError),
  delete: (id) => api.delete(`/users/${id}/`).catch(handleError),
  byType: (type) => api.get('/users/', { params: { user_type: type } }).catch(handleError),
}

// ─── Doctors & Nurses ─────────────────────────────────────────
export const doctorApi = {
  list: (params = {}) => api.get('/doctors/', { params }).catch(handleError),
  get: (id) => api.get(`/doctors/${id}/`).catch(handleError),
  create: (data) => api.post('/doctors/', data).catch(handleError),
  update: (id, data) => api.patch(`/doctors/${id}/`, data).catch(handleError),
}

export const nurseApi = {
  list: (params = {}) => api.get('/nurses/', { params }).catch(handleError),
  get: (id) => api.get(`/nurses/${id}/`).catch(handleError),
  create: (data) => api.post('/nurses/', data).catch(handleError),
}

// ─── Appointments ─────────────────────────────────────────────
export const appointmentApi = {
  list: (params = {}) => api.get('/appointments/', { params }).catch(handleError),
  today: () => api.get('/appointments/today/').catch(handleError),
  get: (id) => api.get(`/appointments/${id}/`).catch(handleError),
  create: (data) => api.post('/appointments/', data).catch(handleError),
  update: (id, data) => api.patch(`/appointments/${id}/`, data).catch(handleError),
  cancel: (id) => api.patch(`/appointments/${id}/`, { status: 'CANCELLED' }).catch(handleError),
}

// ─── Consultations ────────────────────────────────────────────
export const consultationApi = {
  list: (params = {}) => api.get('/consultations/', { params }).catch(handleError),
  get: (id) => api.get(`/consultations/${id}/`).catch(handleError),
  create: (data) => api.post('/consultations/', data).catch(handleError),
  update: (id, data) => api.patch(`/consultations/${id}/`, data).catch(handleError),
  addPrescription: (id, data) => api.post(`/consultations/${id}/add_prescription/`, data).catch(handleError),
  prescriptions: (id) => api.get(`/consultations/${id}/prescriptions/`).catch(handleError),
}

// ─── Prescriptions ────────────────────────────────────────────
export const prescriptionApi = {
  list: (params = {}) => api.get('/prescriptions/', { params }).catch(handleError),
  get: (id) => api.get(`/prescriptions/${id}/`).catch(handleError),
  dispense: (id) => api.post(`/prescriptions/${id}/dispense/`).catch(handleError),
  undispensed: () => api.get('/prescriptions/', { params: { undispensed: true } }).catch(handleError),
}

// ─── Medicines ────────────────────────────────────────────────
export const medicineApi = {
  list: (params = {}) => api.get('/medicines/', { params }).catch(handleError),
  get: (id) => api.get(`/medicines/${id}/`).catch(handleError),
  create: (data) => api.post('/medicines/', data).catch(handleError),
  update: (id, data) => api.patch(`/medicines/${id}/`, data).catch(handleError),
  lowStock: () => api.get('/medicines/low_stock/').catch(handleError),
  adjustStock: (id, data) => api.post(`/medicines/${id}/adjust_stock/`, data).catch(handleError),
  stockMovements: (id) => api.get(`/medicines/${id}/stock_movements/`).catch(handleError),
  search: (q) => api.get('/medicines/', { params: { search: q } }).catch(handleError),
}

// ─── OTC Sales ────────────────────────────────────────────────
export const otcApi = {
  list: (params = {}) => api.get('/otc-sales/', { params }).catch(handleError),
  get: (id) => api.get(`/otc-sales/${id}/`).catch(handleError),
  create: (data) => api.post('/otc-sales/', data).catch(handleError),
  dispense: (id) => api.post(`/otc-sales/${id}/dispense/`).catch(handleError),
}

// ─── Visits & Triage ──────────────────────────────────────────
export const visitApi = {
  list: (params = {}) => api.get('/visits/', { params }).catch(handleError),
  get: (id) => api.get(`/visits/${id}/`).catch(handleError),
  create: (data) => api.post('/visits/', data).catch(handleError),
  update: (id, data) => api.patch(`/visits/${id}/`, data).catch(handleError),
  updateStatus: (id, status) => api.patch(`/visits/${id}/update_status/`, { status }).catch(handleError),
  waiting: () => api.get('/visits/waiting/').catch(handleError),
}

export const triageApi = {
  list: (params = {}) => api.get('/triage/', { params }).catch(handleError),
  get: (id) => api.get(`/triage/${id}/`).catch(handleError),
  create: (data) => api.post('/triage/', data).catch(handleError),
  categories: () => api.get('/triage-categories/').catch(handleError),
}

export const queueApi = {
  list: (params = {}) => api.get('/queue/', { params }).catch(handleError),
  callPatient: (id) => api.post(`/queue/${id}/call_patient/`).catch(handleError),
  startService: (id) => api.post(`/queue/${id}/start_service/`).catch(handleError),
  complete: (id) => api.post(`/queue/${id}/complete/`).catch(handleError),
}

// ─── Lab ──────────────────────────────────────────────────────
export const labApi = {
  tests: (params = {}) => api.get('/lab-tests/', { params }).catch(handleError),
  orders: {
    list: (params = {}) => api.get('/lab-orders/', { params }).catch(handleError),
    get: (id) => api.get(`/lab-orders/${id}/`).catch(handleError),
    create: (data) => api.post('/lab-orders/', data).catch(handleError),
    updateStatus: (id, status) => api.patch(`/lab-orders/${id}/update_status/`, { status }).catch(handleError),
  },
  results: {
    list: (params = {}) => api.get('/lab-results/', { params }).catch(handleError),
    get: (id) => api.get(`/lab-results/${id}/`).catch(handleError),
    create: (data) => api.post('/lab-results/', data).catch(handleError),
    update: (id, data) => api.patch(`/lab-results/${id}/`, data).catch(handleError),
  },
}

// ─── Imaging ──────────────────────────────────────────────────
export const imagingApi = {
  list: (params = {}) => api.get('/imaging/', { params }).catch(handleError),
  get: (id) => api.get(`/imaging/${id}/`).catch(handleError),
  create: (data) => api.post('/imaging/', data).catch(handleError),
  update: (id, data) => api.patch(`/imaging/${id}/`, data).catch(handleError),
  updateStatus: (id, status) => api.patch(`/imaging/${id}/update_status/`, { status }).catch(handleError),
}

// ─── Inpatient ────────────────────────────────────────────────
export const inpatientApi = {
  wards: () => api.get('/wards/').catch(handleError),
  beds: {
    list: (params = {}) => api.get('/beds/', { params }).catch(handleError),
    available: () => api.get('/beds/available/').catch(handleError),
  },
  admissions: {
    list: (params = {}) => api.get('/admissions/', { params }).catch(handleError),
    get: (id) => api.get(`/admissions/${id}/`).catch(handleError),
    create: (data) => api.post('/admissions/', data).catch(handleError),
    discharge: (id, data) => api.post(`/admissions/${id}/discharge/`, data).catch(handleError),
    charges: (id) => api.get(`/admissions/${id}/charges/`).catch(handleError),
    vitals: (id) => api.get(`/admissions/${id}/vitals/`).catch(handleError),
    addCharge: (id, data) => api.post(`/admissions/${id}/add_charge/`, data).catch(handleError),
  },
  medicineRequests: {
    list: (params = {}) => api.get('/medicine-requests/', { params }).catch(handleError),
    get: (id) => api.get(`/medicine-requests/${id}/`).catch(handleError),
    create: (data) => api.post('/medicine-requests/', data).catch(handleError),
    approve: (id, data) => api.post(`/medicine-requests/${id}/approve/`, data).catch(handleError),
    reject: (id, data) => api.post(`/medicine-requests/${id}/reject/`, data).catch(handleError),
  },
}

// ─── Emergency ────────────────────────────────────────────────
export const emergencyApi = {
  beds: () => api.get('/emergency-beds/').catch(handleError),
  visits: {
    list: (params = {}) => api.get('/emergency-visits/', { params }).catch(handleError),
    get: (id) => api.get(`/emergency-visits/${id}/`).catch(handleError),
    charges: (id) => api.get(`/emergency-visits/${id}/charges/`).catch(handleError),
    addCharge: (id, data) => api.post(`/emergency-visits/${id}/add_charge/`, data).catch(handleError),
  },
  medicineRequests: {
    list: (params = {}) => api.get('/emergency-medicine-requests/', { params }).catch(handleError),
    create: (data) => api.post('/emergency-medicine-requests/', data).catch(handleError),
  },
}

// ─── Procurement ──────────────────────────────────────────────
export const procurementApi = {
  suppliers: {
    list: (params = {}) => api.get('/suppliers/', { params }).catch(handleError),
    create: (data) => api.post('/suppliers/', data).catch(handleError),
    update: (id, data) => api.patch(`/suppliers/${id}/`, data).catch(handleError),
  },
  purchaseRequests: {
    list: (params = {}) => api.get('/purchase-requests/', { params }).catch(handleError),
    create: (data) => api.post('/purchase-requests/', data).catch(handleError),
    update: (id, data) => api.patch(`/purchase-requests/${id}/`, data).catch(handleError),
  },
  purchaseOrders: {
    list: (params = {}) => api.get('/purchase-orders/', { params }).catch(handleError),
    create: (data) => api.post('/purchase-orders/', data).catch(handleError),
  },
  grn: {
    list: (params = {}) => api.get('/grn/', { params }).catch(handleError),
    create: (data) => api.post('/grn/', data).catch(handleError),
  },
}

// ─── Insurance Claims ─────────────────────────────────────────
export const claimsApi = {
  consultation: {
    list: (params = {}) => api.get('/claims/consultation/', { params }).catch(handleError),
    approve: (id, data) => api.post(`/claims/consultation/${id}/approve/`, data).catch(handleError),
    reject: (id, data) => api.post(`/claims/consultation/${id}/reject/`, data).catch(handleError),
  },
  pharmacy: {
    list: (params = {}) => api.get('/claims/pharmacy/', { params }).catch(handleError),
    approve: (id, data) => api.post(`/claims/pharmacy/${id}/approve/`, data).catch(handleError),
    reject: (id, data) => api.post(`/claims/pharmacy/${id}/reject/`, data).catch(handleError),
  },
  inpatient: {
    list: (params = {}) => api.get('/claims/inpatient/', { params }).catch(handleError),
    approve: (id, data) => api.post(`/claims/inpatient/${id}/approve/`, data).catch(handleError),
  },
}

// ─── Notifications ────────────────────────────────────────────
export const notificationApi = {
  list: () => api.get('/notifications/').catch(handleError),
  unread: () => api.get('/notifications/unread/').catch(handleError),
  markRead: (id) => api.post(`/notifications/${id}/mark_read/`).catch(handleError),
  markAllRead: () => api.post('/notifications/mark_all_read/').catch(handleError),
}

// ─── Payments ─────────────────────────────────────────────────
export const paymentApi = {
  logs: (params = {}) => api.get('/payment-logs/', { params }).catch(handleError),
  sessions: {
    list: () => api.get('/cashier-sessions/').catch(handleError),
    active: () => api.get('/cashier-sessions/active/').catch(handleError),
    open: (data) => api.post('/cashier-sessions/', data).catch(handleError),
  },
}

// ─── Misc ─────────────────────────────────────────────────────
export const miscApi = {
  insuranceProviders: () => api.get('/insurance-providers/').catch(handleError),
  specializedServices: () => api.get('/specialized-services/').catch(handleError),
  icd10Search: (q, common) => api.get('/icd10/', { params: { search: q, common } }).catch(handleError),
  attendance: {
    checkIn: () => api.post('/attendance/check_in/').catch(handleError),
    checkOut: () => api.post('/attendance/check_out/').catch(handleError),
    list: (params = {}) => api.get('/attendance/', { params }).catch(handleError),
  },
  sha: {
    members: (params = {}) => api.get('/sha/members/', { params }).catch(handleError),
    claims: (params = {}) => api.get('/sha/claims/', { params }).catch(handleError),
  },
}

export default api