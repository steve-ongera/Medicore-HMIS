"""
MediCore HMS - API URL Configuration
All endpoints registered with DRF Router
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# ─── Auth & Users ──────────────────────────────────────
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserViewSet, basename='users')

# ─── Core Clinical ─────────────────────────────────────
router.register(r'patients', views.PatientViewSet, basename='patients')
router.register(r'doctors', views.DoctorViewSet, basename='doctors')
router.register(r'nurses', views.NurseViewSet, basename='nurses')
router.register(r'appointments', views.AppointmentViewSet, basename='appointments')
router.register(r'consultations', views.ConsultationViewSet, basename='consultations')
router.register(r'prescriptions', views.PrescriptionViewSet, basename='prescriptions')
router.register(r'icd10', views.ICD10CodeViewSet, basename='icd10')

# ─── Pharmacy & Medicines ──────────────────────────────
router.register(r'medicines', views.MedicineViewSet, basename='medicines')
router.register(r'otc-sales', views.OTCSaleViewSet, basename='otc-sales')
router.register(r'stock-movements', views.StockMovementViewSet, basename='stock-movements')

# ─── Visits & Triage ───────────────────────────────────
router.register(r'visits', views.PatientVisitViewSet, basename='visits')
router.register(r'triage', views.TriageAssessmentViewSet, basename='triage')
router.register(r'triage-categories', views.TriageCategoryViewSet, basename='triage-categories')
router.register(r'queue', views.QueueManagementViewSet, basename='queue')

# ─── Insurance & Services ──────────────────────────────
router.register(r'insurance-providers', views.InsuranceProviderViewSet, basename='insurance-providers')
router.register(r'specialized-services', views.SpecializedServiceViewSet, basename='specialized-services')

# ─── Laboratory ────────────────────────────────────────
router.register(r'lab-tests', views.LabTestViewSet, basename='lab-tests')
router.register(r'lab-orders', views.LabOrderViewSet, basename='lab-orders')
router.register(r'lab-results', views.LabResultViewSet, basename='lab-results')

# ─── Radiology / Imaging ───────────────────────────────
router.register(r'imaging', views.ImagingStudyViewSet, basename='imaging')

# ─── Inpatient ─────────────────────────────────────────
router.register(r'wards', views.WardViewSet, basename='wards')
router.register(r'beds', views.BedViewSet, basename='beds')
router.register(r'admissions', views.InpatientAdmissionViewSet, basename='admissions')
router.register(r'medicine-requests', views.InpatientMedicineRequestViewSet, basename='medicine-requests')

# ─── Emergency ─────────────────────────────────────────
router.register(r'emergency-beds', views.EmergencyBedViewSet, basename='emergency-beds')
router.register(r'emergency-visits', views.EmergencyVisitViewSet, basename='emergency-visits')
router.register(r'emergency-medicine-requests', views.EmergencyMedicineRequestViewSet, basename='emergency-medicine-requests')

# ─── Procurement ───────────────────────────────────────
router.register(r'suppliers', views.SupplierViewSet, basename='suppliers')
router.register(r'purchase-requests', views.PurchaseRequestViewSet, basename='purchase-requests')
router.register(r'purchase-orders', views.PurchaseOrderViewSet, basename='purchase-orders')
router.register(r'grn', views.GoodsReceivedNoteViewSet, basename='grn')

# ─── Insurance Claims ──────────────────────────────────
router.register(r'claims/consultation', views.ConsultationInsuranceClaimViewSet, basename='claims-consultation')
router.register(r'claims/pharmacy', views.PharmacyInsuranceClaimViewSet, basename='claims-pharmacy')
router.register(r'claims/inpatient', views.InpatientInsuranceClaimViewSet, basename='claims-inpatient')

# ─── Notifications ─────────────────────────────────────
router.register(r'notifications', views.NotificationViewSet, basename='notifications')

# ─── Payments & Finance ────────────────────────────────
router.register(r'payment-logs', views.PaymentAuditLogViewSet, basename='payment-logs')
router.register(r'cashier-sessions', views.CashierSessionViewSet, basename='cashier-sessions')

# ─── SHA ───────────────────────────────────────────────
router.register(r'sha/members', views.SHAMemberViewSet, basename='sha-members')
router.register(r'sha/claims', views.SHAClaimViewSet, basename='sha-claims')

# ─── Attendance & HR ───────────────────────────────────
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'leave', views.LeaveApplicationViewSet, basename='leave')

# ─── Dashboard ─────────────────────────────────────────
router.register(r'dashboard', views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]