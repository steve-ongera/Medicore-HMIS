"""
MediCore HMS - ViewSets
Role-based permissions + full CRUD for all modules
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import uuid

from .models import *
from .serializers import *


# ═══════════════════════════════════════════════════════
#  PERMISSION HELPERS
# ═══════════════════════════════════════════════════════

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'ADMIN'


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'DOCTOR'


class IsNurse(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'NURSE'


class IsReceptionist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'RECEPTIONIST'


class IsPharmacist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'PHARMACIST'


class IsCashier(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'CASHIER'


class IsLabTech(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'LAB_TECH'


class IsInsurance(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'INSURANCE'


# ═══════════════════════════════════════════════════════
#  AUTH VIEWSET
# ═══════════════════════════════════════════════════════

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out'})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not user.check_password(old_password):
            return Response({'error': 'Wrong password'}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed'})


# ═══════════════════════════════════════════════════════
#  USER VIEWSET
# ═══════════════════════════════════════════════════════

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = User.objects.all()
        user_type = self.request.query_params.get('user_type')
        if user_type:
            qs = qs.filter(user_type=user_type)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        return qs


# ═══════════════════════════════════════════════════════
#  PATIENT VIEWSET
# ═══════════════════════════════════════════════════════

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        qs = Patient.objects.all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(id_number__icontains=search) |
                Q(phone_number__icontains=search)
            )
        return qs

    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        history = PatientMedicalHistory.objects.filter(patient=patient).order_by('-date_recorded')
        serializer = PatientMedicalHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def visits(self, request, pk=None):
        patient = self.get_object()
        visits = PatientVisit.objects.filter(patient=patient).order_by('-arrival_time')[:10]
        serializer = PatientVisitSerializer(visits, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        patient = self.get_object()
        prescriptions = Prescription.objects.filter(
            consultation__appointment__patient=patient
        ).order_by('-prescribed_at')[:20]
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════
#  DOCTOR & NURSE VIEWSETS
# ═══════════════════════════════════════════════════════

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return DoctorListSerializer
        return DoctorSerializer

    def get_queryset(self):
        qs = Doctor.objects.filter(is_active=True)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(specialization__icontains=search)
            )
        return qs


class NurseViewSet(viewsets.ModelViewSet):
    queryset = Nurse.objects.all()
    serializer_class = NurseSerializer

    def get_queryset(self):
        qs = Nurse.objects.filter(is_active=True)
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department=dept)
        return qs


# ═══════════════════════════════════════════════════════
#  APPOINTMENT VIEWSET
# ═══════════════════════════════════════════════════════

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        qs = Appointment.objects.select_related('patient', 'doctor').all()
        user = self.request.user
        if user.user_type == 'DOCTOR':
            qs = qs.filter(doctor=user)
        date_filter = self.request.query_params.get('date')
        if date_filter:
            qs = qs.filter(scheduled_time__date=date_filter)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        qs = self.get_queryset().filter(scheduled_time__date=today)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════
#  CONSULTATION VIEWSET
# ═══════════════════════════════════════════════════════

class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return ConsultationCreateSerializer
        return ConsultationSerializer

    def get_queryset(self):
        qs = Consultation.objects.select_related(
            'appointment__patient', 'appointment__doctor'
        ).all()
        user = self.request.user
        if user.user_type == 'DOCTOR':
            qs = qs.filter(appointment__doctor=user)
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(appointment__patient_id=patient_id)
        return qs

    @action(detail=True, methods=['post'])
    def add_prescription(self, request, pk=None):
        consultation = self.get_object()
        serializer = PrescriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(consultation=consultation)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        consultation = self.get_object()
        prescriptions = Prescription.objects.filter(consultation=consultation)
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════
#  PRESCRIPTION VIEWSET
# ═══════════════════════════════════════════════════════

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        qs = Prescription.objects.select_related('medicine', 'consultation').all()
        undispensed = self.request.query_params.get('undispensed')
        if undispensed:
            qs = qs.filter(is_dispensed=False)
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(consultation__appointment__patient_id=patient_id)
        return qs

    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        prescription = self.get_object()
        if prescription.is_dispensed:
            return Response({'error': 'Already dispensed'}, status=400)
        try:
            prescription.dispense(request.user)
            return Response({'detail': 'Dispensed successfully', 'data': PrescriptionSerializer(prescription).data})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


# ═══════════════════════════════════════════════════════
#  MEDICINE VIEWSET
# ═══════════════════════════════════════════════════════

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicineListSerializer
        return MedicineSerializer

    def get_queryset(self):
        qs = Medicine.objects.all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(batch_number__icontains=search))
        low_stock = self.request.query_params.get('low_stock')
        if low_stock:
            qs = [m for m in qs if m.is_low_stock]
            return Medicine.objects.filter(id__in=[m.id for m in qs])
        return qs

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        medicines = Medicine.objects.all()
        low = [m for m in medicines if m.is_low_stock]
        serializer = MedicineListSerializer(low, many=True)
        return Response({'count': len(low), 'results': serializer.data})

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        medicine = self.get_object()
        quantity = int(request.data.get('quantity', 0))
        movement_type = request.data.get('movement_type', 'ADJUSTMENT')
        reason = request.data.get('reason', '')

        prev_qty = medicine.quantity_in_stock
        medicine.quantity_in_stock += quantity
        if medicine.quantity_in_stock < 0:
            return Response({'error': 'Stock cannot go below 0'}, status=400)
        medicine.save()

        StockMovement.objects.create(
            medicine=medicine,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=prev_qty,
            new_quantity=medicine.quantity_in_stock,
            reason=reason,
            performed_by=request.user
        )
        return Response({'detail': 'Stock adjusted', 'new_quantity': medicine.quantity_in_stock})

    @action(detail=True, methods=['get'])
    def stock_movements(self, request, pk=None):
        medicine = self.get_object()
        movements = StockMovement.objects.filter(medicine=medicine).order_by('-created_at')[:50]
        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════
#  OTC SALE VIEWSET
# ═══════════════════════════════════════════════════════

class OTCSaleViewSet(viewsets.ModelViewSet):
    queryset = OverTheCounterSale.objects.all()
    serializer_class = OTCSaleSerializer

    def get_queryset(self):
        qs = OverTheCounterSale.objects.all()
        date_filter = self.request.query_params.get('date')
        if date_filter:
            qs = qs.filter(created_at__date=date_filter)
        status_filter = self.request.query_params.get('payment_status')
        if status_filter:
            qs = qs.filter(payment_status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        sale = self.get_object()
        if sale.is_dispensed:
            return Response({'error': 'Already dispensed'}, status=400)
        # Reduce stock for each item
        for item in sale.items.all():
            if item.quantity > item.medicine.quantity_in_stock:
                return Response({'error': f'Insufficient stock for {item.medicine.name}'}, status=400)
            item.medicine.quantity_in_stock -= item.quantity
            item.medicine.save()
        sale.is_dispensed = True
        sale.dispensed_at = timezone.now()
        sale.dispensed_by = request.user
        sale.save()
        return Response({'detail': 'Dispensed successfully'})


# ═══════════════════════════════════════════════════════
#  VISIT VIEWSET
# ═══════════════════════════════════════════════════════

class PatientVisitViewSet(viewsets.ModelViewSet):
    queryset = PatientVisit.objects.all()
    serializer_class = PatientVisitSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return PatientVisitCreateSerializer
        return PatientVisitSerializer

    def get_queryset(self):
        qs = PatientVisit.objects.select_related('patient', 'assigned_doctor').all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        date_filter = self.request.query_params.get('date')
        if date_filter:
            qs = qs.filter(arrival_time__date=date_filter)
        else:
            qs = qs.filter(arrival_time__date=timezone.now().date())
        visit_type = self.request.query_params.get('visit_type')
        if visit_type:
            qs = qs.filter(visit_type=visit_type)
        return qs

    @action(detail=False, methods=['get'])
    def waiting(self, request):
        qs = PatientVisit.objects.filter(
            status__in=['REGISTERED', 'TRIAGED', 'WAITING'],
            arrival_time__date=timezone.now().date()
        )
        serializer = PatientVisitSerializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        visit = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            visit.status = new_status
            visit.save()
        return Response(PatientVisitSerializer(visit).data)


# ═══════════════════════════════════════════════════════
#  TRIAGE VIEWSET
# ═══════════════════════════════════════════════════════

class TriageAssessmentViewSet(viewsets.ModelViewSet):
    queryset = TriageAssessment.objects.all()
    serializer_class = TriageAssessmentSerializer

    def perform_create(self, serializer):
        assessment = serializer.save()
        # Update visit status
        visit = assessment.visit
        visit.status = 'TRIAGED'
        visit.triage_time = timezone.now()
        visit.save()


class TriageCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TriageCategory.objects.filter(is_active=True)
    serializer_class = TriageCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# ═══════════════════════════════════════════════════════
#  QUEUE VIEWSET
# ═══════════════════════════════════════════════════════

class QueueManagementViewSet(viewsets.ModelViewSet):
    queryset = QueueManagement.objects.filter(is_active=True)
    serializer_class = QueueManagementSerializer

    def get_queryset(self):
        qs = QueueManagement.objects.filter(is_active=True)
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department=dept)
        return qs.order_by('priority_override', 'queue_number')

    @action(detail=True, methods=['post'])
    def call_patient(self, request, pk=None):
        entry = self.get_object()
        entry.call_patient()
        return Response({'detail': 'Patient called'})

    @action(detail=True, methods=['post'])
    def start_service(self, request, pk=None):
        entry = self.get_object()
        entry.start_service(request.user)
        return Response({'detail': 'Service started'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        entry = self.get_object()
        entry.complete_service()
        return Response({'detail': 'Service completed'})


# ═══════════════════════════════════════════════════════
#  LAB VIEWSETS
# ═══════════════════════════════════════════════════════

class LabTestViewSet(viewsets.ModelViewSet):
    queryset = LabTest.objects.filter(is_active=True)
    serializer_class = LabTestSerializer

    def get_queryset(self):
        qs = LabTest.objects.filter(is_active=True)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(test_name__icontains=search) |
                Q(test_code__icontains=search)
            )
        return qs


class LabOrderViewSet(viewsets.ModelViewSet):
    queryset = LabOrder.objects.all()
    serializer_class = LabOrderSerializer

    def get_queryset(self):
        qs = LabOrder.objects.select_related('patient', 'ordered_by').all()
        user = self.request.user
        if user.user_type == 'LAB_TECH':
            qs = qs.filter(Q(assigned_to=user) | Q(assigned_to=None))
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        priority = self.request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        date_filter = self.request.query_params.get('date')
        if date_filter:
            qs = qs.filter(created_at__date=date_filter)
        else:
            qs = qs.filter(created_at__date=timezone.now().date())
        return qs

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            order.status = new_status
            if new_status == 'SAMPLE_COLLECTED':
                order.sample_collected_at = timezone.now()
            elif new_status == 'IN_PROGRESS':
                order.started_at = timezone.now()
            elif new_status == 'COMPLETED':
                order.completed_at = timezone.now()
            order.save()
        return Response(LabOrderSerializer(order).data)


class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer


# ═══════════════════════════════════════════════════════
#  IMAGING VIEWSET
# ═══════════════════════════════════════════════════════

class ImagingStudyViewSet(viewsets.ModelViewSet):
    queryset = ImagingStudy.objects.all()
    serializer_class = ImagingStudySerializer

    def get_queryset(self):
        qs = ImagingStudy.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        study = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            study.status = new_status
            if new_status == 'REPORTED':
                study.reported_at = timezone.now()
                study.reported_by = request.user
            study.save()
        return Response(ImagingStudySerializer(study).data)


# ═══════════════════════════════════════════════════════
#  INPATIENT VIEWSETS
# ═══════════════════════════════════════════════════════

class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.filter(is_active=True)
    serializer_class = WardSerializer


class BedViewSet(viewsets.ModelViewSet):
    queryset = Bed.objects.filter(is_active=True)
    serializer_class = BedSerializer

    def get_queryset(self):
        qs = Bed.objects.filter(is_active=True)
        ward_id = self.request.query_params.get('ward')
        if ward_id:
            qs = qs.filter(ward_id=ward_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=False, methods=['get'])
    def available(self, request):
        qs = Bed.objects.filter(status='AVAILABLE', is_active=True)
        serializer = BedSerializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})


class InpatientAdmissionViewSet(viewsets.ModelViewSet):
    queryset = InpatientAdmission.objects.all()
    serializer_class = InpatientAdmissionSerializer

    def get_queryset(self):
        qs = InpatientAdmission.objects.select_related('patient', 'bed__ward').all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        else:
            qs = qs.filter(status='ACTIVE')
        return qs

    @action(detail=True, methods=['post'])
    def discharge(self, request, pk=None):
        admission = self.get_object()
        summary = request.data.get('discharge_summary', '')
        diagnosis = request.data.get('discharge_diagnosis', '')
        doctor = request.data.get('doctor')
        try:
            doc = Doctor.objects.get(id=doctor)
            admission.discharge(doc, summary, diagnosis)
            return Response({'detail': 'Patient discharged'})
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=400)

    @action(detail=True, methods=['get'])
    def charges(self, request, pk=None):
        admission = self.get_object()
        charges = InpatientDailyCharge.objects.filter(admission=admission).order_by('-charge_date')
        serializer = InpatientDailyChargeSerializer(charges, many=True)
        total = charges.aggregate(t=Sum('total_amount'))['t'] or 0
        return Response({'charges': serializer.data, 'total': float(total)})

    @action(detail=True, methods=['get'])
    def vitals(self, request, pk=None):
        admission = self.get_object()
        vitals = InpatientVitals.objects.filter(admission=admission).order_by('-recorded_at')[:20]
        serializer = InpatientVitalsSerializer(vitals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_charge(self, request, pk=None):
        admission = self.get_object()
        data = request.data.copy()
        data['admission'] = admission.id
        data['created_by'] = request.user.id
        serializer = InpatientDailyChargeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class InpatientMedicineRequestViewSet(viewsets.ModelViewSet):
    queryset = InpatientMedicineRequest.objects.all()
    serializer_class = InpatientMedicineRequestSerializer

    def get_queryset(self):
        qs = InpatientMedicineRequest.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        else:
            qs = qs.filter(status='PENDING')
        return qs.order_by('priority', '-requested_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        req = self.get_object()
        qty = request.data.get('quantity_approved')
        try:
            req.approve(request.user, qty)
            return Response({'detail': 'Approved'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        req = self.get_object()
        reason = request.data.get('reason', '')
        try:
            req.reject(request.user, reason)
            return Response({'detail': 'Rejected'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)


# ═══════════════════════════════════════════════════════
#  EMERGENCY VIEWSETS
# ═══════════════════════════════════════════════════════

class EmergencyBedViewSet(viewsets.ModelViewSet):
    queryset = EmergencyBed.objects.filter(is_active=True)
    serializer_class = EmergencyBedSerializer


class EmergencyVisitViewSet(viewsets.ModelViewSet):
    queryset = EmergencyVisit.objects.all()
    serializer_class = EmergencyVisitSerializer

    def get_queryset(self):
        qs = EmergencyVisit.objects.filter(
            visit__arrival_time__date=timezone.now().date()
        )
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(treatment_status=status_filter)
        return qs

    @action(detail=True, methods=['get'])
    def charges(self, request, pk=None):
        visit = self.get_object()
        charges = EmergencyCharge.objects.filter(emergency_visit=visit)
        serializer = EmergencyChargeSerializer(charges, many=True)
        total = charges.aggregate(t=Sum('total_amount'))['t'] or 0
        return Response({'charges': serializer.data, 'total': float(total)})

    @action(detail=True, methods=['post'])
    def add_charge(self, request, pk=None):
        visit = self.get_object()
        data = request.data.copy()
        data['emergency_visit'] = visit.id
        data['charged_by'] = request.user.id
        serializer = EmergencyChargeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            visit.calculate_total_charges()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class EmergencyMedicineRequestViewSet(viewsets.ModelViewSet):
    queryset = EmergencyMedicineRequest.objects.all()
    serializer_class = EmergencyMedicineRequestSerializer

    def get_queryset(self):
        qs = EmergencyMedicineRequest.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('urgency', '-requested_at')


# ═══════════════════════════════════════════════════════
#  PROCUREMENT VIEWSETS
# ═══════════════════════════════════════════════════════

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    def get_queryset(self):
        qs = Supplier.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(supplier_name__icontains=search)
        return qs


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer

    def get_queryset(self):
        qs = PurchaseRequest.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer


class GoodsReceivedNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceivedNote.objects.all()
    serializer_class = GoodsReceivedNoteSerializer


# ═══════════════════════════════════════════════════════
#  INSURANCE CLAIM VIEWSETS
# ═══════════════════════════════════════════════════════

class ConsultationInsuranceClaimViewSet(viewsets.ModelViewSet):
    queryset = ConsultationInsuranceClaim.objects.all()
    serializer_class = ConsultationInsuranceClaimSerializer

    def get_queryset(self):
        qs = ConsultationInsuranceClaim.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        claim = self.get_object()
        comments = request.data.get('comments')
        claim.approve_by_claims_officer(request.user, comments)
        return Response({'detail': 'Claim approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        claim = self.get_object()
        reason = request.data.get('reason', '')
        claim.reject_by_claims_officer(request.user, reason)
        return Response({'detail': 'Claim rejected'})


class PharmacyInsuranceClaimViewSet(viewsets.ModelViewSet):
    queryset = PharmacyInsuranceClaim.objects.all()
    serializer_class = PharmacyInsuranceClaimSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        claim = self.get_object()
        claim.approve_by_claims_officer(request.user, request.data.get('comments'))
        return Response({'detail': 'Approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        claim = self.get_object()
        claim.reject_by_claims_officer(request.user, request.data.get('reason', ''))
        return Response({'detail': 'Rejected'})


class InpatientInsuranceClaimViewSet(viewsets.ModelViewSet):
    queryset = InpatientInsuranceClaim.objects.all()
    serializer_class = InpatientInsuranceClaimSerializer


# ═══════════════════════════════════════════════════════
#  NOTIFICATION VIEWSET
# ═══════════════════════════════════════════════════════

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread(self, request):
        qs = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.mark_as_read()
        return Response({'detail': 'Marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'detail': 'All marked as read'})


# ═══════════════════════════════════════════════════════
#  PAYMENT VIEWSETS
# ═══════════════════════════════════════════════════════

class PaymentAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentAuditLog.objects.all()
    serializer_class = PaymentAuditLogSerializer

    def get_queryset(self):
        qs = PaymentAuditLog.objects.all()
        date_filter = self.request.query_params.get('date')
        if date_filter:
            qs = qs.filter(created_at__date=date_filter)
        user = self.request.user
        if user.user_type == 'CASHIER':
            qs = qs.filter(processed_by=user)
        return qs


class CashierSessionViewSet(viewsets.ModelViewSet):
    queryset = CashierSession.objects.all()
    serializer_class = CashierSessionSerializer

    def get_queryset(self):
        qs = CashierSession.objects.all()
        user = self.request.user
        if user.user_type == 'CASHIER':
            qs = qs.filter(cashier=user)
        return qs

    @action(detail=False, methods=['get'])
    def active(self, request):
        session = CashierSession.objects.filter(
            cashier=request.user, status='OPEN'
        ).first()
        if session:
            return Response(CashierSessionSerializer(session).data)
        return Response({'detail': 'No active session'}, status=404)


# ═══════════════════════════════════════════════════════
#  SHA VIEWSETS
# ═══════════════════════════════════════════════════════

class SHAMemberViewSet(viewsets.ModelViewSet):
    queryset = SHAMember.objects.all()
    serializer_class = SHAMemberSerializer

    def get_queryset(self):
        qs = SHAMember.objects.all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(sha_number__icontains=search) | Q(patient__first_name__icontains=search))
        return qs


class SHAClaimViewSet(viewsets.ModelViewSet):
    queryset = SHAClaim.objects.all()
    serializer_class = SHAClaimSerializer


# ═══════════════════════════════════════════════════════
#  ICD10 VIEWSET
# ═══════════════════════════════════════════════════════

class ICD10CodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ICD10Code.objects.filter(is_active=True)
    serializer_class = ICD10CodeSerializer

    def get_queryset(self):
        qs = ICD10Code.objects.filter(is_active=True)
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(short_description__icontains=search) |
                Q(local_name__icontains=search)
            )
        common = self.request.query_params.get('common')
        if common:
            qs = qs.filter(is_common=True)
        return qs[:50]  # Limit for performance


# ═══════════════════════════════════════════════════════
#  ATTENDANCE VIEWSETS
# ═══════════════════════════════════════════════════════

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = Attendance.objects.all()
        user = self.request.user
        if user.user_type not in ['ADMIN', 'HR']:
            qs = qs.filter(user=user)
        date_filter = self.request.query_params.get('date')
        if date_filter:
            qs = qs.filter(date=date_filter)
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)
        return qs

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            user=request.user, date=today,
            defaults={'status': 'PRESENT'}
        )
        if attendance.check_in_time:
            return Response({'error': 'Already checked in'}, status=400)
        attendance.check_in_time = timezone.now()
        attendance.status = 'PRESENT'
        attendance.check_in_ip = request.META.get('REMOTE_ADDR')
        attendance.save()
        return Response({'detail': 'Checked in', 'time': attendance.check_in_time})

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        today = timezone.now().date()
        try:
            attendance = Attendance.objects.get(user=request.user, date=today)
        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in found'}, status=400)
        if attendance.check_out_time:
            return Response({'error': 'Already checked out'}, status=400)
        attendance.check_out_time = timezone.now()
        attendance.check_out_ip = request.META.get('REMOTE_ADDR')
        attendance.calculate_hours()
        return Response({'detail': 'Checked out', 'hours': attendance.total_hours})


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    queryset = LeaveApplication.objects.all()
    serializer_class = LeaveApplicationSerializer

    def get_queryset(self):
        qs = LeaveApplication.objects.all()
        user = self.request.user
        if user.user_type not in ['ADMIN', 'HR']:
            qs = qs.filter(user=user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


# ═══════════════════════════════════════════════════════
#  DASHBOARD VIEWSET
# ═══════════════════════════════════════════════════════

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = timezone.now().date()
        data = {
            'total_patients': Patient.objects.count(),
            'today_visits': PatientVisit.objects.filter(arrival_time__date=today).count(),
            'active_admissions': InpatientAdmission.objects.filter(status='ACTIVE').count(),
            'pending_lab_orders': LabOrder.objects.filter(
                status__in=['PENDING', 'IN_PROGRESS'], created_at__date=today
            ).count(),
            'low_stock_medicines': sum(1 for m in Medicine.objects.all() if m.is_low_stock),
            'today_revenue': float(PaymentAuditLog.objects.filter(
                created_at__date=today, status='SUCCESS'
            ).aggregate(t=Sum('amount'))['t'] or 0),
            'pending_claims': (
                ConsultationInsuranceClaim.objects.filter(status='PENDING').count() +
                PharmacyInsuranceClaim.objects.filter(status='PENDING').count()
            ),
            'available_beds': Bed.objects.filter(status='AVAILABLE').count(),
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        today = timezone.now().date()
        return Response({
            'recent_visits': PatientVisitSerializer(
                PatientVisit.objects.filter(arrival_time__date=today).order_by('-arrival_time')[:5],
                many=True
            ).data,
            'recent_admissions': InpatientAdmissionSerializer(
                InpatientAdmission.objects.filter(status='ACTIVE').order_by('-admission_datetime')[:5],
                many=True
            ).data,
            'pending_lab': LabOrderSerializer(
                LabOrder.objects.filter(status='PENDING').order_by('-ordered_at')[:5],
                many=True
            ).data,
        })

    @action(detail=False, methods=['get'])
    def revenue_chart(self, request):
        days = int(request.query_params.get('days', 7))
        data = []
        for i in range(days - 1, -1, -1):
            day = timezone.now().date() - timedelta(days=i)
            revenue = PaymentAuditLog.objects.filter(
                created_at__date=day, status='SUCCESS'
            ).aggregate(t=Sum('amount'))['t'] or 0
            data.append({'date': str(day), 'revenue': float(revenue)})
        return Response(data)

    @action(detail=False, methods=['get'])
    def insurance_summary(self, request):
        return Response({
            'consultation_pending': ConsultationInsuranceClaim.objects.filter(status='PENDING').count(),
            'pharmacy_pending': PharmacyInsuranceClaim.objects.filter(status='PENDING').count(),
            'inpatient_pending': InpatientInsuranceClaim.objects.filter(status='PENDING').count(),
            'consultation_approved': ConsultationInsuranceClaim.objects.filter(status='APPROVED').count(),
            'pharmacy_approved': PharmacyInsuranceClaim.objects.filter(status='APPROVED').count(),
        })


# ═══════════════════════════════════════════════════════
#  MISC VIEWSETS
# ═══════════════════════════════════════════════════════

class InsuranceProviderViewSet(viewsets.ModelViewSet):
    queryset = InsuranceProvider.objects.all()
    serializer_class = InsuranceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]


class SpecializedServiceViewSet(viewsets.ModelViewSet):
    queryset = SpecializedService.objects.all()
    serializer_class = SpecializedServiceSerializer
    permission_classes = [permissions.IsAuthenticated]


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer

    def get_queryset(self):
        qs = StockMovement.objects.all()
        medicine_id = self.request.query_params.get('medicine')
        if medicine_id:
            qs = qs.filter(medicine_id=medicine_id)
        return qs.order_by('-created_at')[:100]