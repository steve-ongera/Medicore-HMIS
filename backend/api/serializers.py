"""
MediCore HMS - Serializers
Covers all major models with nested relationships
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    User, Patient, Doctor, Nurse, Disease,
    Medicine, MedicineCategory, Appointment, Consultation,
    Prescription, MedicineSale, SoldMedicine, PatientMedicalHistory,
    Notification, PatientVisit, TriageAssessment, TriageCategory,
    InsuranceProvider, SpecializedService, QueueManagement,
    LabOrder, LabOrderItem, LabTest, LabTestCategory, LabResult,
    ImagingStudy, Ward, Bed, InpatientAdmission, InpatientDailyCharge,
    InpatientVitals, EmergencyVisit, EmergencyCharge, EmergencyBed,
    OverTheCounterSale, OverTheCounterSaleItem, StockMovement,
    GoodsReceivedNote, PurchaseOrder, PurchaseRequest, Supplier,
    ConsultationInsuranceClaim, PharmacyInsuranceClaim, InpatientInsuranceClaim,
    ICD10Code, ConsultationDiagnosis, Attendance, LeaveApplication,
    PaymentAuditLog, CashierSession, SHAMember, SHAClaim,
    InpatientMedicineRequest, EmergencyMedicineRequest, InpatientInsuranceClaim,
)


# ═══════════════════════════════════════════════════════
#  AUTH SERIALIZERS
# ═══════════════════════════════════════════════════════

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled")
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'user_type', 'phone_number', 'specialization',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'confirm_password', 'user_type',
            'phone_number', 'specialization', 'license_number'
        ]

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ═══════════════════════════════════════════════════════
#  PATIENT SERIALIZERS
# ═══════════════════════════════════════════════════════

class PatientSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'

    def get_age(self, obj):
        if obj.date_of_birth:
            today = timezone.now().date()
            dob = obj.date_of_birth
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class PatientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for lists"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'full_name', 'id_number', 'phone_number', 'gender', 'date_of_birth']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class PatientMedicalHistorySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = PatientMedicalHistory
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  DOCTOR & NURSE SERIALIZERS
# ═══════════════════════════════════════════════════════

class DoctorSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    license_status = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Doctor
        fields = '__all__'


class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'full_name', 'specialization', 'phone_number', 'is_active']


class NurseSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Nurse
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  APPOINTMENT SERIALIZERS
# ═══════════════════════════════════════════════════════

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.first_name', read_only=True)
    patient_last = serializers.CharField(source='patient.last_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'scheduled_time', 'reason', 'symptoms']


# ═══════════════════════════════════════════════════════
#  CONSULTATION SERIALIZERS
# ═══════════════════════════════════════════════════════

class PrescriptionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_unit = serializers.CharField(source='medicine.get_unit_type_display', read_only=True)
    packaging_breakdown = serializers.ReadOnlyField()
    stock_available = serializers.IntegerField(source='medicine.quantity_in_stock', read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'


class ConsultationSerializer(serializers.ModelSerializer):
    prescriptions = PrescriptionSerializer(many=True, read_only=True, source='prescription_set')
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = '__all__'

    def get_patient_name(self, obj):
        p = obj.appointment.patient
        return f"{p.first_name} {p.last_name}"

    def get_doctor_name(self, obj):
        return obj.appointment.doctor.get_full_name()


class ConsultationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ['appointment', 'diagnosis', 'notes', 'follow_up_date', 'follow_up_notes']


# ═══════════════════════════════════════════════════════
#  MEDICINE SERIALIZERS
# ═══════════════════════════════════════════════════════

class MedicineCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineCategory
        fields = '__all__'


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.ReadOnlyField()
    packs_in_stock = serializers.ReadOnlyField()
    price_per_pack_cash = serializers.ReadOnlyField()

    class Meta:
        model = Medicine
        fields = '__all__'


class MedicineListSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'unit_type', 'quantity_in_stock',
            'price_per_unit_cash', 'price_per_unit_insurance',
            'is_low_stock', 'reorder_level'
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  SALE SERIALIZERS
# ═══════════════════════════════════════════════════════

class SoldMedicineSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = SoldMedicine
        fields = '__all__'


class MedicineSaleSerializer(serializers.ModelSerializer):
    items = SoldMedicineSerializer(many=True, read_only=True, source='soldmedicine_set')
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicineSale
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return "Walk-in"


class OTCSaleItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = OverTheCounterSaleItem
        fields = '__all__'


class OTCSaleSerializer(serializers.ModelSerializer):
    items = OTCSaleItemSerializer(many=True, read_only=True)

    class Meta:
        model = OverTheCounterSale
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  VISIT & TRIAGE SERIALIZERS
# ═══════════════════════════════════════════════════════

class InsuranceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceProvider
        fields = '__all__'


class SpecializedServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecializedService
        fields = '__all__'


class TriageCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageCategory
        fields = '__all__'


class PatientVisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_gender = serializers.CharField(source='patient.gender', read_only=True)
    total_wait_time = serializers.ReadOnlyField()
    triage_info = serializers.SerializerMethodField()
    insurance_name = serializers.CharField(source='insurance_provider.name', read_only=True)
    service_name = serializers.CharField(source='specialized_service.name', read_only=True)

    class Meta:
        model = PatientVisit
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_triage_info(self, obj):
        if hasattr(obj, 'triage'):
            return {
                'category': obj.triage.category.color_code,
                'priority': obj.triage.category.priority_level
            }
        return None


class PatientVisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientVisit
        fields = [
            'patient', 'visit_type', 'chief_complaint',
            'insurance_provider', 'specialized_service', 'notes'
        ]


class TriageAssessmentSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()
    is_critical_vitals = serializers.ReadOnlyField()
    assessed_by_name = serializers.SerializerMethodField()
    category_info = TriageCategorySerializer(source='category', read_only=True)

    class Meta:
        model = TriageAssessment
        fields = '__all__'

    def get_assessed_by_name(self, obj):
        if obj.assessed_by:
            return f"{obj.assessed_by.first_name} {obj.assessed_by.last_name}"
        return None


class QueueManagementSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    wait_time = serializers.ReadOnlyField()
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    triage_color = serializers.SerializerMethodField()

    class Meta:
        model = QueueManagement
        fields = '__all__'

    def get_patient_name(self, obj):
        p = obj.visit.patient
        return f"{p.first_name} {p.last_name}"

    def get_triage_color(self, obj):
        if hasattr(obj.visit, 'triage'):
            return obj.visit.triage.category.color_code
        return 'GREEN'


# ═══════════════════════════════════════════════════════
#  LAB SERIALIZERS
# ═══════════════════════════════════════════════════════

class LabTestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTestCategory
        fields = '__all__'


class LabTestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_imaging = serializers.ReadOnlyField()

    class Meta:
        model = LabTest
        fields = '__all__'


class LabOrderItemSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='test.test_name', read_only=True)
    test_code = serializers.CharField(source='test.test_code', read_only=True)

    class Meta:
        model = LabOrderItem
        fields = '__all__'


class LabOrderSerializer(serializers.ModelSerializer):
    test_items = LabOrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()
    ordered_by_name = serializers.CharField(source='ordered_by.get_full_name', read_only=True)

    class Meta:
        model = LabOrder
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  IMAGING SERIALIZERS
# ═══════════════════════════════════════════════════════

class ImagingStudySerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    ordered_by_name = serializers.CharField(source='ordered_by.get_full_name', read_only=True)

    class Meta:
        model = ImagingStudy
        fields = '__all__'

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None


# ═══════════════════════════════════════════════════════
#  INPATIENT SERIALIZERS
# ═══════════════════════════════════════════════════════

class WardSerializer(serializers.ModelSerializer):
    occupied_beds_count = serializers.ReadOnlyField()
    available_beds_count = serializers.ReadOnlyField()
    occupancy_rate = serializers.ReadOnlyField()

    class Meta:
        model = Ward
        fields = '__all__'


class BedSerializer(serializers.ModelSerializer):
    ward_name = serializers.CharField(source='ward.ward_name', read_only=True)
    ward_code = serializers.CharField(source='ward.ward_code', read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Bed
        fields = '__all__'

    def get_is_available(self, obj):
        return obj.is_available()


class InpatientAdmissionSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    bed_number = serializers.CharField(source='bed.bed_number', read_only=True)
    ward_name = serializers.ReadOnlyField()
    length_of_stay = serializers.ReadOnlyField()
    outstanding_balance = serializers.ReadOnlyField()

    class Meta:
        model = InpatientAdmission
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class InpatientDailyChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InpatientDailyCharge
        fields = '__all__'


class InpatientVitalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InpatientVitals
        fields = '__all__'


class InpatientMedicineRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField()
    ward_name = serializers.ReadOnlyField()
    bed_number = serializers.ReadOnlyField()
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_stock = serializers.IntegerField(source='medicine.quantity_in_stock', read_only=True)

    class Meta:
        model = InpatientMedicineRequest
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  EMERGENCY SERIALIZERS
# ═══════════════════════════════════════════════════════

class EmergencyBedSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyBed
        fields = '__all__'


class EmergencyChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyCharge
        fields = '__all__'


class EmergencyVisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    monitoring_hours = serializers.ReadOnlyField()
    total_charges_calc = serializers.SerializerMethodField()

    class Meta:
        model = EmergencyVisit
        fields = '__all__'

    def get_patient_name(self, obj):
        p = obj.visit.patient
        return f"{p.first_name} {p.last_name}"

    def get_total_charges_calc(self, obj):
        return float(obj.charges.aggregate(
            total=__import__('django.db.models', fromlist=['Sum']).Sum('total_amount')
        )['total'] or 0)


class EmergencyMedicineRequestSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_stock = serializers.IntegerField(source='medicine.quantity_in_stock', read_only=True)

    class Meta:
        model = EmergencyMedicineRequest
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  PROCUREMENT SERIALIZERS
# ═══════════════════════════════════════════════════════

class SupplierSerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Supplier
        fields = '__all__'


class PurchaseRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.supplier_name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)

    class Meta:
        model = GoodsReceivedNote
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  INSURANCE CLAIM SERIALIZERS
# ═══════════════════════════════════════════════════════

class ConsultationInsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    insurance_name = serializers.CharField(source='insurance_provider.name', read_only=True)

    class Meta:
        model = ConsultationInsuranceClaim
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class PharmacyInsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    insurance_name = serializers.CharField(source='insurance_provider.name', read_only=True)

    class Meta:
        model = PharmacyInsuranceClaim
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class InpatientInsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    insurance_name = serializers.CharField(source='insurance_provider.name', read_only=True)

    class Meta:
        model = InpatientInsuranceClaim
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.admission.patient.first_name} {obj.admission.patient.last_name}"


# ═══════════════════════════════════════════════════════
#  ICD10 SERIALIZERS
# ═══════════════════════════════════════════════════════

class ICD10CodeSerializer(serializers.ModelSerializer):
    full_display = serializers.ReadOnlyField()

    class Meta:
        model = ICD10Code
        fields = ['id', 'code', 'short_description', 'local_name', 'full_display', 'is_common', 'nhif_eligible']


class ConsultationDiagnosisSerializer(serializers.ModelSerializer):
    icd10_display = serializers.CharField(source='icd10_code.full_display', read_only=True)

    class Meta:
        model = ConsultationDiagnosis
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  NOTIFICATION SERIALIZER
# ═══════════════════════════════════════════════════════

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField()
    patient_name = serializers.ReadOnlyField()
    time_since_created = serializers.ReadOnlyField()

    class Meta:
        model = Notification
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  PAYMENT SERIALIZERS
# ═══════════════════════════════════════════════════════

class PaymentAuditLogSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)

    class Meta:
        model = PaymentAuditLog
        fields = '__all__'


class CashierSessionSerializer(serializers.ModelSerializer):
    cashier_name = serializers.CharField(source='cashier.get_full_name', read_only=True)

    class Meta:
        model = CashierSession
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  SHA SERIALIZERS
# ═══════════════════════════════════════════════════════

class SHAMemberSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    is_valid = serializers.ReadOnlyField()
    available_balance = serializers.ReadOnlyField()

    class Meta:
        model = SHAMember
        fields = '__all__'

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class SHAClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = SHAClaim
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  ATTENDANCE SERIALIZERS
# ═══════════════════════════════════════════════════════

class AttendanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    is_late = serializers.ReadOnlyField()

    class Meta:
        model = Attendance
        fields = '__all__'


class LeaveApplicationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = LeaveApplication
        fields = '__all__'


# ═══════════════════════════════════════════════════════
#  DASHBOARD SERIALIZERS
# ═══════════════════════════════════════════════════════

class DashboardStatsSerializer(serializers.Serializer):
    """Generic stats for dashboard cards"""
    total_patients = serializers.IntegerField()
    today_visits = serializers.IntegerField()
    active_admissions = serializers.IntegerField()
    pending_lab_orders = serializers.IntegerField()
    low_stock_medicines = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_claims = serializers.IntegerField()
    available_beds = serializers.IntegerField()