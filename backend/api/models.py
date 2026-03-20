from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta
import uuid
import random
import string

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('DOCTOR', 'Doctor'),
        ('RECEPTIONIST', 'Receptionist'),
        ('NURSE', 'nurse'),
        ('PROCUREMENT', 'Procurement Officer'),
        ('LAB_TECH', 'Lab Technician'),
        ('CASHIER', 'Cashier'),
        ('PHARMACIST', 'Pharmacist'),
        ('ACCOUNTANT', 'Accountant'),
        ('INSURANCE', 'Claims Officer'),
        ('HR', 'Human Resource Officer'),
    )
    
    user_type = models.CharField(max_length=12, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)  # For doctors
    license_number = models.CharField(max_length=50, blank=True, null=True)  # For doctors
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"


class LoginAttempt(models.Model):
    """
    Track login attempts for security purposes
    """
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Login attempt for {self.username} at {self.timestamp}"


class AccountLock(models.Model):
    """
    Track locked accounts
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_lock')
    locked_at = models.DateTimeField(auto_now_add=True)
    failed_attempts = models.PositiveIntegerField(default=0)
    last_attempt_ip = models.GenericIPAddressField(null=True, blank=True)
    unlock_time = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=True)
    
    def is_account_locked(self):
        if not self.is_locked:
            return False
        if self.unlock_time and timezone.now() > self.unlock_time:
            self.is_locked = False
            self.save()
            return False
        return True
    
    def __str__(self):
        return f"Account lock for {self.user.username}"


class TwoFactorCode(models.Model):
    """
    Store 2FA verification codes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tfa_codes')
    code = models.CharField(max_length=7)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    session_key = models.CharField(max_length=40)
    
    def save(self, *args, **kwargs):
        if not self.code:
            digits = ''.join(random.choices(string.digits, k=6))
            self.code = f"{digits[:3]}-{digits[3:]}"
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=2)
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        self.used = True
        self.used_at = timezone.now()
        self.save()
    
    def time_remaining(self):
        if self.is_expired():
            return 0
        return int((self.expires_at - timezone.now()).total_seconds())
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"2FA Code for {self.user.username} - {self.code}"


class SecurityNotification(models.Model):
    """
    Security-related notifications sent to users
    """
    NOTIFICATION_TYPES = (
        ('failed_login', 'Failed Login Attempt'),
        ('account_locked', 'Account Locked'),
        ('tfa_code', '2FA Code'),
        ('successful_login', 'Successful Login'),
        ('account_unlocked', 'Account Unlocked'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"



from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class Doctor(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Prefer Not to Say'),
    )
    
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    SPECIALIZATION_CHOICES = (
        ('GP', 'General Practitioner'),
        ('CAR', 'Cardiologist'),
        ('DER', 'Dermatologist'),
        ('PED', 'Pediatrician'),
        ('ORT', 'Orthopedic Surgeon'),
        ('NEU', 'Neurologist'),
        ('PSY', 'Psychiatrist'),
        ('ONC', 'Oncologist'),
        ('RAD', 'Radiologist'),
        ('EM', 'Emergency Medicine'),
        ('ANES', 'Anesthesiologist'),
        ('OBGYN', 'Obstetrician/Gynecologist'),
        ('ENT', 'ENT Specialist'),
    )
    
    # Personal Information
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    date_of_birth = models.DateField(_("Date of Birth"))
    gender = models.CharField(_("Gender"), max_length=1, choices=GENDER_CHOICES)
    id_number = models.CharField(_("ID Number"), max_length=20, unique=True)
    national_id = models.CharField(_("National ID"), max_length=20, blank=True, null=True)
    passport_number = models.CharField(_("Passport Number"), max_length=20, blank=True, null=True)
    
    # Contact Information
    phone_number = models.CharField(_("Phone Number"), max_length=15)
    alternate_phone = models.CharField(_("Alternate Phone"), max_length=15, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    emergency_contact = models.CharField(_("Emergency Contact"), max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(_("Emergency Phone"), max_length=15, blank=True, null=True)
    
    # Address Information
    address = models.TextField(_("Address"), blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    state = models.CharField(_("State/Province"), max_length=100, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True, null=True)
    
    # Medical Information
    blood_type = models.CharField(_("Blood Type"), max_length=5, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    allergies = models.TextField(_("Allergies"), blank=True, null=True)
    chronic_conditions = models.TextField(_("Chronic Conditions"), blank=True, null=True)
    
    # Professional Information
    specialization = models.CharField(_("Specialization"), max_length=10, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(_("Medical License Number"), max_length=50, unique=True)
    license_expiry = models.DateField(_("License Expiry Date"), blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(_("Years of Experience"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    qualifications = models.TextField(_("Qualifications"), blank=True, null=True)
    bio = models.TextField(_("Professional Bio"), blank=True, null=True)
    
    # Hospital/Clinic Affiliation
    is_active = models.BooleanField(_("Active Staff"), default=True)
    joining_date = models.DateField(_("Joining Date"), blank=True, null=True)
    department = models.CharField(_("Department"), max_length=100, blank=True, null=True)
    position = models.CharField(_("Position"), max_length=100, blank=True, null=True)
    
    # System Information
    profile_picture = models.ImageField(_("Profile Picture"), upload_to='doctors/profile_pictures/', blank=True, null=True)
    signature = models.ImageField(_("Signature"), upload_to='doctors/signatures/', blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    # Availability (could be moved to separate model if complex)
    working_days = models.CharField(_("Working Days"), max_length=100, blank=True, null=True,
                                  help_text="Comma separated days (e.g., Mon,Tue,Wed)")
    working_hours = models.CharField(_("Working Hours"), max_length=100, blank=True, null=True,
                                   help_text="e.g., 9:00 AM - 5:00 PM")
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.get_specialization_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        import datetime
        return datetime.date.today().year - self.date_of_birth.year - (
            (datetime.date.today().month, datetime.date.today().day) < 
            (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def license_status(self):
        if not self.license_expiry:
            return "Unknown"
        from datetime import date
        return "Valid" if self.license_expiry >= date.today() else "Expired"
    
    class Meta:
        verbose_name = _("Doctor")
        verbose_name_plural = _("Doctors")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['specialization']),
            models.Index(fields=['license_number']),
        ]


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class Nurse(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('U', 'Prefer Not to Say'),
    )
    
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    NURSE_TYPE_CHOICES = (
        ('RN', 'Registered Nurse'),
        ('LPN', 'Licensed Practical Nurse'),
        ('NP', 'Nurse Practitioner'),
        ('CNS', 'Clinical Nurse Specialist'),
        ('CRNA', 'Certified Registered Nurse Anesthetist'),
        ('CNM', 'Certified Nurse Midwife'),
        ('SN', 'Student Nurse'),
    )
    
    DEPARTMENT_CHOICES = (
        ('ER', 'Emergency Room'),
        ('ICU', 'Intensive Care Unit'),
        ('OR', 'Operating Room'),
        ('PED', 'Pediatrics'),
        ('OB', 'Obstetrics'),
        ('ONC', 'Oncology'),
        ('CAR', 'Cardiology'),
        ('PSY', 'Psychiatry'),
        ('GEN', 'General Ward'),
        ('OPD', 'Outpatient Department'),
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='nurse_profile',
        null=True,  # Temporarily allow null for existing records
        blank=True
    )
    
    # Personal Information
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    date_of_birth = models.DateField(_("Date of Birth"))
    gender = models.CharField(_("Gender"), max_length=1, choices=GENDER_CHOICES)
    national_id = models.CharField(_("National ID"), max_length=20, blank=True, null=True)
    nurse_id = models.CharField(_("Nurse ID"), max_length=20, unique=True)
    
    # Contact Information
    phone_number = models.CharField(_("Phone Number"), max_length=15)
    alternate_phone = models.CharField(_("Alternate Phone"), max_length=15, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    emergency_contact = models.CharField(_("Emergency Contact"), max_length=100, blank=True, null=True)
    emergency_relation = models.CharField(_("Relationship"), max_length=50, blank=True, null=True)
    emergency_phone = models.CharField(_("Emergency Phone"), max_length=15, blank=True, null=True)
    
    # Address Information
    address = models.TextField(_("Address"), blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    state = models.CharField(_("State/Province"), max_length=100, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True, null=True)
    
    # Medical Information
    blood_type = models.CharField(_("Blood Type"), max_length=5, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    allergies = models.TextField(_("Allergies"), blank=True, null=True)
    chronic_conditions = models.TextField(_("Chronic Conditions"), blank=True, null=True)
    
    # Professional Information
    nurse_type = models.CharField(_("Nurse Type"), max_length=5, choices=NURSE_TYPE_CHOICES)
    license_number = models.CharField(_("License Number"), max_length=50, unique=True)
    license_expiry = models.DateField(_("License Expiry Date"), blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(
        _("Years of Experience"), 
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        default=0
    )
    department = models.CharField(_("Department"), max_length=5, choices=DEPARTMENT_CHOICES)
    specialization = models.CharField(_("Specialization"), max_length=100, blank=True, null=True)
    certifications = models.TextField(_("Certifications"), blank=True, null=True)
    bio = models.TextField(_("Professional Bio"), blank=True, null=True)
    
    # Employment Details
    is_active = models.BooleanField(_("Active Staff"), default=True)
    joining_date = models.DateField(_("Joining Date"), blank=True, null=True)
    position = models.CharField(_("Position"), max_length=100, blank=True, null=True)
    shift_pattern = models.CharField(_("Shift Pattern"), max_length=100, blank=True, null=True)
    is_charge_nurse = models.BooleanField(_("Charge Nurse"), default=False)
    
    # Skills and Competencies
    is_bcls_certified = models.BooleanField(_("BCLS Certified"), default=False)
    is_acl_certified = models.BooleanField(_("ACLS Certified"), default=False)
    is_pals_certified = models.BooleanField(_("PALS Certified"), default=False)
    additional_skills = models.TextField(_("Additional Skills"), blank=True, null=True)
    
    # System Information
    profile_picture = models.ImageField(
        _("Profile Picture"), 
        upload_to='nurses/profile_pictures/', 
        blank=True, 
        null=True
    )
    signature = models.ImageField(
        _("Signature"), 
        upload_to='nurses/signatures/', 
        blank=True, 
        null=True
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"Nurse {self.first_name} {self.last_name} ({self.get_nurse_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        import datetime
        return datetime.date.today().year - self.date_of_birth.year - (
            (datetime.date.today().month, datetime.date.today().day) < 
            (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def license_status(self):
        if not self.license_expiry:
            return "Unknown"
        from datetime import date
        return "Valid" if self.license_expiry >= date.today() else "Expired"
    
    class Meta:
        verbose_name = _("Nurse")
        verbose_name_plural = _("Nurses")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['nurse_type']),
            models.Index(fields=['department']),
            models.Index(fields=['license_number']),
        ]

     
class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    id_number = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    blood_type = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.id_number})"
    
    class Meta:
        ordering = ['-created_at']

class Disease(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icd_code = models.CharField(max_length=20, blank=True, null=True)  # International Classification of Diseases code
    
    def __str__(self):
        return self.name

class MedicineCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Medicine(models.Model):
    """
    Enhanced Medicine model with built-in packaging info
    """
    # Basic Info
    name = models.CharField(max_length=200)
    category = models.ForeignKey('MedicineCategory', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    
    # Packaging Information (Simple & Clear)
    UNIT_TYPE_CHOICES = (
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('SYRUP_ML', 'Syrup (ML)'),
        ('INJECTION', 'Injection'),
        ('CREAM_TUBE', 'Cream/Ointment (Tube)'),
        ('DROPS', 'Drops'),
        ('SACHET', 'Sachet'),
        ('SUPPOSITORY', 'Suppository'),
    )
    
    unit_type = models.CharField(
        _("Unit Type"),
        max_length=20,
        choices=UNIT_TYPE_CHOICES,
        help_text="What is being sold (tablet, capsule, ml, etc.)"
    )
    
    # Packaging Details
    units_per_pack = models.IntegerField(
        _("Units Per Pack"),
        default=10,
        help_text="e.g., 10 tablets per strip, 100ml per bottle"
    )
    pack_name = models.CharField(
        _("Pack Name"),
        max_length=50,
        default="Strip",
        help_text="e.g., Strip, Bottle, Box, Blister"
    )
    
    # Stock - Track in UNITS (individual tablets/ml/etc)
    quantity_in_stock = models.PositiveIntegerField(
        _("Quantity in Stock (Units)"),
        default=0,
        help_text="Total individual units available (e.g., total tablets)"
    )
    reorder_level = models.PositiveIntegerField(default=100)
    
    cost_per_unit_cash= models.DecimalField(max_digits=10, decimal_places=2 , default= 0, help_text='bying price')
    
    # CASH PRICING (What uninsured patients pay)
    price_per_unit_cash = models.DecimalField(
        _("Cash Price Per Unit (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price per single unit for cash patients (e.g., per tablet)"
    )
    
    # INSURANCE PRICING (What insurance covers)
    price_per_unit_insurance = models.DecimalField(
        _("Insurance Price Per Unit (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price per single unit for insured patients"
    )
    
    # Display image for doctors
    image = models.ImageField(
        upload_to='medicine_images/', 
        blank=True, 
        null=True,
        help_text="Show doctors what the medicine looks like"
    )
    
    # Other fields
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.units_per_pack} {self.get_unit_type_display()} per {self.pack_name})"
    
    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level
    
    @property
    def packs_in_stock(self):
        """How many complete packs available"""
        return self.quantity_in_stock // self.units_per_pack
    
    @property
    def loose_units_in_stock(self):
        """Remaining units after complete packs"""
        return self.quantity_in_stock % self.units_per_pack
    
    @property
    def price_per_pack_cash(self):
        """Calculate pack price for cash patients"""
        return self.price_per_unit_cash * self.units_per_pack
    
    @property
    def price_per_pack_insurance(self):
        """Calculate pack price for insured patients"""
        return self.price_per_unit_insurance * self.units_per_pack
    
    def calculate_price(self, quantity_units, is_insured=False):
        """
        Calculate total price for given quantity
        
        Args:
            quantity_units: Number of units to dispense (e.g., 30 tablets)
            is_insured: Whether patient has insurance
        
        Returns:
            dict with pricing breakdown
        """
        if quantity_units <= 0:
            return {'error': 'Quantity must be greater than 0'}
        
        if quantity_units > self.quantity_in_stock:
            return {'error': f'Insufficient stock. Available: {self.quantity_in_stock} {self.get_unit_type_display()}'}
        
        # Choose price based on insurance status
        price_per_unit = self.price_per_unit_insurance if is_insured else self.price_per_unit_cash
        
        # Calculate
        total_price = quantity_units * price_per_unit
        full_packs = quantity_units // self.units_per_pack
        loose_units = quantity_units % self.units_per_pack
        
        return {
            'medicine_name': self.name,
            'unit_type': self.get_unit_type_display(),
            'pack_name': self.pack_name,
            'units_per_pack': self.units_per_pack,
            
            'quantity_requested': quantity_units,
            'full_packs': full_packs,
            'loose_units': loose_units,
            
            'price_per_unit': float(price_per_unit),
            'total_price': float(total_price),
            
            'is_insured': is_insured,
            'payment_type': 'Insurance' if is_insured else 'Cash',
            
            'stock_available': self.quantity_in_stock,
            'can_dispense': True,
            
            # Human readable summary
            'summary': self.get_prescription_summary(quantity_units, is_insured)
        }
    
    def get_prescription_summary(self, quantity_units, is_insured):
        """
        Generate human-readable prescription summary
        """
        full_packs = quantity_units // self.units_per_pack
        loose_units = quantity_units % self.units_per_pack
        
        price_per_unit = self.price_per_unit_insurance if is_insured else self.price_per_unit_cash
        total_price = quantity_units * price_per_unit
        
        parts = []
        if full_packs > 0:
            parts.append(f"{full_packs} {self.pack_name}(s)")
        if loose_units > 0:
            parts.append(f"{loose_units} loose {self.get_unit_type_display()}(s)")
        
        packaging = " + ".join(parts) if parts else f"{quantity_units} {self.get_unit_type_display()}(s)"
        
        return f"{packaging} = KSh {total_price:,.2f} ({'Insurance' if is_insured else 'Cash'})"

class StockMovement(models.Model):
    """
    Track all medicine stock movements for audit trail
    """
    MOVEMENT_TYPE_CHOICES = (
        ('PURCHASE', 'Purchase/Received'),
        ('SALE', 'Sale/Dispensed'),
        ('ADJUSTMENT', 'Adjustment'),
        ('RETURN', 'Return'),
        ('DAMAGE', 'Damage/Expired'),
        ('TRANSFER', 'Transfer'),
    )
    
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    movement_type = models.CharField(
        _("Movement Type"),
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES
    )
    quantity = models.IntegerField(_("Quantity"))
    previous_quantity = models.IntegerField(_("Previous Stock"))
    new_quantity = models.IntegerField(_("New Stock"))
    
    # References
    medicine_sale = models.ForeignKey(
        'MedicineSale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    goods_received_note = models.ForeignKey(
        'GoodsReceivedNote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    
    reason = models.TextField(_("Reason/Notes"), blank=True, null=True)
    batch_number = models.CharField(_("Batch Number"), max_length=100, blank=True, null=True)
    
    performed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements_performed'
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Stock Movement")
        verbose_name_plural = _("Stock Movements")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.medicine.name} ({self.quantity})"


# for this medicine packing model am not using it now because i have simplified it in medicine model kindly take note


from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class MedicinePackaging(models.Model):
    """
    Defines how medicines are packaged and sold
    e.g., Paracetamol comes in bottles of 100 tablets
    """
    PACKAGING_TYPE_CHOICES = (
        ('BOTTLE', 'Bottle'),
        ('BLISTER_PACK', 'Blister Pack'),
        ('STRIP', 'Strip'),
        ('VIAL', 'Vial'),
        ('AMPULE', 'Ampule'),
        ('SACHET', 'Sachet'),
        ('TUBE', 'Tube'),
        ('BOX', 'Box'),
        ('CARTON', 'Carton'),
        ('PACKET', 'Packet'),
    )
    
    UNIT_TYPE_CHOICES = (
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('ML', 'Milliliter (ml)'),
        ('MG', 'Milligram (mg)'),
        ('G', 'Gram (g)'),
        ('SACHET', 'Sachet'),
        ('DOSE', 'Dose'),
        ('APPLICATION', 'Application'),
        ('UNIT', 'Unit'),
    )
    
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.CASCADE,
        related_name='packaging_options'
    )
    
    # Packaging details
    packaging_type = models.CharField(
        _("Packaging Type"),
        max_length=20,
        choices=PACKAGING_TYPE_CHOICES
    )
    unit_type = models.CharField(
        _("Unit Type"),
        max_length=20,
        choices=UNIT_TYPE_CHOICES,
        help_text="What is being counted (tablets, ml, etc.)"
    )
    
    # Quantity per package
    units_per_package = models.IntegerField(
        _("Units Per Package"),
        validators=[MinValueValidator(1)],
        help_text="e.g., 100 tablets per bottle, 10 tablets per strip"
    )
    
    # Pricing
    package_cost_price = models.DecimalField(
        _("Package Cost Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="What the hospital paid for this package"
    )
    package_selling_price = models.DecimalField(
        _("Package Selling Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="What patients pay for full package"
    )
    
    # Calculated prices per unit
    cost_per_unit = models.DecimalField(
        _("Cost Per Unit (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False
    )
    selling_price_per_unit = models.DecimalField(
        _("Selling Price Per Unit (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Stock tracking
    packages_in_stock = models.IntegerField(
        _("Packages in Stock"),
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Is this the default/primary packaging?
    is_primary = models.BooleanField(
        _("Primary Packaging"),
        default=False,
        help_text="Default packaging shown to doctors"
    )
    
    # Can we sell partial packages?
    allow_partial_sales = models.BooleanField(
        _("Allow Partial Sales"),
        default=True,
        help_text="Can we sell individual units (e.g., 5 tablets from a strip)?"
    )
    
    # Minimum quantity rules
    minimum_dispensable_units = models.IntegerField(
        _("Minimum Dispensable Units"),
        default=1,
        help_text="Minimum number of units that can be dispensed"
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Medicine Packaging")
        verbose_name_plural = _("Medicine Packaging Options")
        ordering = ['-is_primary', 'packaging_type']
        indexes = [
            models.Index(fields=['medicine', 'is_active']),
            models.Index(fields=['is_primary']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate per-unit prices
        if self.units_per_package > 0:
            self.cost_per_unit = self.package_cost_price / self.units_per_package
            self.selling_price_per_unit = self.package_selling_price / self.units_per_package
        
        # Ensure only one primary packaging per medicine
        if self.is_primary:
            MedicinePackaging.objects.filter(
                medicine=self.medicine,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.units_per_package} {self.get_unit_type_display()} per {self.get_packaging_type_display()}"
    
    @property
    def total_units_in_stock(self):
        """Calculate total units available"""
        return self.packages_in_stock * self.units_per_package
    
    @property
    def profit_margin_percentage(self):
        """Calculate profit margin"""
        if self.cost_per_unit > 0:
            profit = self.selling_price_per_unit - self.cost_per_unit
            return round((profit / self.cost_per_unit) * 100, 2)
        return 0
    
    def calculate_price_for_quantity(self, quantity_units):
        """
        Calculate total price for a given quantity of units
        Returns dict with full breakdown
        """
        if quantity_units <= 0:
            return None
        
        # Check if we can sell this quantity
        if not self.allow_partial_sales and quantity_units < self.units_per_package:
            return {
                'error': f"Cannot sell partial {self.get_packaging_type_display()}. "
                        f"Minimum: {self.units_per_package} {self.get_unit_type_display()}"
            }
        
        if quantity_units < self.minimum_dispensable_units:
            return {
                'error': f"Minimum dispensable quantity is {self.minimum_dispensable_units} {self.get_unit_type_display()}"
            }
        
        # Calculate full packages and loose units
        full_packages = quantity_units // self.units_per_package
        loose_units = quantity_units % self.units_per_package
        
        # Calculate pricing
        total_price = quantity_units * self.selling_price_per_unit
        total_cost = quantity_units * self.cost_per_unit
        profit = total_price - total_cost
        
        return {
            'packaging_type': self.get_packaging_type_display(),
            'unit_type': self.get_unit_type_display(),
            'quantity_requested': quantity_units,
            'full_packages': full_packages,
            'loose_units': loose_units,
            'units_per_package': self.units_per_package,
            'price_per_unit': float(self.selling_price_per_unit),
            'price_per_package': float(self.package_selling_price),
            'total_price': float(total_price),
            'total_cost': float(total_cost),
            'profit': float(profit),
            'profit_margin': self.profit_margin_percentage,
            'available_stock': self.total_units_in_stock,
            'sufficient_stock': self.total_units_in_stock >= quantity_units,
            'can_dispense': self.total_units_in_stock >= quantity_units and quantity_units >= self.minimum_dispensable_units,
        }


class DosageGuideline(models.Model):
    """
    Help doctors prescribe correct quantities
    Shows standard dosing for different conditions
    """
    FREQUENCY_CHOICES = (
        ('OD', 'Once Daily (OD)'),
        ('BD', 'Twice Daily (BD)'),
        ('TDS', 'Three Times Daily (TDS)'),
        ('QID', 'Four Times Daily (QID)'),
        ('PRN', 'As Needed (PRN)'),
        ('STAT', 'Immediately (STAT)'),
    )
    
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='dosage_guidelines'
    )
    
    # What is this for?
    indication = models.CharField(
        _("Indication/Condition"),
        max_length=200,
        help_text="e.g., 'Headache', 'Malaria', 'Hypertension'"
    )
    
    # Dosing
    dose_per_time = models.IntegerField(
        _("Dose Per Time"),
        help_text="Number of units per dose (e.g., 2 tablets)"
    )
    frequency = models.CharField(
        _("Frequency"),
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='BD'
    )
    duration_days = models.IntegerField(
        _("Duration (Days)"),
        default=7,
        help_text="How many days to take the medicine"
    )
    
    # Instructions
    instructions = models.TextField(
        _("Instructions"),
        help_text="e.g., 'Take with food', 'Take on empty stomach'"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['medicine', 'indication']
    
    def __str__(self):
        return f"{self.medicine.name} - {self.indication}"
    
    @property
    def total_units_needed(self):
        """Calculate total units needed for this course"""
        frequency_map = {
            'OD': 1,
            'BD': 2,
            'TDS': 3,
            'QID': 4,
            'PRN': 2,  # Approximate
            'STAT': 1,
        }
        
        doses_per_day = frequency_map.get(self.frequency, 2)
        total = self.dose_per_time * doses_per_day * self.duration_days
        return total
    
    @property
    def prescription_text(self):
        """Generate prescription text for doctor"""
        return (
            f"{self.dose_per_time} {self.medicine.get_unit_type_display()}(s) "
            f"{self.get_frequency_display()} for {self.duration_days} days"
        )
    
    def calculate_total_cost(self, is_insured=False):
        """Calculate cost for this guideline"""
        return self.medicine.calculate_price(
            self.total_units_needed,
            is_insured
        )

 

# Add after the MedicinePackaging model

class InsuranceMedicinePrice(models.Model):
    """
    OPTIONAL: Override insurance prices for specific providers
    If not set, uses medicine.price_per_unit_insurance
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    insurance_provider = models.ForeignKey('InsuranceProvider', on_delete=models.CASCADE)
    
    price_per_unit = models.DecimalField(
        _("Price Per Unit (KSh)"),
        max_digits=10,
        decimal_places=2,
        help_text="Special price for this insurance company"
    )
    
    is_covered = models.BooleanField(_("Covered"), default=True)
    max_quantity_per_month = models.IntegerField(
        _("Max Quantity Per Month"),
        blank=True,
        null=True,
        help_text="Leave blank for unlimited"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['medicine', 'insurance_provider']
    
    def __str__(self):
        return f"{self.medicine.name} - {self.insurance_provider.name}: KSh {self.price_per_unit}/unit"


class PrescriptionInsuranceBreakdown(models.Model):
    """
    Insurance pricing breakdown for prescriptions
    Extends PrescriptionPricingBreakdown with insurance details
    """
    prescription = models.OneToOneField(
        'Prescription',
        on_delete=models.CASCADE,
        related_name='insurance_breakdown'
    )
    
    insurance_price = models.ForeignKey(
        InsuranceMedicinePrice,
        on_delete=models.PROTECT,
        related_name='prescription_breakdowns'
    )
    
    # Quantity details (same as base prescription)
    quantity_units = models.IntegerField(_("Quantity (Units)"))
    
    # Insurance pricing
    insurance_price_per_unit = models.DecimalField(
        _("Insurance Price Per Unit (KSh)"),
        max_digits=10,
        decimal_places=2
    )
    total_insurance_price = models.DecimalField(
        _("Total Insurance Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        help_text="Total amount before co-pay"
    )
    
    # Patient co-payment
    patient_copay_amount = models.DecimalField(
        _("Patient Co-pay Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        help_text="Amount patient must pay"
    )
    
    # Insurance payment
    insurance_pays_amount = models.DecimalField(
        _("Insurance Pays (KSh)"),
        max_digits=10,
        decimal_places=2,
        help_text="Amount insurance company pays"
    )
    
    # Authorization
    requires_preauthorization = models.BooleanField(
        _("Requires Pre-authorization"),
        default=False
    )
    preauthorization_code = models.CharField(
        _("Pre-authorization Code"),
        max_length=100,
        blank=True,
        null=True
    )
    preauthorization_approved = models.BooleanField(
        _("Pre-authorization Approved"),
        default=False
    )
    preauthorization_date = models.DateTimeField(
        _("Pre-authorization Date"),
        blank=True,
        null=True
    )
    
    # Claim tracking
    claim_submitted = models.BooleanField(_("Claim Submitted"), default=False)
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=100,
        blank=True,
        null=True
    )
    claim_approved = models.BooleanField(_("Claim Approved"), default=False)
    claim_paid = models.BooleanField(_("Claim Paid"), default=False)
    
    # Dispensing status
    is_dispensed = models.BooleanField(_("Dispensed"), default=False)
    dispensed_at = models.DateTimeField(_("Dispensed At"), blank=True, null=True)
    dispensed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_insurance_prescriptions'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Prescription Insurance Breakdown")
        verbose_name_plural = _("Prescription Insurance Breakdowns")
        ordering = ['-created_at']
    
    def __str__(self):
        return (f"{self.prescription.medicine.name} - "
                f"{self.insurance_price.insurance_provider.name} - "
                f"Patient pays KSh {self.patient_copay_amount}")
    
    @property
    def patient_savings(self):
        """Calculate how much patient saves with insurance"""
        regular_price = (
            self.quantity_units * 
            self.insurance_price.packaging.selling_price_per_unit
        )
        return regular_price - self.patient_copay_amount


class InsurancePriceHistory(models.Model):
    """
    Track historical insurance pricing changes for audit
    """
    insurance_price = models.ForeignKey(
        InsuranceMedicinePrice,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    
    # Previous values
    old_package_price = models.DecimalField(
        _("Old Package Price (KSh)"),
        max_digits=10,
        decimal_places=2
    )
    new_package_price = models.DecimalField(
        _("New Package Price (KSh)"),
        max_digits=10,
        decimal_places=2
    )
    old_copay_percentage = models.DecimalField(
        _("Old Co-pay %"),
        max_digits=5,
        decimal_places=2
    )
    new_copay_percentage = models.DecimalField(
        _("New Co-pay %"),
        max_digits=5,
        decimal_places=2
    )
    
    change_reason = models.TextField(_("Reason for Change"))
    changed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(_("Changed At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Insurance Price History")
        verbose_name_plural = _("Insurance Price Histories")
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.insurance_price.medicine.name} - {self.changed_at}"
    
        
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'DOCTOR'})
    receptionist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_appointments', limit_choices_to={'user_type': 'RECEPTIONIST'})
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    reason = models.TextField()
    symptoms = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} with Dr. {self.doctor.last_name} at {self.scheduled_time}"
    
    class Meta:
        ordering = ['scheduled_time']

import random
import string

class Consultation(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    diagnosis = models.TextField()
    diseases = models.ManyToManyField(Disease, blank=True)
    notes = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)
    follow_up_notes = models.TextField(blank=True, null=True)
    consultation_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Consultation for {self.appointment.patient} on {self.created_at.date()}"
    
    def generate_unique_code(self):
        while True:
            code = 'R' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if not Consultation.objects.filter(consultation_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        # Check if this is a new consultation
        is_new = self.pk is None
        
        # Generate unique code if needed
        if not self.consultation_code:
            self.consultation_code = self.generate_unique_code()
        
        # Save the consultation first
        super().save(*args, **kwargs)
        
        # Only create medical history for new consultations
        if is_new:
            self._create_medical_history()
    
    def _create_medical_history(self):
        """
        Create a single comprehensive medical history entry for this consultation
        """
        # Build comprehensive description
        history_parts = []
        
        if self.diagnosis:
            history_parts.append(f"Diagnosis: {self.diagnosis}")
        
        if self.notes and self.notes.strip():
            history_parts.append(f"Notes: {self.notes}")
        
        # Combine all information into one entry
        if history_parts:
            full_description = " | ".join(history_parts)
            
            # Create only one medical history entry
            PatientMedicalHistory.objects.create(
                patient=self.appointment.patient,
                consultation=self,
                record_type="Consultation Record",
                description=full_description,
                recorded_by=self.appointment.doctor,
            )


class Prescription(models.Model):
    """
    SIMPLIFIED Prescription - just the essentials
    """
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    # What doctor prescribes (in UNITS - tablets/ml/etc)
    quantity = models.PositiveIntegerField(
        _("Quantity (Units)"),
        validators=[MinValueValidator(1)],
        help_text="Total units to dispense (e.g., 30 tablets)"
    )
    
    # Instructions
    dosage_text = models.CharField(
        _("Dosage"),
        max_length=200,
        help_text="e.g., '2 tablets twice daily'"
    )
    duration = models.CharField(
        _("Duration"),
        max_length=100,
        help_text="e.g., '7 days', '2 weeks'"
    )
    instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Special instructions"
    )
    
    # Pricing - Calculated when dispensed
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price per unit when dispensed"
    )
    total_price = models.DecimalField(
        _("Total Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Insurance
    is_insured = models.BooleanField(_("Insured"), default=False)
    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Status
    is_dispensed = models.BooleanField(_("Dispensed"), default=False)
    dispensed_at = models.DateTimeField(blank=True, null=True)
    dispensed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_prescriptions'
    )
    
    prescribed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-prescribed_at']
    
    def __str__(self):
        return f"{self.medicine.name} x{self.quantity} for {self.consultation.appointment.patient}"
    
    def calculate_and_save_price(self):
        """
        Calculate price based on quantity and insurance status
        Call this before dispensing
        """
        pricing = self.medicine.calculate_price(
            self.quantity,
            self.is_insured
        )
        
        if 'error' in pricing:
            raise ValueError(pricing['error'])
        
        self.unit_price = Decimal(str(pricing['price_per_unit']))
        self.total_price = Decimal(str(pricing['total_price']))
        self.save()
    
    def dispense(self, user):
        """
        Dispense the medication
        """
        from django.utils import timezone
        
        # Check stock
        if self.quantity > self.medicine.quantity_in_stock:
            raise ValueError(f"Insufficient stock. Available: {self.medicine.quantity_in_stock}")
        
        # Calculate price
        self.calculate_and_save_price()
        
        # Reduce stock
        self.medicine.quantity_in_stock -= self.quantity
        self.medicine.save()
        
        # Mark as dispensed
        self.is_dispensed = True
        self.dispensed_at = timezone.now()
        self.dispensed_by = user
        self.save()
        
        # Create stock movement
        StockMovement.objects.create(
            medicine=self.medicine,
            movement_type='SALE',
            quantity=-self.quantity,
            previous_quantity=self.medicine.quantity_in_stock + self.quantity,
            new_quantity=self.medicine.quantity_in_stock,
            medicine_sale=None,  # Link if needed
            reason=f"Prescription for {self.consultation.appointment.patient}",
            performed_by=user
        )
    
    @property
    def packaging_breakdown(self):
        """Show how prescription breaks down into packs"""
        full_packs = self.quantity // self.medicine.units_per_pack
        loose_units = self.quantity % self.medicine.units_per_pack
        
        parts = []
        if full_packs > 0:
            parts.append(f"{full_packs} {self.medicine.pack_name}(s)")
        if loose_units > 0:
            parts.append(f"{loose_units} loose {self.medicine.get_unit_type_display()}(s)")
        
        return " + ".join(parts) if parts else f"{self.quantity} {self.medicine.get_unit_type_display()}(s)"


class MedicineSale(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Cash'),
        ('MPESA', 'M-Pesa'),
        ('INSURANCE', 'Insurance'),
        ('CREDIT', 'Credit'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    receptionist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'user_type': 'RECEPTIONIST'})
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    mpesa_number = models.CharField(max_length=15, blank=True, null=True)
    mpesa_code = models.CharField(max_length=50, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(default=timezone.now)  # instead of auto_now_add=True
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"
    
    class Meta:
        ordering = ['-sale_date']

class SoldMedicine(models.Model):
    sale = models.ForeignKey(MedicineSale, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.medicine.name} in Sale #{self.sale.id}"
    
    @property
    def total_price(self):
        return self.quantity * self.unit_price

class PatientMedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, blank=True, null=True)
    record_type = models.CharField(max_length=100)  # e.g., "Allergy", "Surgery", "Chronic Condition"
    description = models.TextField()
    date_recorded = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        # Prevent duplicate entries for the same consultation and record type
        unique_together = ['patient', 'consultation', 'record_type']
    
    def __str__(self):
        return f"{self.record_type} for {self.patient}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('APPOINTMENT', 'New Appointment'),
        ('LOW_STOCK', 'Low Stock Alert'),
        ('FOLLOW_UP', 'Follow Up Reminder'),
        ('GENERAL', 'General Notification'),
        ('QUEUE_CALL', 'Patient Call'),
        ('CONSULTATION', 'Consultation Update'),
        ('LAB_RESULT', 'Lab Result Ready'),
        ('PRESCRIPTION', 'Prescription Ready'),
    )
    
    # Recipient information
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    
    # Sender information (who triggered the notification)
    sender = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_notifications',
        verbose_name='Sent By'
    )
    
    # Patient context (if applicable)
    patient = models.ForeignKey(
        'Patient', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications',
        verbose_name='Related Patient'
    )
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200, blank=True, null=True)  # Short title for the notification
    message = models.TextField()
    
    # Related object tracking
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'appointment', 'queue', 'consultation'
    
    # Status and metadata
    is_read = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    action_url = models.CharField(max_length=500, blank=True, null=True)  # URL for notification action
    expires_at = models.DateTimeField(blank=True, null=True)  # When notification becomes irrelevant
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        sender_name = self.sender.get_full_name() if self.sender else "System"
        patient_name = f" for {self.patient.first_name} {self.patient.last_name}" if self.patient else ""
        return f"{self.notification_type} from {sender_name}{patient_name}"
    
    @property
    def sender_name(self):
        """Get formatted sender name"""
        if self.sender:
            return self.sender.get_full_name() or f"{self.sender.first_name} {self.sender.last_name}"
        return "System"
    
    @property
    def patient_name(self):
        """Get formatted patient name"""
        if self.patient:
            return f"{self.patient.first_name} {self.patient.last_name}"
        return None
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    @property
    def time_since_created(self):
        """Get human-readable time since creation"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(self.created_at)
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()
    
    def get_absolute_url(self):
        """Get action URL for the notification"""
        if self.action_url:
            return self.action_url
        
        # Default URLs based on notification type
        url_map = {
            'APPOINTMENT': f'/appointments/{self.related_object_id}/',
            'QUEUE_CALL': '/consultation-queue/',
            'CONSULTATION': f'/consultations/{self.related_object_id}/',
            'LAB_RESULT': f'/lab/results/{self.related_object_id}/',
            'PRESCRIPTION': f'/pharmacy/prescriptions/{self.related_object_id}/',
        }
        return url_map.get(self.notification_type, '#')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['patient', 'created_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

class ClinicSettings(models.Model):
    clinic_name = models.CharField(max_length=200)
    clinic_logo = models.ImageField(upload_to='clinic_logos/', blank=True, null=True)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    working_hours = models.TextField()
    appointment_duration = models.PositiveIntegerField(default=30, help_text="Default appointment duration in minutes")
    max_patients_per_day = models.PositiveIntegerField(default=20)
    
    def __str__(self):
        return self.clinic_name
    
    class Meta:
        verbose_name_plural = "Clinic Settings"

class DoctorSchedule(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_patients = models.IntegerField(default=20)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    

class DoctorLeave(models.Model):
    LEAVE_TYPE = [
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation'),
        ('conference', 'Conference'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE)
    reason = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.doctor} - {self.leave_type} ({self.start_date} to {self.end_date})"
    


class WorkloadSummary(models.Model):
    """Daily workload summary for doctors"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    total_hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    workload_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'date']
    
    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.workload_percentage}% workload)"
    

from django.db import models
from django.utils import timezone
import uuid


class OverTheCounterSale(models.Model):
    """
    Model for tracking over-the-counter medicine sales where detailed patient 
    information is not required.
    """
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    sale_id = models.CharField(max_length=50, unique=True, editable=False)
    customer_name = models.CharField(max_length=100)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    cashier = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='otc_sales')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_dispensed = models.BooleanField(_("Dispensed"), default=False)
    dispensed_at = models.DateTimeField(_("Dispensed At"), blank=True, null=True)
    dispensed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_otc_sales',
        limit_choices_to={'user_type': 'PHARMACIST'})
    
    def save(self, *args, **kwargs):
        # Generate a unique sale ID if not already set
        if not self.sale_id:
            today = timezone.now().strftime('%Y%m%d')
            self.sale_id = f"OTC-{today}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sale_id} - {self.customer_name}"
    
    @property
    def get_items_count(self):
        return self.items.count()
    
    @property
    def get_items(self):
        return self.items.all()


class OverTheCounterSaleItem(models.Model):
    """
    Model for tracking individual medicine items in an over-the-counter sale.
    """
    sale = models.ForeignKey(OverTheCounterSale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('Medicine', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calculate subtotal before saving
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
    
    class Meta:
        ordering = ['created_at']


class Conversation(models.Model):
    participant1 = models.ForeignKey(User, related_name='conversations_as_participant1', on_delete=models.CASCADE)
    participant2 = models.ForeignKey(User, related_name='conversations_as_participant2', on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant1', 'participant2', 'patient')

    def __str__(self):
        return f"Conversation between {self.participant1} and {self.participant2}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"

class ReceptionQueue(models.Model):
    receptionist = models.ForeignKey(User, on_delete=models.CASCADE)
    current_patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Queue for {self.receptionist}"
    
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from .models import Patient, Doctor, Nurse, User  # Import from existing models


class TriageCategory(models.Model):
    """
    Triage categories following Kenyan hospital standards
    Based on Emergency Severity Index (ESI) and color-coded system
    """
    PRIORITY_CHOICES = (
        (1, 'Red - Emergency (Immediate)'),
        (2, 'Orange - Very Urgent (10 mins)'),
        (3, 'Yellow - Urgent (30 mins)'),
        (4, 'Green - Standard (60 mins)'),
        (5, 'Blue - Non-Urgent (120 mins)'),
    )
    
    COLOR_CHOICES = (
        ('RED', 'Red'),
        ('ORANGE', 'Orange'),
        ('YELLOW', 'Yellow'),
        ('GREEN', 'Green'),
        ('BLUE', 'Blue'),
    )
    
    priority_level = models.IntegerField(
        _("Priority Level"), 
        choices=PRIORITY_CHOICES, 
        unique=True
    )
    color_code = models.CharField(
        _("Color Code"), 
        max_length=10, 
        choices=COLOR_CHOICES
    )
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(_("Description"))
    max_wait_time = models.IntegerField(
        _("Maximum Wait Time (minutes)"),
        help_text="Expected maximum wait time in minutes"
    )
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("Triage Category")
        verbose_name_plural = _("Triage Categories")
        ordering = ['priority_level']
    
    def __str__(self):
        return f"{self.color_code} - {self.name} (Priority {self.priority_level})"

class SpecializedService(models.Model):
    """
    Defines a specialist service and its consultation fee
    e.g Cardiologist, Pediatrician, Dentist
    """
    name = models.CharField(max_length=100, unique=True)
    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Consultation fee for this specialty"
    )

    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Specialized Service"
        verbose_name_plural = "Specialized Services"

    def __str__(self):
        return f"{self.name} - KES {self.consultation_fee}"

class InsuranceProvider(models.Model):
    """
    Stores Insurance companies eg SHA, Jubilee, AAR, Britam
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Insurance Provider"
        verbose_name_plural = "Insurance Providers"

    def __str__(self):
        return self.name

class PatientVisit(models.Model):
    """
    Tracks each patient visit to the hospital
    Separate from appointments - handles walk-ins and emergency cases
    """
    VISIT_TYPE_CHOICES = (
        ('EMERGENCY', 'Emergency'), #casuality/ trauma
        ('OUTPATIENT', 'Outpatient'),# Noraml OPD 
        ('INPATIENT', 'Inpatient'),
        ('FOLLOW_UP', 'Follow-up'),
        ('REFERRAL', 'Referral'),
        ('ANTENATAL', 'Antenatal Care'),
        ('IMMUNIZATION', 'Immunization'),
        ('GENERAL', 'General Consultation'),
    )
    
    STATUS_CHOICES = (
        ('REGISTERED', 'Registered'),
        ('TRIAGED', 'Triaged'),
        ('WAITING', 'Waiting for Doctor'),
        ('IN_CONSULTATION', 'In Consultation'),
        ('IN_TREATMENT', 'In Treatment'),
        ('COMPLETED', 'Completed'),
        ('ADMITTED', 'Admitted'),
        ('REFERRED', 'Referred'),
        ('CANCELLED', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('SHA', 'SHA'),
        ('JUBILEE', 'Jubilee'),
        ('INSURANCE_OTHER', 'Other Insurance'),
        ('CASH', 'Cash'),
        ('MPESA', 'Mpesa'),
    )
    
    
    # Visit Identification
    visit_number = models.CharField(
        _("Visit Number"), 
        max_length=20, 
        unique=True,
        help_text="Auto-generated unique visit number"
    )
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE,
        related_name='hospital_visits'
    )
    visit_type = models.CharField(
        _("Visit Type"), 
        max_length=20, 
        choices=VISIT_TYPE_CHOICES
    )
    
    # Visit Details
    arrival_time = models.DateTimeField(_("Arrival Time"), default=timezone.now)
    chief_complaint = models.TextField(
        _("Chief Complaint"),
        help_text="Main reason for visit"
    )
    status = models.CharField(
        _("Status"), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='REGISTERED'
    )
    
    # Staff Assignment
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_visits',
        limit_choices_to={'user_type': 'RECEPTIONIST'}
    )
    assigned_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_visits'
    )
    assigned_nurse = models.ForeignKey(
        Nurse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_visits'
    )
    
    specialized_service = models.ForeignKey(
        SpecializedService,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits",
        help_text="Specialist patient wants to see e.g Cardiologist"
    )

    # Insurance used (optional)
    insurance_provider = models.ForeignKey(
        InsuranceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="insured_visits",
        help_text="Insurance provider e.g SHA, Jubilee"
    )
    
    # Timestamps
    triage_time = models.DateTimeField(_("Triage Time"), null=True, blank=True)
    consultation_start = models.DateTimeField(_("Consultation Start"), null=True, blank=True)
    consultation_end = models.DateTimeField(_("Consultation End"), null=True, blank=True)
    discharge_time = models.DateTimeField(_("Discharge Time"), null=True, blank=True)
    
    # Additional Info
    referral_from = models.CharField(
        _("Referred From"), 
        max_length=200, 
        blank=True, 
        null=True
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    # System fields
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Patient Visit")
        verbose_name_plural = _("Patient Visits")
        ordering = ['-arrival_time']
        indexes = [
            models.Index(fields=['visit_number']),
            models.Index(fields=['patient', '-arrival_time']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate visit number if not set
        if not self.visit_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            # Get count of visits today
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            count = PatientVisit.objects.filter(
                created_at__gte=today_start
            ).count() + 1
            self.visit_number = f"V{date_str}{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.visit_number} - {self.patient.first_name} {self.patient.last_name}"
    
    @property
    def total_wait_time(self):
        """Calculate total wait time from arrival to consultation"""
        if self.consultation_start and self.arrival_time:
            delta = self.consultation_start - self.arrival_time
            return delta.total_seconds() / 60  # Return in minutes
        return None
    
    @property
    def is_overdue(self):
        """Check if visit is overdue based on triage priority"""
        if hasattr(self, 'triage') and self.status == 'WAITING':
            wait_time = (timezone.now() - self.arrival_time).total_seconds() / 60
            return wait_time > self.triage.category.max_wait_time
        return False


class TriageAssessment(models.Model):
    """
    Triage assessment for each patient visit
    Following Kenyan Ministry of Health guidelines
    """
    CONSCIOUSNESS_CHOICES = (
        ('ALERT', 'Alert and Responsive'),
        ('VERBAL', 'Responds to Verbal'),
        ('PAIN', 'Responds to Pain'),
        ('UNRESPONSIVE', 'Unresponsive'),
    )
    
    BREATHING_CHOICES = (
        ('NORMAL', 'Normal'),
        ('LABORED', 'Labored'),
        ('SHALLOW', 'Shallow'),
        ('ABSENT', 'Absent'),
    )
    
    visit = models.OneToOneField(
        PatientVisit,
        on_delete=models.CASCADE,
        related_name='triage'
    )
    category = models.ForeignKey(
        TriageCategory,
        on_delete=models.PROTECT
    )
    
    # Vital Signs
    temperature = models.DecimalField(
        _("Temperature (°C)"),
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(45)],
        null=True,
        blank=True
    )
    blood_pressure_systolic = models.IntegerField(
        _("BP Systolic (mmHg)"),
        validators=[MinValueValidator(40), MaxValueValidator(250)],
        null=True,
        blank=True
    )
    blood_pressure_diastolic = models.IntegerField(
        _("BP Diastolic (mmHg)"),
        validators=[MinValueValidator(20), MaxValueValidator(150)],
        null=True,
        blank=True
    )
    pulse_rate = models.IntegerField(
        _("Pulse Rate (bpm)"),
        validators=[MinValueValidator(30), MaxValueValidator(220)],
        null=True,
        blank=True
    )
    respiratory_rate = models.IntegerField(
        _("Respiratory Rate (breaths/min)"),
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        null=True,
        blank=True
    )
    oxygen_saturation = models.IntegerField(
        _("Oxygen Saturation (%)"),
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    weight = models.DecimalField(
        _("Weight (kg)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    height = models.DecimalField(
        _("Height (cm)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Clinical Assessment
    consciousness_level = models.CharField(
        _("Consciousness Level"),
        max_length=20,
        choices=CONSCIOUSNESS_CHOICES
    )
    breathing_status = models.CharField(
        _("Breathing Status"),
        max_length=20,
        choices=BREATHING_CHOICES
    )
    pain_score = models.IntegerField(
        _("Pain Score (0-10)"),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        default=0
    )
    
    # Assessment Details
    presenting_symptoms = models.TextField(_("Presenting Symptoms"))
    medical_history_notes = models.TextField(
        _("Relevant Medical History"),
        blank=True,
        null=True
    )
    allergies_noted = models.TextField(_("Allergies"), blank=True, null=True)
    current_medications = models.TextField(
        _("Current Medications"),
        blank=True,
        null=True
    )
    
    # Triage Decision
    triage_notes = models.TextField(_("Triage Notes"))
    requires_immediate_attention = models.BooleanField(
        _("Requires Immediate Attention"),
        default=False
    )
    recommended_specialty = models.CharField(
        _("Recommended Specialty"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Staff and Timestamps
    assessed_by = models.ForeignKey(
        Nurse,
        on_delete=models.SET_NULL,
        null=True,
        related_name='triage_assessments'
    )
    assessment_time = models.DateTimeField(_("Assessment Time"), default=timezone.now)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Triage Assessment")
        verbose_name_plural = _("Triage Assessments")
        ordering = ['-assessment_time']
    
    def __str__(self):
        return f"Triage for {self.visit.visit_number} - {self.category.color_code}"
    
    @property
    def bmi(self):
        """Calculate BMI if height and weight available"""
        if self.weight and self.height:
            height_m = float(self.height) / 100
            return round(float(self.weight) / (height_m ** 2), 2)
        return None
    
    @property
    def is_critical_vitals(self):
        """Check if any vital signs are in critical range"""
        critical = False
        
        # Critical temperature
        if self.temperature and (self.temperature < 35 or self.temperature > 39.5):
            critical = True
        
        # Critical BP
        if self.blood_pressure_systolic and (
            self.blood_pressure_systolic < 90 or self.blood_pressure_systolic > 180
        ):
            critical = True
        
        # Critical oxygen saturation
        if self.oxygen_saturation and self.oxygen_saturation < 90:
            critical = True
        
        return critical


class QueueManagement(models.Model):
    """
    Queue management for different hospital departments
    """
    DEPARTMENT_CHOICES = (
        ('TRIAGE', 'Triage'),
        ('CONSULTATION', 'Consultation'),
        ('LABORATORY', 'Laboratory'),
        ('PHARMACY', 'Pharmacy'),
        ('RADIOLOGY', 'Radiology'),
        ('PROCEDURE', 'Procedure Room'),
        ('ADMISSION', 'Admission'),
    )
    
    visit = models.ForeignKey(
        PatientVisit,
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )
    department = models.CharField(
        _("Department"),
        max_length=20,
        choices=DEPARTMENT_CHOICES
    )
    
    # Queue Details
    queue_number = models.IntegerField(_("Queue Number"))
    priority_override = models.BooleanField(
        _("Priority Override"),
        default=False,
        help_text="Manual priority escalation"
    )
    
    # Timing
    joined_queue = models.DateTimeField(_("Joined Queue"), default=timezone.now)
    called_time = models.DateTimeField(_("Called Time"), null=True, blank=True)
    service_start = models.DateTimeField(_("Service Start"), null=True, blank=True)
    service_end = models.DateTimeField(_("Service End"), null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_("Active in Queue"), default=True)
    is_serving = models.BooleanField(_("Currently Being Served"), default=False)
    is_completed = models.BooleanField(_("Completed"), default=False)
    
    # Staff
    serving_staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queue_services'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Queue Entry")
        verbose_name_plural = _("Queue Entries")
        ordering = ['priority_override', 'queue_number', 'joined_queue']
        indexes = [
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['visit']),
        ]
    
    def __str__(self):
        return f"{self.department} Queue #{self.queue_number} - {self.visit.visit_number}"
    
    @property
    def wait_time(self):
        """Calculate wait time in minutes"""
        if self.service_start:
            delta = self.service_start - self.joined_queue
        else:
            delta = timezone.now() - self.joined_queue
        return round(delta.total_seconds() / 60, 2)
    
    @property
    def service_duration(self):
        """Calculate service duration in minutes"""
        if self.service_start and self.service_end:
            delta = self.service_end - self.service_start
            return round(delta.total_seconds() / 60, 2)
        return None
    
    def call_patient(self):
        """Mark patient as called"""
        self.called_time = timezone.now()
        self.save()
    
    def start_service(self, staff_member):
        """Start serving the patient"""
        self.service_start = timezone.now()
        self.is_serving = True
        self.serving_staff = staff_member
        self.save()
    
    def complete_service(self):
        """Complete the service"""
        self.service_end = timezone.now()
        self.is_serving = False
        self.is_completed = True
        self.is_active = False
        self.save()


class QueueStatistics(models.Model):
    """
    Daily statistics for queue performance monitoring
    """
    date = models.DateField(_("Date"), unique=True)
    department = models.CharField(
        _("Department"),
        max_length=20,
        choices=QueueManagement.DEPARTMENT_CHOICES
    )
    
    # Statistics
    total_patients = models.IntegerField(_("Total Patients"), default=0)
    average_wait_time = models.DecimalField(
        _("Average Wait Time (minutes)"),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    max_wait_time = models.DecimalField(
        _("Maximum Wait Time (minutes)"),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    average_service_time = models.DecimalField(
        _("Average Service Time (minutes)"),
        max_digits=6,
        decimal_places=2,
        default=0
    )
    
    # Priority breakdown
    emergency_cases = models.IntegerField(_("Emergency Cases"), default=0)
    priority_cases = models.IntegerField(_("Priority Cases"), default=0)
    regular_cases = models.IntegerField(_("Regular Cases"), default=0)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Queue Statistics")
        verbose_name_plural = _("Queue Statistics")
        ordering = ['-date']
        unique_together = ['date', 'department']
    
    def __str__(self):
        return f"{self.department} Statistics - {self.date}"
    
    
class HospitalAsset(models.Model):
    """
    Model for tracking all hospital assets including equipment, machinery, 
    furniture, and other resources for audit and maintenance purposes.
    """
    
    ASSET_CATEGORY_CHOICES = (
        ('MEDICAL_EQUIPMENT', 'Medical Equipment'),
        ('LABORATORY_EQUIPMENT', 'Laboratory Equipment'),
        ('RADIOLOGY_EQUIPMENT', 'Radiology Equipment'),
        ('SURGICAL_EQUIPMENT', 'Surgical Equipment'),
        ('IT_EQUIPMENT', 'IT Equipment'),
        ('FURNITURE', 'Furniture'),
        ('VEHICLE', 'Vehicle'),
        ('BUILDING', 'Building/Infrastructure'),
        ('HVAC', 'HVAC System'),
        ('GENERATOR', 'Generator/Power System'),
        ('OTHER', 'Other'),
    )
    
    ASSET_STATUS_CHOICES = (
        ('OPERATIONAL', 'Operational'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('RETIRED', 'Retired'),
        ('PENDING_DISPOSAL', 'Pending Disposal'),
    )
    
    CONDITION_CHOICES = (
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('CRITICAL', 'Critical'),
    )
    
    PRIORITY_CHOICES = (
        ('CRITICAL', 'Critical - Life Support'),
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    )
    
    # Asset Identification
    asset_id = models.CharField(
        _("Asset ID"),
        max_length=50,
        unique=True,
        help_text="Unique identifier for the asset (e.g., MED-001, LAB-023)"
    )
    asset_name = models.CharField(_("Asset Name"), max_length=200)
    category = models.CharField(
        _("Category"),
        max_length=30,
        choices=ASSET_CATEGORY_CHOICES
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    
    # Procurement Details
    manufacturer = models.CharField(_("Manufacturer"), max_length=200, blank=True, null=True)
    model_number = models.CharField(_("Model Number"), max_length=100, blank=True, null=True)
    serial_number = models.CharField(_("Serial Number"), max_length=100, blank=True, null=True)
    purchase_date = models.DateField(_("Purchase Date"), blank=True, null=True)
    purchase_cost = models.DecimalField(
        _("Purchase Cost (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    supplier = models.CharField(_("Supplier"), max_length=200, blank=True, null=True)
    warranty_expiry = models.DateField(_("Warranty Expiry Date"), blank=True, null=True)
    
    # Location and Assignment
    location = models.CharField(
        _("Location"),
        max_length=200,
        help_text="Department or specific location (e.g., ICU, Lab, Ward 3)"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets',
        help_text="Staff member responsible for this asset"
    )
    
    # Asset Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ASSET_STATUS_CHOICES,
        default='OPERATIONAL'
    )
    condition = models.CharField(
        _("Condition"),
        max_length=20,
        choices=CONDITION_CHOICES,
        default='GOOD'
    )
    priority = models.CharField(
        _("Priority Level"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    
    # Maintenance Information
    requires_maintenance = models.BooleanField(_("Requires Maintenance"), default=False)
    maintenance_frequency = models.CharField(
        _("Maintenance Frequency"),
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 'Every 3 months', 'Annually', 'Every 6 months'"
    )
    last_maintenance_date = models.DateField(_("Last Maintenance Date"), blank=True, null=True)
    next_maintenance_date = models.DateField(_("Next Maintenance Date"), blank=True, null=True)
    maintenance_notes = models.TextField(_("Maintenance Notes"), blank=True, null=True)
    
    # Calibration (for medical equipment)
    requires_calibration = models.BooleanField(_("Requires Calibration"), default=False)
    last_calibration_date = models.DateField(_("Last Calibration Date"), blank=True, null=True)
    next_calibration_date = models.DateField(_("Next Calibration Date"), blank=True, null=True)
    calibration_certificate = models.FileField(
        _("Calibration Certificate"),
        upload_to='asset_certificates/',
        blank=True,
        null=True
    )
    
    # Audit and Compliance
    last_audit_date = models.DateField(_("Last Audit Date"), blank=True, null=True)
    next_audit_date = models.DateField(_("Next Audit Date"), blank=True, null=True)
    compliance_status = models.BooleanField(_("Compliance Status"), default=True)
    regulatory_notes = models.TextField(
        _("Regulatory Notes"),
        blank=True,
        null=True,
        help_text="Any regulatory compliance notes or requirements"
    )
    
    # Purchase Requests
    needs_replacement = models.BooleanField(_("Needs Replacement"), default=False)
    replacement_reason = models.TextField(_("Replacement Reason"), blank=True, null=True)
    estimated_replacement_cost = models.DecimalField(
        _("Estimated Replacement Cost (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    
    # Documentation
    asset_image = models.ImageField(
        _("Asset Image"),
        upload_to='asset_images/',
        blank=True,
        null=True
    )
    user_manual = models.FileField(
        _("User Manual"),
        upload_to='asset_manuals/',
        blank=True,
        null=True
    )
    additional_documents = models.FileField(
        _("Additional Documents"),
        upload_to='asset_documents/',
        blank=True,
        null=True
    )
    
    # Additional Information
    barcode = models.CharField(_("Barcode/QR Code"), max_length=100, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assets_created'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Hospital Asset")
        verbose_name_plural = _("Hospital Assets")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_id']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['location']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['next_audit_date']),
        ]
    
    def __str__(self):
        return f"{self.asset_id} - {self.asset_name}"
    
    @property
    def is_maintenance_due(self):
        """Check if maintenance is due within 7 days"""
        if self.next_maintenance_date:
            days_until = (self.next_maintenance_date - timezone.now().date()).days
            return days_until <= 7
        return False
    
    @property
    def is_maintenance_overdue(self):
        """Check if maintenance is overdue"""
        if self.next_maintenance_date:
            return self.next_maintenance_date < timezone.now().date()
        return False
    
    @property
    def is_audit_due(self):
        """Check if audit is due within 30 days"""
        if self.next_audit_date:
            days_until = (self.next_audit_date - timezone.now().date()).days
            return days_until <= 30
        return False
    
    @property
    def warranty_status(self):
        """Check warranty status"""
        if not self.warranty_expiry:
            return "No Warranty Info"
        if self.warranty_expiry >= timezone.now().date():
            return "Under Warranty"
        return "Warranty Expired"
    
    @property
    def age_in_years(self):
        """Calculate asset age in years"""
        if self.purchase_date:
            delta = timezone.now().date() - self.purchase_date
            return round(delta.days / 365.25, 1)
        return None


class AssetMaintenanceLog(models.Model):
    """
    Log of all maintenance activities performed on assets
    """
    MAINTENANCE_TYPE_CHOICES = (
        ('PREVENTIVE', 'Preventive Maintenance'),
        ('CORRECTIVE', 'Corrective Maintenance'),
        ('CALIBRATION', 'Calibration'),
        ('INSPECTION', 'Inspection'),
        ('REPAIR', 'Repair'),
        ('REPLACEMENT', 'Part Replacement'),
    )
    
    asset = models.ForeignKey(
        HospitalAsset,
        on_delete=models.CASCADE,
        related_name='maintenance_logs'
    )
    maintenance_type = models.CharField(
        _("Maintenance Type"),
        max_length=20,
        choices=MAINTENANCE_TYPE_CHOICES
    )
    
    # Maintenance Details
    maintenance_date = models.DateField(_("Maintenance Date"))
    performed_by = models.CharField(_("Performed By"), max_length=200)
    service_provider = models.CharField(
        _("Service Provider"),
        max_length=200,
        blank=True,
        null=True,
        help_text="External service provider if applicable"
    )
    
    # Work Details
    description = models.TextField(_("Work Description"))
    parts_replaced = models.TextField(_("Parts Replaced"), blank=True, null=True)
    cost = models.DecimalField(
        _("Cost (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    
    # Status
    downtime_hours = models.DecimalField(
        _("Downtime (Hours)"),
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )
    is_completed = models.BooleanField(_("Completed"), default=True)
    
    # Documentation
    invoice_number = models.CharField(_("Invoice Number"), max_length=100, blank=True, null=True)
    receipt = models.FileField(
        _("Receipt/Invoice"),
        upload_to='maintenance_receipts/',
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Additional Notes"), blank=True, null=True)
    
    # System Fields
    logged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_logs_created'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Asset Maintenance Log")
        verbose_name_plural = _("Asset Maintenance Logs")
        ordering = ['-maintenance_date']
    
    def __str__(self):
        return f"{self.asset.asset_id} - {self.get_maintenance_type_display()} on {self.maintenance_date}"
    
    
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class ICD10Category(models.Model):
    """
    ICD-10 Chapter/Category classification
    Example: Chapter I - Certain infectious and parasitic diseases (A00-B99)
    """
    chapter_number = models.CharField(
        _("Chapter Number"), 
        max_length=10,
        help_text="e.g., 'I', 'II', 'III'"
    )
    code_range = models.CharField(
        _("Code Range"), 
        max_length=20,
        help_text="e.g., 'A00-B99'"
    )
    category_name = models.CharField(_("Category Name"), max_length=500)
    description = models.TextField(_("Description"), blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    class Meta:
        verbose_name = _("ICD-10 Category")
        verbose_name_plural = _("ICD-10 Categories")
        ordering = ['chapter_number']
        indexes = [
            models.Index(fields=['chapter_number']),
            models.Index(fields=['code_range']),
        ]
    
    def __str__(self):
        return f"Chapter {self.chapter_number}: {self.category_name} ({self.code_range})"


class ICD10Code(models.Model):
    """
    Complete ICD-10 code database
    Contains all codes relevant to Kenyan healthcare
    """
    
    # ICD-10 Code Structure: A00.0
    # A = Letter (category)
    # 00 = Numbers (specific condition)
    # .0 = Decimal (subcategory - optional)
    
    code = models.CharField(
        _("ICD-10 Code"),
        max_length=10,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]\d{2}(\.\d{1,2})?$',
                message='Enter a valid ICD-10 code (e.g., A00, A00.0, A00.1)'
            )
        ],
        help_text="e.g., I10, B50.0, J18.9"
    )
    
    category = models.ForeignKey(
        ICD10Category,
        on_delete=models.CASCADE,
        related_name='codes'
    )
    
    # Full description in English
    description = models.TextField(
        _("Full Description"),
        help_text="Complete medical description of the condition"
    )
    
    # Short description for UI dropdowns
    short_description = models.CharField(
        _("Short Description"),
        max_length=200,
        help_text="Abbreviated description for quick reference"
    )
    
    # Common Kenyan name/alternative names
    local_name = models.CharField(
        _("Local/Common Name"),
        max_length=200,
        blank=True,
        null=True,
        help_text="Common name used in Kenyan hospitals (e.g., 'Malaria', 'High BP')"
    )
    
    # Clinical information
    is_notifiable = models.BooleanField(
        _("Notifiable Disease"),
        default=False,
        help_text="Must be reported to MOH/DHIS2 (e.g., Cholera, TB, COVID-19)"
    )
    
    requires_isolation = models.BooleanField(
        _("Requires Isolation"),
        default=False,
        help_text="Patient needs isolation (infectious diseases)"
    )
    
    # NHIF & Insurance mapping
    nhif_eligible = models.BooleanField(
        _("NHIF Eligible"),
        default=False,
        help_text="Covered under NHIF packages"
    )
    
    nhif_package_code = models.CharField(
        _("NHIF Package Code"),
        max_length=50,
        blank=True,
        null=True,
        help_text="Associated NHIF benefit package"
    )
    
    # Clinical decision support
    suggested_lab_tests = models.TextField(
        _("Suggested Lab Tests"),
        blank=True,
        null=True,
        help_text="Comma-separated list of recommended tests"
    )
    
    treatment_guidelines = models.TextField(
        _("Treatment Guidelines"),
        blank=True,
        null=True,
        help_text="Standard treatment protocols"
    )
    
    # Usage statistics
    usage_count = models.IntegerField(
        _("Usage Count"),
        default=0,
        help_text="How many times this code has been used"
    )
    
    # Status
    is_active = models.BooleanField(_("Active"), default=True)
    is_common = models.BooleanField(
        _("Common Diagnosis"),
        default=False,
        help_text="Frequently used in this hospital - shows in quick-select"
    )
    
    # Metadata
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("ICD-10 Code")
        verbose_name_plural = _("ICD-10 Codes")
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_common', 'is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['-usage_count']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.short_description}"
    
    def save(self, *args, **kwargs):
        # Auto-populate short description if not provided
        if not self.short_description and self.description:
            self.short_description = self.description[:200]
        super().save(*args, **kwargs)
    
    @property
    def full_display(self):
        """Full display name with code and description"""
        return f"[{self.code}] {self.short_description}"


class ConsultationDiagnosis(models.Model):
    """
    Links ICD-10 codes to patient consultations
    This replaces/enhances your current Consultation.diseases ManyToMany
    """
    DIAGNOSIS_TYPE_CHOICES = (
        ('PRIMARY', 'Primary Diagnosis'),
        ('SECONDARY', 'Secondary Diagnosis'),
        ('DIFFERENTIAL', 'Differential Diagnosis'),
        ('PROVISIONAL', 'Provisional Diagnosis'),
        ('FINAL', 'Final Diagnosis'),
    )
    
    CERTAINTY_CHOICES = (
        ('CONFIRMED', 'Confirmed'),
        ('SUSPECTED', 'Suspected'),
        ('RULED_OUT', 'Ruled Out'),
    )
    
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.CASCADE,
        related_name='icd10_diagnoses'
    )
    
    icd10_code = models.ForeignKey(
        ICD10Code,
        on_delete=models.PROTECT,
        related_name='diagnoses'
    )
    
    diagnosis_type = models.CharField(
        _("Diagnosis Type"),
        max_length=20,
        choices=DIAGNOSIS_TYPE_CHOICES,
        default='PRIMARY'
    )
    
    certainty = models.CharField(
        _("Certainty"),
        max_length=20,
        choices=CERTAINTY_CHOICES,
        default='CONFIRMED'
    )
    
    # Clinical notes specific to this diagnosis
    clinical_notes = models.TextField(
        _("Clinical Notes"),
        blank=True,
        null=True,
        help_text="Specific notes about this diagnosis for this patient"
    )
    
    # Treatment plan for this specific diagnosis
    treatment_plan = models.TextField(
        _("Treatment Plan"),
        blank=True,
        null=True
    )
    
    # Timeline
    onset_date = models.DateField(
        _("Onset Date"),
        blank=True,
        null=True,
        help_text="When symptoms started"
    )
    
    diagnosed_date = models.DateField(
        _("Diagnosed Date"),
        auto_now_add=True
    )
    
    # Insurance/Billing
    submitted_to_nhif = models.BooleanField(
        _("Submitted to NHIF"),
        default=False
    )
    
    nhif_claim_number = models.CharField(
        _("NHIF Claim Number"),
        max_length=100,
        blank=True,
        null=True
    )
    
    submitted_to_insurance = models.BooleanField(
        _("Submitted to Insurance"),
        default=False
    )
    
    insurance_claim_number = models.CharField(
        _("Insurance Claim Number"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # System fields
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='diagnoses_created'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Consultation Diagnosis")
        verbose_name_plural = _("Consultation Diagnoses")
        ordering = ['diagnosis_type', '-created_at']
        indexes = [
            models.Index(fields=['consultation', 'diagnosis_type']),
            models.Index(fields=['icd10_code']),
            models.Index(fields=['submitted_to_nhif']),
        ]
    
    def __str__(self):
        return f"{self.consultation.appointment.patient} - {self.icd10_code.code}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Increment usage count for the ICD-10 code
        self.icd10_code.usage_count += 1
        self.icd10_code.save(update_fields=['usage_count'])


class DiseaseStatistics(models.Model):
    """
    Monthly/Weekly statistics for MOH/DHIS2 reporting
    Aggregates diagnosis data for reporting
    """
    REPORTING_PERIOD_CHOICES = (
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual'),
    )
    
    icd10_code = models.ForeignKey(
        ICD10Code,
        on_delete=models.CASCADE,
        related_name='statistics'
    )
    
    period_type = models.CharField(
        _("Reporting Period"),
        max_length=20,
        choices=REPORTING_PERIOD_CHOICES
    )
    
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    
    # Statistics
    total_cases = models.IntegerField(_("Total Cases"), default=0)
    new_cases = models.IntegerField(_("New Cases"), default=0)
    male_cases = models.IntegerField(_("Male Cases"), default=0)
    female_cases = models.IntegerField(_("Female Cases"), default=0)
    pediatric_cases = models.IntegerField(
        _("Pediatric Cases (0-15 years)"),
        default=0
    )
    adult_cases = models.IntegerField(
        _("Adult Cases (16+ years)"),
        default=0
    )
    
    # Outcomes
    recovered = models.IntegerField(_("Recovered"), default=0)
    referred = models.IntegerField(_("Referred"), default=0)
    deaths = models.IntegerField(_("Deaths"), default=0)
    
    # NHIF claims
    nhif_claims_submitted = models.IntegerField(
        _("NHIF Claims Submitted"),
        default=0
    )
    
    # System fields
    generated_at = models.DateTimeField(_("Generated At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Disease Statistics")
        verbose_name_plural = _("Disease Statistics")
        ordering = ['-period_end']
        unique_together = ['icd10_code', 'period_type', 'period_start']
        indexes = [
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['icd10_code', 'period_type']),
        ]
    
    def __str__(self):
        return f"{self.icd10_code.code} - {self.period_type} ({self.period_start} to {self.period_end})"


class NotifiableDisease(models.Model):
    """
    Track notifiable diseases that must be reported to MOH
    According to Kenya's Public Health Act
    """
    URGENCY_CHOICES = (
        ('IMMEDIATE', 'Immediate (within 24 hours)'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending Report'),
        ('REPORTED', 'Reported to MOH'),
        ('CONFIRMED', 'Confirmed by MOH'),
        ('INVESTIGATING', 'Under Investigation'),
        ('CLOSED', 'Case Closed'),
    )
    
    diagnosis = models.ForeignKey(
        ConsultationDiagnosis,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='notifiable_diseases'
    )
    
    icd10_code = models.ForeignKey(
        ICD10Code,
        on_delete=models.PROTECT,
        limit_choices_to={'is_notifiable': True}
    )
    
    # Reporting details
    urgency = models.CharField(
        _("Reporting Urgency"),
        max_length=20,
        choices=URGENCY_CHOICES
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    date_detected = models.DateField(_("Date Detected"), auto_now_add=True)
    date_reported = models.DateField(
        _("Date Reported to MOH"),
        blank=True,
        null=True
    )
    
    # Contact tracing
    requires_contact_tracing = models.BooleanField(
        _("Requires Contact Tracing"),
        default=False
    )
    
    contacts_traced = models.TextField(
        _("Contacts Traced"),
        blank=True,
        null=True,
        help_text="List of contacts traced"
    )
    
    # MOH details
    dhis2_reported = models.BooleanField(_("Reported to DHIS2"), default=False)
    dhis2_reference = models.CharField(
        _("DHIS2 Reference"),
        max_length=100,
        blank=True,
        null=True
    )
    
    moh_reference = models.CharField(
        _("MOH Reference Number"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Outbreak tracking
    is_outbreak_case = models.BooleanField(_("Part of Outbreak"), default=False)
    outbreak_reference = models.CharField(
        _("Outbreak Reference"),
        max_length=100,
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    # System fields
    reported_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='notifiable_disease_reports'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Notifiable Disease")
        verbose_name_plural = _("Notifiable Diseases")
        ordering = ['-date_detected']
        indexes = [
            models.Index(fields=['status', 'urgency']),
            models.Index(fields=['date_detected']),
            models.Index(fields=['dhis2_reported']),
        ]
    
    def __str__(self):
        return f"{self.icd10_code.code} - {self.patient} ({self.status})"
    
    
# models.py - ADD THESE TO YOUR EXISTING MODELS FILE

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class SHAMember(models.Model):
    """
    Links existing Patient to SHA membership
    Does NOT modify Patient model
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('PENDING', 'Pending Verification'),
    )
    
    patient = models.OneToOneField(
        'Patient',
        on_delete=models.CASCADE,
        related_name='sha_member'
    )
    
    # SHA Details
    sha_number = models.CharField(
        _("SHA Number"),
        max_length=50,
        unique=True,
        db_index=True
    )
    package_name = models.CharField(
        _("Package Name"),
        max_length=200,
        default="Standard Package"
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    enrollment_date = models.DateField(_("Enrollment Date"), default=timezone.now)
    expiry_date = models.DateField(_("Expiry Date"), blank=True, null=True)
    
    # Balance tracking
    annual_limit = models.DecimalField(
        _("Annual Limit (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=500000
    )
    used_amount = models.DecimalField(
        _("Used Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Verification
    last_verified = models.DateTimeField(_("Last Verified"), blank=True, null=True)
    verification_response = models.JSONField(_("Verification Response"), blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("SHA Member")
        verbose_name_plural = _("SHA Members")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sha_number} - {self.patient.first_name} {self.patient.last_name}"
    
    @property
    def is_valid(self):
        """Check if membership is valid"""
        if self.status != 'ACTIVE':
            return False
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False
        return True
    
    @property
    def available_balance(self):
        """Calculate available balance"""
        return self.annual_limit - self.used_amount


class SHAClaim(models.Model):
    """
    Tracks claims submitted to SHA
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('PARTIALLY_APPROVED', 'Partially Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    )
    
    CLAIM_TYPE_CHOICES = (
        ('OUTPATIENT', 'Outpatient'),
        ('INPATIENT', 'Inpatient'),
        ('EMERGENCY', 'Emergency'),
        ('PHARMACY', 'Pharmacy'),
        ('LABORATORY', 'Laboratory'),
        ('RADIOLOGY', 'Radiology'),
    )
    
    # Claim Identification
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    sha_reference = models.CharField(
        _("SHA Reference Number"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference number from SHA system"
    )
    
    # Links to existing models
    sha_member = models.ForeignKey(
        SHAMember,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.CASCADE,
        related_name='sha_claims',
        blank=True,
        null=True
    )
    
    # Claim Details
    claim_type = models.CharField(
        _("Claim Type"),
        max_length=20,
        choices=CLAIM_TYPE_CHOICES,
        default='OUTPATIENT'
    )
    service_date = models.DateField(_("Service Date"), default=timezone.now)
    
    # Financial
    claimed_amount = models.DecimalField(
        _("Claimed Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    approved_amount = models.DecimalField(
        _("Approved Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    patient_copay = models.DecimalField(
        _("Patient Co-pay (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Status tracking
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(_("Submitted At"), blank=True, null=True)
    approved_at = models.DateTimeField(_("Approved At"), blank=True, null=True)
    paid_at = models.DateTimeField(_("Paid At"), blank=True, null=True)
    
    # API Response Storage
    submission_request = models.JSONField(_("Submission Request"), blank=True, null=True)
    submission_response = models.JSONField(_("Submission Response"), blank=True, null=True)
    approval_response = models.JSONField(_("Approval Response"), blank=True, null=True)
    
    # Rejection details
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Staff
    submitted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sha_claims_submitted'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("SHA Claim")
        verbose_name_plural = _("SHA Claims")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['sha_reference']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            random_str = uuid.uuid4().hex[:6].upper()
            self.claim_number = f"SHA-{date_str}-{random_str}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.claim_number} - {self.sha_member.patient.first_name} - {self.status}"
    
    @property
    def pending_amount(self):
        """Amount pending payment"""
        return self.approved_amount - self.patient_copay


class SHAClaimItem(models.Model):
    """
    Individual items/services in a claim
    """
    ITEM_TYPE_CHOICES = (
        ('CONSULTATION', 'Consultation Fee'),
        ('MEDICINE', 'Medicine/Drugs'),
        ('LAB_TEST', 'Laboratory Test'),
        ('RADIOLOGY', 'Radiology/Imaging'),
        ('PROCEDURE', 'Medical Procedure'),
        ('BED_CHARGE', 'Bed Charge'),
        ('OTHER', 'Other'),
    )
    
    claim = models.ForeignKey(
        SHAClaim,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    item_type = models.CharField(
        _("Item Type"),
        max_length=20,
        choices=ITEM_TYPE_CHOICES
    )
    description = models.CharField(_("Description"), max_length=500)
    
    # Link to ICD-10 if applicable
    icd10_code = models.ForeignKey(
        'ICD10Code',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sha_claim_items'
    )
    
    # Link to medicine if applicable
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sha_claim_items'
    )
    
    quantity = models.IntegerField(_("Quantity"), default=1)
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    approved_amount = models.DecimalField(
        _("Approved Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("SHA Claim Item")
        verbose_name_plural = _("SHA Claim Items")
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} - {self.total_amount}"


class SHAAPILog(models.Model):
    """
    Logs all API calls to SHA for debugging and audit
    """
    REQUEST_TYPE_CHOICES = (
        ('VERIFY_MEMBER', 'Verify Member'),
        ('SUBMIT_CLAIM', 'Submit Claim'),
        ('CHECK_CLAIM_STATUS', 'Check Claim Status'),
        ('GET_PACKAGES', 'Get Packages'),
        ('OTHER', 'Other'),
    )
    
    request_type = models.CharField(
        _("Request Type"),
        max_length=30,
        choices=REQUEST_TYPE_CHOICES
    )
    endpoint = models.CharField(_("API Endpoint"), max_length=500)
    
    # Request details
    request_method = models.CharField(_("HTTP Method"), max_length=10, default='POST')
    request_headers = models.JSONField(_("Request Headers"), blank=True, null=True)
    request_body = models.JSONField(_("Request Body"), blank=True, null=True)
    
    # Response details
    response_status = models.IntegerField(_("Response Status Code"), blank=True, null=True)
    response_body = models.JSONField(_("Response Body"), blank=True, null=True)
    response_time = models.FloatField(_("Response Time (seconds)"), blank=True, null=True)
    
    # Status
    success = models.BooleanField(_("Success"), default=False)
    error_message = models.TextField(_("Error Message"), blank=True, null=True)
    
    # Related objects
    sha_member = models.ForeignKey(
        SHAMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_logs'
    )
    claim = models.ForeignKey(
        SHAClaim,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_logs'
    )
    
    # User tracking
    initiated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sha_api_logs'
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("SHA API Log")
        verbose_name_plural = _("SHA API Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_type', '-created_at']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        return f"{self.request_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    
"""
Hospital Procurement Models for Level 4 Hospital ERP
Add these to your existing models.py file
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class Supplier(models.Model):
    """
    Manages hospital suppliers/vendors
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('BLACKLISTED', 'Blacklisted'),
        ('PENDING', 'Pending Approval'),
    )
    
    SUPPLIER_TYPE_CHOICES = (
        ('PHARMACEUTICAL', 'Pharmaceutical Supplier'),
        ('MEDICAL_EQUIPMENT', 'Medical Equipment'),
        ('LABORATORY', 'Laboratory Supplies'),
        ('SURGICAL', 'Surgical Supplies'),
        ('GENERAL', 'General Supplies'),
        ('FOOD', 'Food & Catering'),
        ('CLEANING', 'Cleaning Supplies'),
        ('IT', 'IT Equipment'),
        ('MAINTENANCE', 'Maintenance Services'),
        ('OTHER', 'Other'),
    )
    
    # Supplier Identification
    supplier_code = models.CharField(
        _("Supplier Code"),
        max_length=50,
        unique=True,
        editable=False
    )
    supplier_name = models.CharField(_("Supplier Name"), max_length=200)
    supplier_type = models.CharField(
        _("Supplier Type"),
        max_length=30,
        choices=SUPPLIER_TYPE_CHOICES
    )
    
    # Contact Information
    contact_person = models.CharField(_("Contact Person"), max_length=200)
    phone_number = models.CharField(_("Phone Number"), max_length=15)
    alternate_phone = models.CharField(_("Alternate Phone"), max_length=15, blank=True, null=True)
    email = models.EmailField(_("Email"))
    website = models.URLField(_("Website"), blank=True, null=True)
    
    # Address
    physical_address = models.TextField(_("Physical Address"))
    city = models.CharField(_("City"), max_length=100)
    county = models.CharField(_("County"), max_length=100)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True, null=True)
    
    # Business Details
    pin_number = models.CharField(_("KRA PIN Number"), max_length=20, unique=True)
    vat_number = models.CharField(_("VAT Number"), max_length=50, blank=True, null=True)
    business_registration = models.CharField(
        _("Business Registration Number"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Banking Details
    bank_name = models.CharField(_("Bank Name"), max_length=100, blank=True, null=True)
    bank_branch = models.CharField(_("Bank Branch"), max_length=100, blank=True, null=True)
    account_number = models.CharField(_("Account Number"), max_length=50, blank=True, null=True)
    account_name = models.CharField(_("Account Name"), max_length=200, blank=True, null=True)
    
    # Performance Metrics
    credit_days = models.IntegerField(
        _("Credit Days"),
        default=30,
        help_text="Number of days credit allowed"
    )
    credit_limit = models.DecimalField(
        _("Credit Limit (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    rating = models.DecimalField(
        _("Supplier Rating"),
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MinValueValidator(5)],
        default=0,
        help_text="Rating out of 5"
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    blacklist_reason = models.TextField(_("Blacklist Reason"), blank=True, null=True)
    
    # Documents
    certificate_of_incorporation = models.FileField(
        _("Certificate of Incorporation"),
        upload_to='suppliers/documents/',
        blank=True,
        null=True
    )
    tax_compliance = models.FileField(
        _("Tax Compliance Certificate"),
        upload_to='suppliers/documents/',
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    # System Fields
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='suppliers_created',
        limit_choices_to={'user_type': 'PROCUREMENT'}
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['supplier_name']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['status']),
            models.Index(fields=['supplier_type']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.supplier_code:
            # Generate unique supplier code
            prefix = self.supplier_type[:3].upper()
            count = Supplier.objects.filter(supplier_type=self.supplier_type).count() + 1
            self.supplier_code = f"SUP-{prefix}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.supplier_code} - {self.supplier_name}"
    
    @property
    def is_active(self):
        return self.status == 'ACTIVE'


class PurchaseRequest(models.Model):
    """
    Internal purchase requisition from departments
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved by HOD'),
        ('APPROVED_ACCOUNTANT', 'Approved by Accountant'),
        ('PROCUREMENT_REVIEW', 'Under Procurement Review'),
        ('APPROVED_PROCUREMENT', 'Approved by Procurement'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED_TO_PO', 'Converted to Purchase Order'),
        ('CANCELLED', 'Cancelled'),
    )
    
    URGENCY_CHOICES = (
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency'),
    )
    
    DEPARTMENT_CHOICES = (
        ('PHARMACY', 'Pharmacy'),
        ('LABORATORY', 'Laboratory'),
        ('RADIOLOGY', 'Radiology'),
        ('SURGERY', 'Surgery'),
        ('ICU', 'ICU'),
        ('WARD', 'Ward'),
        ('KITCHEN', 'Kitchen'),
        ('LAUNDRY', 'Laundry'),
        ('MAINTENANCE', 'Maintenance'),
        ('IT', 'IT'),
        ('ADMIN', 'Administration'),
        ('OTHER', 'Other'),
    )
    
    # Request Identification
    request_number = models.CharField(
        _("Request Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Request Details
    requesting_department = models.CharField(
        _("Requesting Department"),
        max_length=20,
        choices=DEPARTMENT_CHOICES
    )
    requested_by = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='purchase_requests'
    )
    urgency = models.CharField(
        _("Urgency"),
        max_length=20,
        choices=URGENCY_CHOICES,
        default='ROUTINE'
    )
    
    # Justification
    purpose = models.TextField(_("Purpose/Justification"))
    expected_delivery_date = models.DateField(_("Expected Delivery Date"))
    
    # Budget
    estimated_cost = models.DecimalField(
        _("Estimated Cost (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    budget_line = models.CharField(
        _("Budget Line"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Budget code/line item"
    )
    
    # Status & Approvals
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # HOD Approval
    hod_approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_hod_approvals'
    )
    hod_approved_at = models.DateTimeField(_("HOD Approved At"), blank=True, null=True)
    hod_comments = models.TextField(_("HOD Comments"), blank=True, null=True)
    
    # Accountant Approval
    accountant_approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_accountant_approvals',
        limit_choices_to={'user_type': 'ACCOUNTANT'}
    )
    accountant_approved_at = models.DateTimeField(_("Accountant Approved At"), blank=True, null=True)
    accountant_comments = models.TextField(_("Accountant Comments"), blank=True, null=True)
    
    # Procurement Approval
    procurement_approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_procurement_approvals',
        limit_choices_to={'user_type': 'PROCUREMENT'}
    )
    procurement_approved_at = models.DateTimeField(_("Procurement Approved At"), blank=True, null=True)
    procurement_comments = models.TextField(_("Procurement Comments"), blank=True, null=True)
    
    # Rejection
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_rejections'
    )
    rejected_at = models.DateTimeField(_("Rejected At"), blank=True, null=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    notes = models.TextField(_("Additional Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Purchase Request")
        verbose_name_plural = _("Purchase Requests")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['status']),
            models.Index(fields=['requesting_department']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = PurchaseRequest.objects.filter(created_at__date=today.date()).count() + 1
            self.request_number = f"PR-{date_str}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.request_number} - {self.requesting_department}"
    
    @property
    def is_overdue(self):
        """Check if expected delivery date has passed"""
        return self.expected_delivery_date < timezone.now().date()

class PurchaseRequestItem(models.Model):
    """
    Individual items in a purchase request
    """
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Item can be linked to Medicine or be generic
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_request_items'
    )
    
    # Generic item details (if not a medicine)
    item_name = models.CharField(_("Item Name"), max_length=200)
    item_description = models.TextField(_("Description"), blank=True, null=True)
    specifications = models.TextField(_("Specifications"), blank=True, null=True)
    
    quantity_requested = models.IntegerField(
        _("Quantity Requested"),
        validators=[MinValueValidator(1)]
    )
    unit_of_measure = models.CharField(
        _("Unit of Measure"),
        max_length=50,
        default='Units',
        help_text="e.g., Units, Boxes, Cartons, Litres"
    )
    
    estimated_unit_price = models.DecimalField(
        _("Estimated Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    estimated_total = models.DecimalField(
        _("Estimated Total (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Purchase Request Item")
        verbose_name_plural = _("Purchase Request Items")
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        # Auto-populate item_name from medicine if linked
        if self.medicine and not self.item_name:
            self.item_name = self.medicine.name
        
        # Calculate estimated total
        self.estimated_total = self.quantity_requested * self.estimated_unit_price
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} - Qty: {self.quantity_requested}"


class PurchaseOrder(models.Model):
    """
    Official purchase order sent to suppliers
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Supplier'),
        ('ACKNOWLEDGED', 'Acknowledged by Supplier'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('FULLY_RECEIVED', 'Fully Received'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    PAYMENT_TERMS_CHOICES = (
        ('CASH', 'Cash on Delivery'),
        ('CREDIT_7', '7 Days Credit'),
        ('CREDIT_14', '14 Days Credit'),
        ('CREDIT_30', '30 Days Credit'),
        ('CREDIT_60', '60 Days Credit'),
        ('CREDIT_90', '90 Days Credit'),
        ('ADVANCE', 'Advance Payment'),
    )
    
    # PO Identification
    po_number = models.CharField(
        _("PO Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Links
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    
    # PO Details
    po_date = models.DateField(_("PO Date"), default=timezone.now)
    expected_delivery_date = models.DateField(_("Expected Delivery Date"))
    delivery_address = models.TextField(
        _("Delivery Address"),
        help_text="Hospital delivery address"
    )
    
    # Financial
    subtotal = models.DecimalField(
        _("Subtotal (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    vat_amount = models.DecimalField(
        _("VAT Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    payment_terms = models.CharField(
        _("Payment Terms"),
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='CREDIT_30'
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    sent_to_supplier_at = models.DateTimeField(_("Sent to Supplier At"), blank=True, null=True)
    acknowledged_at = models.DateTimeField(_("Acknowledged At"), blank=True, null=True)
    
    # Terms & Conditions
    terms_and_conditions = models.TextField(
        _("Terms & Conditions"),
        blank=True,
        null=True
    )
    special_instructions = models.TextField(_("Special Instructions"), blank=True, null=True)
    
    # Documents
    po_document = models.FileField(
        _("PO Document"),
        upload_to='purchase_orders/',
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    # System Fields
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders_created',
        limit_choices_to={'user_type': 'PROCUREMENT'}
    )
    approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_approved'
    )
    approved_at = models.DateTimeField(_("Approved At"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['status']),
            models.Index(fields=['supplier']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m')
            count = PurchaseOrder.objects.filter(
                created_at__year=today.year,
                created_at__month=today.month
            ).count() + 1
            self.po_number = f"PO-{date_str}-{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.supplier_name}"
    
    @property
    def is_overdue(self):
        """Check if delivery is overdue"""
        if self.status not in ['FULLY_RECEIVED', 'CLOSED', 'CANCELLED']:
            return self.expected_delivery_date < timezone.now().date()
        return False


class PurchaseOrderItem(models.Model):
    """
    Individual items in a purchase order
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Link to medicine or generic item
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='po_items'
    )
    
    item_name = models.CharField(_("Item Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True, null=True)
    
    quantity_ordered = models.IntegerField(
        _("Quantity Ordered"),
        validators=[MinValueValidator(1)]
    )
    quantity_received = models.IntegerField(
        _("Quantity Received"),
        default=0,
        validators=[MinValueValidator(0)]
    )
    unit_of_measure = models.CharField(_("Unit of Measure"), max_length=50, default='Units')
    
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        _("Total Price (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Purchase Order Item")
        verbose_name_plural = _("Purchase Order Items")
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        # Auto-populate from medicine
        if self.medicine and not self.item_name:
            self.item_name = self.medicine.name
        
        # Calculate total
        self.total_price = self.quantity_ordered * self.unit_price
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity_ordered} @ {self.unit_price}"
    
    @property
    def quantity_pending(self):
        """Quantity yet to be received"""
        return self.quantity_ordered - self.quantity_received
    
    @property
    def is_fully_received(self):
        """Check if full quantity received"""
        return self.quantity_received >= self.quantity_ordered


class GoodsReceivedNote(models.Model):
    """
    Records goods received from suppliers
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Inspection'),
        ('INSPECTED', 'Inspected'),
        ('ACCEPTED', 'Accepted'),
        ('PARTIALLY_ACCEPTED', 'Partially Accepted'),
        ('REJECTED', 'Rejected'),
    )
    
    # GRN Identification
    grn_number = models.CharField(
        _("GRN Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='goods_received_notes'
    )
    
    # Delivery Details
    delivery_date = models.DateField(_("Delivery Date"), default=timezone.now)
    delivery_note_number = models.CharField(
        _("Delivery Note Number"),
        max_length=100,
        help_text="Supplier's delivery note number"
    )
    invoice_number = models.CharField(
        _("Invoice Number"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Receiver Details
    received_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='goods_received'
    )
    
    # Inspection
    inspected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goods_inspected'
    )
    inspected_at = models.DateTimeField(_("Inspected At"), blank=True, null=True)
    inspection_notes = models.TextField(_("Inspection Notes"), blank=True, null=True)
    
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Quality Issues
    has_quality_issues = models.BooleanField(_("Has Quality Issues"), default=False)
    quality_issues_description = models.TextField(
        _("Quality Issues"),
        blank=True,
        null=True
    )
    
    # Documents
    delivery_note = models.FileField(
        _("Delivery Note"),
        upload_to='grn/delivery_notes/',
        blank=True,
        null=True
    )
    invoice = models.FileField(
        _("Invoice"),
        upload_to='grn/invoices/',
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Goods Received Note")
        verbose_name_plural = _("Goods Received Notes")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['grn_number']),
            models.Index(fields=['purchase_order']),
            models.Index(fields=['status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.grn_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = GoodsReceivedNote.objects.filter(created_at__date=today.date()).count() + 1
            self.grn_number = f"GRN-{date_str}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.grn_number} - {self.purchase_order.po_number}"


class GoodsReceivedNoteItem(models.Model):
    """
    Individual items in a GRN
    """
    grn = models.ForeignKey(
        GoodsReceivedNote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    po_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.CASCADE,
        related_name='grn_items'
    )
    
    quantity_received = models.IntegerField(
        _("Quantity Received"),
        validators=[MinValueValidator(0)]
    )
    quantity_accepted = models.IntegerField(
        _("Quantity Accepted"),
        validators=[MinValueValidator(0)],
        default=0
    )
    quantity_rejected = models.IntegerField(
        _("Quantity Rejected"),
        validators=[MinValueValidator(0)],
        default=0
    )
    
    # Medicine specific fields
    batch_number = models.CharField(_("Batch Number"), max_length=100, blank=True, null=True)
    expiry_date = models.DateField(_("Expiry Date"), blank=True, null=True)
    manufacturer = models.CharField(_("Manufacturer"), max_length=200, blank=True, null=True)
    
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("GRN Item")
        verbose_name_plural = _("GRN Items")
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        # Update medicine stock if accepted
        if self.quantity_accepted > 0 and self.po_item.medicine:
            medicine = self.po_item.medicine
            medicine.quantity_in_stock += self.quantity_accepted
            if self.batch_number:
                medicine.batch_number = self.batch_number
            if self.expiry_date:
                medicine.expiry_date = self.expiry_date
            medicine.save()
        
        # Update PO item received quantity
        self.po_item.quantity_received += self.quantity_received
        self.po_item.save()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.po_item.item_name} - Received: {self.quantity_received}"
    
    

# ADD THESE MODELS TO YOUR EXISTING models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class LabTestCategory(models.Model):
    """
    Categories for different types of laboratory tests
    """
    CATEGORY_TYPE_CHOICES = (
        ('HEMATOLOGY', 'Hematology'),
        ('BIOCHEMISTRY', 'Biochemistry'),
        ('MICROBIOLOGY', 'Microbiology'),
        ('SEROLOGY', 'Serology'),
        ('IMMUNOLOGY', 'Immunology'),
        ('PARASITOLOGY', 'Parasitology'),
        ('HISTOPATHOLOGY', 'Histopathology'),
        ('CYTOLOGY', 'Cytology'),
        ('MOLECULAR', 'Molecular Biology'),
        ('RADIOLOGY', 'Radiology/Imaging'),
        ('ULTRASOUND', 'Ultrasound'),
        ('XRAY', 'X-Ray'),
        ('CT_SCAN', 'CT Scan'),
        ('MRI', 'MRI'),
        ('OTHER', 'Other'),
    )
    
    name = models.CharField(_("Category Name"), max_length=100)
    category_type = models.CharField(
        _("Category Type"),
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    department = models.CharField(
        _("Department"),
        max_length=100,
        help_text="Lab department handling this category"
    )
    is_active = models.BooleanField(_("Active"), default=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Test Category")
        verbose_name_plural = _("Lab Test Categories")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class LabTest(models.Model):
    """
    Master list of all available laboratory tests
    """
    SAMPLE_TYPE_CHOICES = (
        ('BLOOD', 'Blood'),
        ('URINE', 'Urine'),
        ('STOOL', 'Stool'),
        ('SPUTUM', 'Sputum'),
        ('CSF', 'Cerebrospinal Fluid'),
        ('SWAB', 'Swab'),
        ('TISSUE', 'Tissue'),
        ('FLUID', 'Body Fluid'),
        ('NONE', 'No Sample Required (Imaging)'),
        ('OTHER', 'Other'),
    )
    
    test_code = models.CharField(
        _("Test Code"),
        max_length=20,
        unique=True,
        help_text="Unique test identifier (e.g., CBC001, XRAY001)"
    )
    test_name = models.CharField(_("Test Name"), max_length=200)
    category = models.ForeignKey(
        LabTestCategory,
        on_delete=models.CASCADE,
        related_name='tests'
    )
    
    description = models.TextField(_("Description"), blank=True, null=True)
    sample_type = models.CharField(
        _("Sample Type"),
        max_length=20,
        choices=SAMPLE_TYPE_CHOICES
    )
    sample_volume = models.CharField(
        _("Sample Volume/Quantity"),
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., '5ml', '10ml EDTA tube'"
    )
    
    # Test specifications
    preparation_instructions = models.TextField(
        _("Preparation Instructions"),
        blank=True,
        null=True,
        help_text="Patient preparation (e.g., 'Fasting required')"
    )
    normal_range = models.CharField(
        _("Normal Range"),
        max_length=200,
        blank=True,
        null=True,
        help_text="Normal reference range for results"
    )
    turnaround_time = models.IntegerField(
        _("Turnaround Time (hours)"),
        default=24,
        help_text="Expected time to get results"
    )
    
    # Pricing
    cost = models.DecimalField(
        _("Test Cost (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    nhif_covered = models.BooleanField(
        _("NHIF Covered"),
        default=False
    )
    sha_covered = models.BooleanField(
        _("SHA Covered"),
        default=False
    )
    
    # Status
    is_active = models.BooleanField(_("Active"), default=True)
    requires_specialist = models.BooleanField(
        _("Requires Specialist"),
        default=False,
        help_text="Requires specialist interpretation"
    )
    
    # Usage tracking
    usage_count = models.IntegerField(_("Usage Count"), default=0)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Test")
        verbose_name_plural = _("Lab Tests")
        ordering = ['test_name']
        indexes = [
            models.Index(fields=['test_code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.test_code} - {self.test_name}"
    
    @property
    def is_imaging(self):
        """Check if test is an imaging test"""
        return self.category.category_type in ['RADIOLOGY', 'ULTRASOUND', 'XRAY', 'CT_SCAN', 'MRI']


class LabOrder(models.Model):
    """
    Laboratory test orders from doctors
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REPORTED', 'Reported'),
        ('CANCELLED', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency'),
        ('STAT', 'STAT (Immediate)'),
    )
    
    # Order Identification
    order_number = models.CharField(
        _("Order Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Links to existing models
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='lab_orders'
    )
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.CASCADE,
        related_name='lab_orders',
        blank=True,
        null=True
    )
    ordered_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='lab_orders_created',
        limit_choices_to={'user_type': 'DOCTOR'}
    )
    
    # Order Details
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='ROUTINE'
    )
    clinical_notes = models.TextField(
        _("Clinical Notes"),
        blank=True,
        null=True,
        help_text="Clinical information/provisional diagnosis"
    )
    special_instructions = models.TextField(
        _("Special Instructions"),
        blank=True,
        null=True
    )
    
    # Status tracking
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Timestamps
    ordered_at = models.DateTimeField(_("Ordered At"), auto_now_add=True)
    sample_collected_at = models.DateTimeField(_("Sample Collected At"), blank=True, null=True)
    started_at = models.DateTimeField(_("Started At"), blank=True, null=True)
    completed_at = models.DateTimeField(_("Completed At"), blank=True, null=True)
    reported_at = models.DateTimeField(_("Reported At"), blank=True, null=True)
    
    # Lab staff assignment
    assigned_to = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_lab_orders',
        limit_choices_to={'user_type': 'LAB_TECH'}
    )
    
    # Financial
    total_cost = models.DecimalField(
        _("Total Cost (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    paid = models.BooleanField(_("Paid"), default=False)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Order")
        verbose_name_plural = _("Lab Orders")
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['patient', '-ordered_at']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = LabOrder.objects.filter(created_at__date=today.date()).count() + 1
            self.order_number = f"LAB-{date_str}-{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order_number} - {self.patient.first_name} {self.patient.last_name}"
    
    @property
    def is_overdue(self):
        """Check if order is taking longer than expected"""
        if self.status not in ['COMPLETED', 'REPORTED', 'CANCELLED']:
            # Get maximum turnaround time from ordered tests
            max_turnaround = self.test_items.aggregate(
                models.Max('test__turnaround_time')
            )['test__turnaround_time__max']
            
            if max_turnaround:
                expected_completion = self.ordered_at + timezone.timedelta(hours=max_turnaround)
                return timezone.now() > expected_completion
        return False


class LabOrderItem(models.Model):
    """
    Individual tests in a lab order
    """
    lab_order = models.ForeignKey(
        LabOrder,
        on_delete=models.CASCADE,
        related_name='test_items'
    )
    test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    
    # Sample information
    sample_id = models.CharField(
        _("Sample ID"),
        max_length=50,
        blank=True,
        null=True,
        help_text="Barcode/unique sample identifier"
    )
    sample_collected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='samples_collected'
    )
    sample_quality = models.CharField(
        _("Sample Quality"),
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 'Good', 'Hemolyzed', 'Insufficient'"
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=LabOrder.STATUS_CHOICES,
        default='PENDING'
    )
    
    # Results
    result_value = models.TextField(
        _("Result Value"),
        blank=True,
        null=True
    )
    result_unit = models.CharField(
        _("Result Unit"),
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., 'mg/dl', 'cells/cmm'"
    )
    is_abnormal = models.BooleanField(_("Abnormal Result"), default=False)
    
    # Technical details
    method_used = models.CharField(
        _("Method Used"),
        max_length=200,
        blank=True,
        null=True
    )
    machine_used = models.CharField(
        _("Machine/Equipment Used"),
        max_length=200,
        blank=True,
        null=True
    )
    
    # Performed by
    performed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_tests_performed',
        limit_choices_to={'user_type': 'LAB_TECH'}
    )
    verified_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_tests_verified',
        limit_choices_to={'user_type': 'LAB_TECH'}
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Order Item")
        verbose_name_plural = _("Lab Order Items")
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.test.test_name} - {self.lab_order.order_number}"
    
    def save(self, *args, **kwargs):
        # Increment test usage count
        if self.pk is None:  # Only on creation
            self.test.usage_count += 1
            self.test.save(update_fields=['usage_count'])
        super().save(*args, **kwargs)


class LabResult(models.Model):
    """
    Detailed lab results with attachments
    """
    RESULT_TYPE_CHOICES = (
        ('NUMERIC', 'Numeric'),
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('MIXED', 'Mixed'),
    )
    
    lab_order = models.OneToOneField(
        LabOrder,
        on_delete=models.CASCADE,
        related_name='result'
    )
    
    result_type = models.CharField(
        _("Result Type"),
        max_length=20,
        choices=RESULT_TYPE_CHOICES,
        default='MIXED'
    )
    
    # Comprehensive results
    summary = models.TextField(
        _("Result Summary"),
        help_text="Overall summary of findings"
    )
    interpretation = models.TextField(
        _("Interpretation"),
        blank=True,
        null=True,
        help_text="Clinical interpretation of results"
    )
    recommendations = models.TextField(
        _("Recommendations"),
        blank=True,
        null=True
    )
    
    # Critical results
    is_critical = models.BooleanField(
        _("Critical Result"),
        default=False,
        help_text="Requires immediate attention"
    )
    critical_value_notified = models.BooleanField(
        _("Critical Value Notified"),
        default=False
    )
    notified_to = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='critical_results_received'
    )
    notified_at = models.DateTimeField(_("Notified At"), blank=True, null=True)
    
    # Attachments
    result_document = models.FileField(
        _("Result Document"),
        upload_to='lab_results/documents/',
        blank=True,
        null=True,
        help_text="PDF report, images, scans"
    )
    
    # Quality control
    quality_control_passed = models.BooleanField(
        _("Quality Control Passed"),
        default=True
    )
    qc_notes = models.TextField(_("QC Notes"), blank=True, null=True)
    
    # Authorization
    result_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='lab_results_entered',
        limit_choices_to={'user_type': 'LAB_TECH'}
    )
    verified_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_results_verified'
    )
    verified_at = models.DateTimeField(_("Verified At"), blank=True, null=True)
    
    # Patient notification
    patient_notified = models.BooleanField(_("Patient Notified"), default=False)
    result_released_to_patient = models.BooleanField(
        _("Released to Patient"),
        default=False
    )
    released_at = models.DateTimeField(_("Released At"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Result")
        verbose_name_plural = _("Lab Results")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Results for {self.lab_order.order_number}"




# models.py - UPDATE YOUR ImagingStudy MODEL

class ImagingStudy(models.Model):
    """
    Specific model for imaging/radiology studies
    Now linked to Consultation for direct orders from doctors
    """
    MODALITY_CHOICES = (
        ('XRAY', 'X-Ray'),
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('ULTRASOUND', 'Ultrasound'),
        ('MAMMOGRAPHY', 'Mammography'),
        ('FLUOROSCOPY', 'Fluoroscopy'),
        ('ANGIOGRAPHY', 'Angiography'),
        ('OTHER', 'Other'),
    )
    
    BODY_PART_CHOICES = (
        ('CHEST', 'Chest'),
        ('ABDOMEN', 'Abdomen'),
        ('PELVIS', 'Pelvis'),
        ('HEAD', 'Head/Skull'),
        ('SPINE', 'Spine'),
        ('EXTREMITIES', 'Extremities'),
        ('JOINT', 'Joint'),
        ('SOFT_TISSUE', 'Soft Tissue'),
        ('OTHER', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REPORTED', 'Reported'),
        ('CANCELLED', 'Cancelled'),
    )
    
    # UPDATED: Now can be linked to either LabOrder OR Consultation
    lab_order = models.ForeignKey(
        'LabOrder',
        on_delete=models.CASCADE,
        related_name='imaging_studies',
        blank=True,
        null=True
    )
    
    # NEW: Direct link to consultation
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.CASCADE,
        related_name='imaging_studies',
        blank=True,
        null=True
    )
    
    # NEW: Direct patient link (auto-populated from consultation/lab_order)
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='imaging_studies', blank=True, null=True
    )
    
    # NEW: Ordering doctor (auto-populated from consultation)
    ordered_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='imaging_studies_ordered',
        limit_choices_to={'user_type': 'DOCTOR'}
    )
    
    modality = models.CharField(
        _("Modality"),
        max_length=20,
        choices=MODALITY_CHOICES
    )
    body_part = models.CharField(
        _("Body Part"),
        max_length=20,
        choices=BODY_PART_CHOICES
    )
    study_description = models.CharField(
        _("Study Description"),
        max_length=500,
        help_text="e.g., 'Chest X-Ray PA and Lateral'"
    )
    
    # Clinical information
    clinical_indication = models.TextField(
        _("Clinical Indication"),
        help_text="Reason for imaging"
    )
    
    # NEW: Status tracking
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # NEW: Priority
    is_urgent = models.BooleanField(_("Urgent"), default=False)
    
    # Imaging details
    contrast_used = models.BooleanField(_("Contrast Used"), default=False)
    contrast_type = models.CharField(
        _("Contrast Type"),
        max_length=100,
        blank=True,
        null=True
    )
    radiation_dose = models.CharField(
        _("Radiation Dose"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Findings
    findings = models.TextField(
        _("Findings"),
        blank=True,
        null=True
    )
    impression = models.TextField(
        _("Impression/Conclusion"),
        blank=True,
        null=True
    )
    
    # Images
    image_1 = models.ImageField(
        _("Image 1"),
        upload_to='imaging_studies/',
        blank=True,
        null=True
    )
    image_2 = models.ImageField(
        _("Image 2"),
        upload_to='imaging_studies/',
        blank=True,
        null=True
    )
    image_3 = models.ImageField(
        _("Image 3"),
        upload_to='imaging_studies/',
        blank=True,
        null=True
    )
    image_4 = models.ImageField(
        _("Image 4"),
        upload_to='imaging_studies/',
        blank=True,
        null=True
    )
    dicom_file = models.FileField(
        _("DICOM File"),
        upload_to='imaging_studies/dicom/',
        blank=True,
        null=True,
        help_text="DICOM format for PACS integration"
    )
    
    # Staff
    performed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imaging_studies_performed',
        limit_choices_to={'user_type': 'LAB_TECH'}
    )
    reported_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imaging_studies_reported'
    )
    
    # NEW: Timestamps
    ordered_at = models.DateTimeField(_("Ordered At"), auto_now_add=True, blank=True, null=True)
    performed_at = models.DateTimeField(_("Performed At"), blank=True, null=True)
    reported_at = models.DateTimeField(_("Reported At"), blank=True, null=True)
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True, blank=True, null=True)
    
    class Meta:
        verbose_name = _("Imaging Study")
        verbose_name_plural = _("Imaging Studies")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consultation']),
            models.Index(fields=['patient', '-ordered_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_modality_display()} - {self.study_description} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Auto-populate patient from consultation or lab_order
        if not self.patient_id:
            if self.consultation:
                self.patient = self.consultation.appointment.patient
                self.ordered_by = self.consultation.appointment.doctor
            elif self.lab_order:
                self.patient = self.lab_order.patient
                self.ordered_by = self.lab_order.ordered_by
        
        super().save(*args, **kwargs)
    
    def send_completion_notification(self):
        """
        Send notification to ordering doctor when imaging is completed
        """
        if self.ordered_by and self.status == 'REPORTED':
            from .models import Notification
            
            Notification.objects.create(
                recipient=self.ordered_by,
                sender=self.reported_by,
                patient=self.patient,
                notification_type='LAB_RESULT',
                title=f'Imaging Results Ready: {self.get_modality_display()}',
                message=f'Imaging study for {self.patient.first_name} {self.patient.last_name} has been completed and reported. '
                        f'Study: {self.study_description}',
                is_urgent=self.is_urgent,
                action_url=f'/imaging/{self.id}/view/',
                related_object_id=self.id,
                related_object_type='imaging_study'
            )


# ============================================================
# ADD THIS TO YOUR models.py
# ============================================================

class ImagingPayment(models.Model):
    """
    Track payments for imaging studies
    This doesn't modify ImagingStudy model - just tracks payments separately
    """
    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    )
    
    imaging_study = models.OneToOneField(
        'ImagingStudy',
        on_delete=models.CASCADE,
        related_name='payment_record'
    )
    
    # Patient info (denormalized for easy access)
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='imaging_payments'
    )
    
    # Payment details
    amount = models.DecimalField(
        _("Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    status = models.CharField(
        _("Payment Status"),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='UNPAID'
    )
    
    # Payment reference
    payment_reference = models.CharField(
        _("Payment Reference"),
        max_length=100,
        blank=True,
        null=True,
        help_text="M-Pesa code, receipt number, etc."
    )
    
    payment_method = models.CharField(
        _("Payment Method"),
        max_length=50,
        blank=True,
        null=True,
        help_text="Cash, M-Pesa, Insurance, etc."
    )
    
    # Who processed payment
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='imaging_payments_created'
    )
    
    paid_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imaging_payments_processed',
        limit_choices_to={'user_type': 'CASHIER'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    paid_at = models.DateTimeField(_("Paid At"), blank=True, null=True)
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Imaging Payment")
        verbose_name_plural = _("Imaging Payments")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['patient', '-created_at']),
        ]
    
    def __str__(self):
        return f"Payment for {self.imaging_study} - {self.status}"
    
    @property
    def is_paid(self):
        return self.status == 'PAID'
    
class ImagingInsuranceClaim(models.Model):
    """
    Insurance claims for imaging/radiology studies
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved by Claims Officer'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Payment Confirmed'),
    )
    
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    imaging_study = models.OneToOneField(
        'ImagingStudy',
        on_delete=models.CASCADE,
        related_name='insurance_claim'
    )
    
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='imaging_insurance_claims'
    )
    
    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='imaging_claims'
    )
    
    # Claim Details
    claimed_amount = models.DecimalField(
        _("Claimed Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    approved_amount = models.DecimalField(
        _("Approved Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    patient_copay = models.DecimalField(
        _("Patient Co-pay (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Approval Details
    claims_officer_approved = models.BooleanField(
        _("Claims Officer Approved"),
        default=False
    )
    
    approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_imaging_claims',
        limit_choices_to={'user_type': 'INSURANCE'}
    )
    
    approved_at = models.DateTimeField(
        _("Approved At"),
        blank=True,
        null=True
    )
    
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True,
        null=True
    )
    
    # Payment Confirmation
    payment_confirmed = models.BooleanField(
        _("Payment Confirmed"),
        default=False
    )
    
    confirmed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_imaging_payments',
        limit_choices_to={'user_type': 'CASHIER'}
    )
    
    confirmed_at = models.DateTimeField(
        _("Payment Confirmed At"),
        blank=True,
        null=True
    )
    
    insurance_payment_received = models.BooleanField(
        _("Insurance Payment Received"),
        default=False,
        help_text="Has the insurance company paid for this claim?"
    )
    
    insurance_payment_date = models.DateField(
        _("Insurance Payment Date"),
        blank=True,
        null=True,
        help_text="Date when insurance payment was received"
    )
    
    insurance_payment_reference = models.CharField(
        _("Insurance Payment Reference"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Payment reference/transaction number from insurance company"
    )
    
    insurance_payment_notes = models.TextField(
        _("Insurance Payment Notes"),
        blank=True,
        null=True,
        help_text="Additional notes about insurance payment"
    )
    
    # System Fields
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='imaging_claims_created',
        limit_choices_to={'user_type': 'CASHIER'}
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Imaging Insurance Claim")
        verbose_name_plural = _("Imaging Insurance Claims")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['status']),
            models.Index(fields=['patient', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = ImagingInsuranceClaim.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.claim_number = f"IMG-CLM-{date_str}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.claim_number} - {self.patient} ({self.status})"



class LabEquipment(models.Model):
    """
    Laboratory equipment and machinery tracking
    """
    STATUS_CHOICES = (
        ('OPERATIONAL', 'Operational'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('CALIBRATION', 'Calibration Required'),
        ('OUT_OF_SERVICE', 'Out of Service'),
    )
    
    equipment_name = models.CharField(_("Equipment Name"), max_length=200)
    equipment_code = models.CharField(
        _("Equipment Code"),
        max_length=50,
        unique=True
    )
    manufacturer = models.CharField(_("Manufacturer"), max_length=200)
    model_number = models.CharField(_("Model Number"), max_length=100)
    serial_number = models.CharField(_("Serial Number"), max_length=100, unique=True)
    
    # Location
    location = models.CharField(
        _("Location"),
        max_length=200,
        help_text="Lab section/room"
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPERATIONAL'
    )
    
    # Maintenance
    last_maintenance = models.DateField(_("Last Maintenance"), blank=True, null=True)
    next_maintenance = models.DateField(_("Next Maintenance"), blank=True, null=True)
    last_calibration = models.DateField(_("Last Calibration"), blank=True, null=True)
    next_calibration = models.DateField(_("Next Calibration"), blank=True, null=True)
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Equipment")
        verbose_name_plural = _("Lab Equipment")
        ordering = ['equipment_name']
    
    def __str__(self):
        return f"{self.equipment_code} - {self.equipment_name}"
    
    @property
    def needs_maintenance(self):
        """Check if maintenance is due"""
        if self.next_maintenance:
            return self.next_maintenance <= timezone.now().date()
        return False


class LabStatistics(models.Model):
    """
    Daily lab statistics for reporting
    """
    date = models.DateField(_("Date"), unique=True)
    
    total_orders = models.IntegerField(_("Total Orders"), default=0)
    completed_orders = models.IntegerField(_("Completed Orders"), default=0)
    pending_orders = models.IntegerField(_("Pending Orders"), default=0)
    cancelled_orders = models.IntegerField(_("Cancelled Orders"), default=0)
    
    total_tests = models.IntegerField(_("Total Tests"), default=0)
    abnormal_results = models.IntegerField(_("Abnormal Results"), default=0)
    critical_results = models.IntegerField(_("Critical Results"), default=0)
    
    revenue = models.DecimalField(
        _("Revenue (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Lab Statistics")
        verbose_name_plural = _("Lab Statistics")
        ordering = ['-date']
    
    def __str__(self):
        return f"Lab Stats - {self.date}"
    
    
# Add this to your models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
import json


class PaymentAuditLog(models.Model):
    """
    Comprehensive audit trail for all payment transactions
    Helps prevent fraud and track all financial activities
    """
    TRANSACTION_TYPE_CHOICES = (
        ('CONSULTATION_PAYMENT', 'Consultation Payment'),
        ('MEDICINE_SALE', 'Medicine Sale'),
        ('LAB_PAYMENT', 'Laboratory Payment'),
        ('REFUND', 'Refund'),
        ('ADJUSTMENT', 'Payment Adjustment'),
        ('EMERGENCY_PAYMENT', 'emergency payment')
    )
    
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
        ('REVERSED', 'Reversed'),
    )
    
    # Transaction Details
    transaction_id = models.CharField(_("Transaction ID"),max_length=100,unique=True,db_index=True)
    transaction_type = models.CharField(_("Transaction Type"),max_length=30,choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(_("Status"),max_length=20,choices=STATUS_CHOICES,default='SUCCESS')
    
    # Financial Details
    amount = models.DecimalField(_("Amount (KSh)"),max_digits=12,decimal_places=2)
    payment_method = models.CharField(_("Payment Method"), max_length=20)
    mpesa_code = models.CharField( _("M-Pesa Code"),max_length=50,blank=True,null=True,db_index=True)
    mpesa_phone = models.CharField(_("M-Pesa Phone"),max_length=15,blank=True,null=True)
    
    # Related Records
    medicine_sale = models.ForeignKey('MedicineSale',on_delete=models.SET_NULL,null=True,blank=True,related_name='audit_logs')
    consultation = models.ForeignKey('Consultation',on_delete=models.SET_NULL,null=True,blank=True,related_name='payment_audits')
    patient = models.ForeignKey('Patient',on_delete=models.SET_NULL,null=True,blank=True,related_name='payment_audits')
    
    # Cost Breakdown (stored as JSON for detailed tracking)
    cost_breakdown = models.JSONField(_("Cost Breakdown"),blank=True,null=True,help_text="Detailed breakdown of charges")
    
    # QR Code Field - NEW
    qr_code = models.ImageField(_("QR Code"), upload_to='payment_qrcodes/', blank=True, null=True)
    qr_code_data = models.JSONField(_("QR Code Data"), blank=True, null=True, help_text="Data encoded in QR code")
    
    # User Tracking
    processed_by = models.ForeignKey('User',on_delete=models.SET_NULL,null=True,related_name='processed_payments')
    
    # IP and Session Tracking (for fraud detection)
    ip_address = models.GenericIPAddressField(_("IP Address"),blank=True,null=True)
    session_id = models.CharField(_("Session ID"),max_length=100,blank=True,null=True)
    
    # Additional Info
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Payment Audit Log")
        verbose_name_plural = _("Payment Audit Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['mpesa_code']),
            models.Index(fields=['processed_by', '-created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - KSh {self.amount} ({self.status})"
    
    def generate_qr_code(self, request=None):
        """
        Generate and save QR code for this payment transaction
        """
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile
        import json
        
        # Prepare QR code data
        qr_data = {
            "transaction_id": self.transaction_id,
            "receipt_type": "PAYMENT_RECEIPT",
            "amount": str(self.amount),
            "payment_method": self.payment_method,
            
            # Patient Information
            "patient": {
                "name": f"{self.patient.first_name} {self.patient.last_name}" if self.patient else "N/A",
               
            } if self.patient else None,
            
            # Service Information
            "service": {
                "type": self.transaction_type.replace('_', ' ').title(),
    
            } if self.cost_breakdown else None,
            
            
            # Verification Information
            "verification": {
                "system": "Hospital Management System",
                "timestamp": timezone.now().isoformat()
            }
        }
        
        # If we have a request object, add verification URL
        if request:
            verification_url = f"{request.build_absolute_uri('/')[:-1]}/payment/verify/{self.transaction_id}/"
            qr_data["verification"]["url"] = verification_url
        
        # Save QR code data to JSON field
        self.qr_code_data = qr_data
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data, indent=2))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="#000000", back_color="white")
        
        # Save image to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Save to ImageField
        filename = f"qr_{self.transaction_id}.png"
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)
        
        return qr_data

class CashierSession(models.Model):
    """
    Track cashier sessions for accountability
    Each cashier must open/close a session
    """
    SESSION_STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('RECONCILED', 'Reconciled'),
    )
    
    session_id = models.CharField(
        _("Session ID"),
        max_length=50,
        unique=True,
        editable=False
    )
    cashier = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='cashier_sessions'
    )
    
    # Session Details
    opened_at = models.DateTimeField(_("Opened At"), auto_now_add=True)
    closed_at = models.DateTimeField(_("Closed At"), blank=True, null=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        default='OPEN'
    )
    
    # Financial Tracking
    opening_balance = models.DecimalField(
        _("Opening Balance (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    expected_cash = models.DecimalField(
        _("Expected Cash (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    actual_cash = models.DecimalField(
        _("Actual Cash (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )
    cash_variance = models.DecimalField(
        _("Cash Variance (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Transaction Counts
    total_cash_transactions = models.IntegerField(_("Cash Transactions"), default=0)
    total_mpesa_transactions = models.IntegerField(_("M-Pesa Transactions"), default=0)
    total_insurance_transactions = models.IntegerField(_("Insurance Transactions"), default=0)
    total_credit_transactions = models.IntegerField(_("Credit Transactions"), default=0)
    
    # Amounts by Payment Method
    total_cash_amount = models.DecimalField(
        _("Total Cash Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_mpesa_amount = models.DecimalField(
        _("Total M-Pesa Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Reconciliation
    reconciled_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reconciled_sessions'
    )
    reconciled_at = models.DateTimeField(_("Reconciled At"), blank=True, null=True)
    reconciliation_notes = models.TextField(_("Reconciliation Notes"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Cashier Session")
        verbose_name_plural = _("Cashier Sessions")
        ordering = ['-opened_at']
    
    def save(self, *args, **kwargs):
        if not self.session_id:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d%H%M')
            self.session_id = f"CS-{self.cashier.id}-{date_str}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.session_id} - {self.cashier.get_full_name()} ({self.status})"
    
    def calculate_variance(self):
        """Calculate cash variance"""
        if self.actual_cash is not None:
            self.cash_variance = self.actual_cash - self.expected_cash
            self.save(update_fields=['cash_variance'])


class MPesaDuplicateCheck(models.Model):
    """
    Prevent duplicate M-Pesa code usage
    Fast lookup table for fraud prevention
    """
    mpesa_code = models.CharField(
        _("M-Pesa Code"),
        max_length=50,
        unique=True,
        db_index=True
    )
    medicine_sale = models.ForeignKey(
        'MedicineSale',
        on_delete=models.CASCADE,
        related_name='mpesa_checks'
    )
    used_at = models.DateTimeField(_("Used At"), auto_now_add=True)
    used_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        verbose_name = _("M-Pesa Duplicate Check")
        verbose_name_plural = _("M-Pesa Duplicate Checks")
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['mpesa_code']),
        ]
    
    def __str__(self):
        return f"{self.mpesa_code} - {self.used_at}"
    

class AuditLog(models.Model):
    """
    System audit trail for compliance and transparency
    """
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('disburse', 'Disburse'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export Data'),
        ('print', 'Print Document'),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    table_affected = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    
    # Technical details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    
    # Data changes (store as JSON for detailed tracking)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} by {self.user} on {self.timestamp}"

    

class URLVisit(models.Model):
    url_path = models.CharField(max_length=500, unique=True)
    url_name = models.CharField(max_length=200, blank=True, null=True)
    view_name = models.CharField(max_length=200, blank=True, null=True)
    visit_count = models.PositiveIntegerField(default=0)
    last_visited = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-visit_count']
    
    def __str__(self):
        return f"{self.url_path} ({self.visit_count} visits)"


class UserURLVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='url_visits')
    url_visit = models.ForeignKey(URLVisit, on_delete=models.CASCADE, related_name='user_visits')
    visited_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-visited_at']
    
    def __str__(self):
        return f"{self.user.username} visited {self.url_visit.url_path}"
    
    
class SecurityThreat(models.Model):
    """
    Log detected security threats
    """
    THREAT_TYPES = (
        ('sql_injection', 'SQL Injection'),
        ('xss', 'Cross-Site Scripting (XSS)'),
        ('path_traversal', 'Path Traversal'),
        ('code_injection', 'Code Injection'),
        ('brute_force', 'Brute Force Attack'),
        ('credential_stuffing', 'Credential Stuffing'),
        ('rate_limit', 'Rate Limit Exceeded'),
        ('suspicious_agent', 'Suspicious User Agent'),
        ('phishing', 'Phishing Attempt'),
        ('malware', 'Malware Detection'),
        ('ddos', 'DDoS Attack'),
        ('other', 'Other'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    threat_type = models.CharField(max_length=30, choices=THREAT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='security_threats'
    )
    
    description = models.TextField()
    request_path = models.CharField(max_length=500)
    request_method = models.CharField(max_length=10)
    user_agent = models.TextField(blank=True, null=True)
    request_data = models.JSONField(blank=True, null=True)
    
    # Response actions
    blocked = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_threats'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['-detected_at']),
            models.Index(fields=['severity', '-detected_at']),
            models.Index(fields=['ip_address', '-detected_at']),
            models.Index(fields=['resolved', '-detected_at']),
        ]
    
    def __str__(self):
        return f"{self.get_threat_type_display()} - {self.severity} ({self.detected_at})"


class UserSession(models.Model):
    """
    Track active user sessions for real-time monitoring
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    
    # Session details
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True, null=True)  # Mobile, Desktop, Tablet
    browser = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    
    # Location (if available)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.login_time})"
    
    def is_expired(self):
        """Check if session has been inactive for more than 30 minutes"""
        if not self.is_active:
            return True
        time_diff = timezone.now() - self.last_activity
        return time_diff > timedelta(minutes=30)


class SuspiciousActivity(models.Model):
    """
    Track suspicious user activities that might indicate phishing or compromise
    """
    ACTIVITY_TYPES = (
        ('unusual_access_pattern', 'Unusual Access Pattern'),
        ('rapid_data_access', 'Rapid Data Access'),
        ('failed_authorization', 'Multiple Failed Authorization Attempts'),
        ('data_exfiltration', 'Possible Data Exfiltration'),
        ('privilege_escalation', 'Privilege Escalation Attempt'),
        ('unusual_location', 'Access from Unusual Location'),
        ('unusual_time', 'Access at Unusual Time'),
        ('multiple_devices', 'Multiple Devices Simultaneously'),
        ('phishing_link_click', 'Phishing Link Click'),
        ('account_sharing', 'Possible Account Sharing'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suspicious_activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    
    # Risk scoring
    risk_score = models.PositiveIntegerField(default=0)  # 0-100
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100%
    
    # Evidence
    evidence = models.JSONField(blank=True, null=True)
    
    # Investigation
    investigated = models.BooleanField(default=False)
    investigated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigated_activities'
    )
    investigated_at = models.DateTimeField(null=True, blank=True)
    investigation_notes = models.TextField(blank=True, null=True)
    
    is_false_positive = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True, null=True)
    
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-detected_at']
        verbose_name_plural = "Suspicious Activities"
        indexes = [
            models.Index(fields=['-detected_at']),
            models.Index(fields=['user', '-detected_at']),
            models.Index(fields=['investigated', '-detected_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


# Add these models to your existing models.py file
# These models handle inpatient management, bed tracking, and daily billing

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class Ward(models.Model):
    """
    Hospital wards/departments for inpatient care
    """
    WARD_TYPE_CHOICES = (
        ('GENERAL', 'General Ward'),
        ('PRIVATE', 'Private Ward'),
        ('ICU', 'Intensive Care Unit'),
        ('HDU', 'High Dependency Unit'),
        ('MATERNITY', 'Maternity Ward'),
        ('PEDIATRIC', 'Pediatric Ward'),
        ('SURGICAL', 'Surgical Ward'),
        ('MEDICAL', 'Medical Ward'),
        ('ISOLATION', 'Isolation Ward'),
        ('EMERGENCY', 'Emergency Ward'),
    )
    
    ward_code = models.CharField(
        _("Ward Code"),
        max_length=20,
        unique=True,
        help_text="e.g., ICU-01, GEN-A"
    )
    ward_name = models.CharField(_("Ward Name"), max_length=100)
    ward_type = models.CharField(
        _("Ward Type"),
        max_length=20,
        choices=WARD_TYPE_CHOICES
    )
    
    floor_number = models.CharField(
        _("Floor Number"),
        max_length=10,
        blank=True,
        null=True
    )
    building = models.CharField(
        _("Building"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Capacity
    total_beds = models.PositiveIntegerField(_("Total Beds"), default=0)
    
    # Staff assignment
    nurse_in_charge = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wards_in_charge'
    )
    
    # Ward specifications
    has_oxygen = models.BooleanField(_("Has Oxygen Supply"), default=False)
    has_monitoring = models.BooleanField(_("Has Patient Monitoring"), default=False)
    has_bathroom = models.BooleanField(_("Has Attached Bathroom"), default=False)
    
    description = models.TextField(_("Description"), blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Ward")
        verbose_name_plural = _("Wards")
        ordering = ['ward_code']
        indexes = [
            models.Index(fields=['ward_code']),
            models.Index(fields=['ward_type']),
        ]
    
    def __str__(self):
        return f"{self.ward_code} - {self.ward_name}"
    
    @property
    def occupied_beds_count(self):
        """Count currently occupied beds"""
        return self.beds.filter(status='OCCUPIED').count()
    
    @property
    def available_beds_count(self):
        """Count available beds"""
        return self.beds.filter(status='AVAILABLE').count()
    
    @property
    def occupancy_rate(self):
        """Calculate occupancy percentage"""
        if self.total_beds == 0:
            return 0
        return round((self.occupied_beds_count / self.total_beds) * 100, 2)


class Bed(models.Model):
    """
    Individual bed tracking within wards
    """
    BED_STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('RESERVED', 'Reserved'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('CLEANING', 'Being Cleaned'),
        ('OUT_OF_SERVICE', 'Out of Service'),
    )
    
    BED_TYPE_CHOICES = (
        ('STANDARD', 'Standard Bed'),
        ('ICU', 'ICU Bed'),
        ('ELECTRIC', 'Electric Bed'),
        ('PEDIATRIC', 'Pediatric Bed'),
        ('MATERNITY', 'Maternity Bed'),
        ('ISOLATION', 'Isolation Bed'),
    )
    
    bed_number = models.CharField(
        _("Bed Number"),
        max_length=20,
        unique=True,
        help_text="e.g., ICU-01-A, GEN-A-05"
    )
    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name='beds'
    )
    
    bed_type = models.CharField(
        _("Bed Type"),
        max_length=20,
        choices=BED_TYPE_CHOICES,
        default='STANDARD'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=BED_STATUS_CHOICES,
        default='AVAILABLE'
    )
    
    # Bed specifications
    has_oxygen = models.BooleanField(_("Has Oxygen"), default=False)
    has_monitor = models.BooleanField(_("Has Monitor"), default=False)
    has_ventilator = models.BooleanField(_("Has Ventilator"), default=False)
    is_window_side = models.BooleanField(_("Window Side"), default=False)
    
    # Pricing
    daily_rate = models.DecimalField(
        _("Daily Rate (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Daily bed charge"
    )
    
    # Current occupant (if any)
    current_admission = models.ForeignKey(
        'InpatientAdmission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_bed'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    last_maintenance = models.DateField(_("Last Maintenance"), blank=True, null=True)
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Bed")
        verbose_name_plural = _("Beds")
        ordering = ['ward', 'bed_number']
        indexes = [
            models.Index(fields=['bed_number']),
            models.Index(fields=['ward', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.bed_number} ({self.ward.ward_code}) - {self.get_status_display()}"
    
    def is_available(self):
        """Check if bed is available for assignment"""
        return self.status == 'AVAILABLE' and self.is_active


class InpatientAdmission(models.Model):
    """
    Manages patient admissions to the hospital
    Linked to consultations for continuity of care
    """
    ADMISSION_STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('DISCHARGED', 'Discharged'),
        ('TRANSFERRED', 'Transferred'),
        ('ABSCONDED', 'Absconded'),
        ('DECEASED', 'Deceased'),
    )
    
    ADMISSION_TYPE_CHOICES = (
        ('EMERGENCY', 'Emergency Admission'),
        ('ELECTIVE', 'Elective Admission'),
        ('DIRECT', 'Direct Admission'),
        ('TRANSFER', 'Transfer from Another Facility'),
        ('OBSERVATION', 'Observation'),
    )
    
    # Admission Identification
    admission_number = models.CharField(
        _("Admission Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Patient and Links
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='inpatient_admissions'
    )
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_admissions',
        help_text="Initial consultation that led to admission"
    )
    
    # Bed Assignment
    bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        related_name='admissions'
    )
    
    # Admission Details
    admission_type = models.CharField(
        _("Admission Type"),
        max_length=20,
        choices=ADMISSION_TYPE_CHOICES,
        default='DIRECT'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ADMISSION_STATUS_CHOICES,
        default='ACTIVE'
    )
    
    # Medical Information
    admitting_diagnosis = models.TextField(_("Admitting Diagnosis"))
    icd10_codes = models.ManyToManyField(
        'ICD10Code',
        blank=True,
        related_name='inpatient_admissions'
    )
    clinical_summary = models.TextField(
        _("Clinical Summary"),
        blank=True,
        null=True
    )
    
    # Staff
    admitting_doctor = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='admitted_patients'
    )
    attending_doctor = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='attending_inpatients',
        help_text="Current doctor managing the case"
    )
    primary_nurse = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_inpatients'
    )
    
    # Timestamps
    admission_datetime = models.DateTimeField(_("Admission Date/Time"), default=timezone.now)
    expected_discharge_date = models.DateField(
        _("Expected Discharge Date"),
        blank=True,
        null=True
    )
    discharge_datetime = models.DateTimeField(
        _("Discharge Date/Time"),
        blank=True,
        null=True
    )
    
    # Discharge Information
    discharge_summary = models.TextField(_("Discharge Summary"), blank=True, null=True)
    discharge_diagnosis = models.TextField(_("Discharge Diagnosis"), blank=True, null=True)
    discharge_instructions = models.TextField(
        _("Discharge Instructions"),
        blank=True,
        null=True
    )
    discharged_by = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discharged_patients'
    )
    
    # Special Care Requirements
    requires_isolation = models.BooleanField(_("Requires Isolation"), default=False)
    isolation_reason = models.TextField(_("Isolation Reason"), blank=True, null=True)
    
    requires_monitoring = models.BooleanField(_("Requires Continuous Monitoring"), default=False)
    is_critical = models.BooleanField(_("Critical Condition"), default=False)
    
    # Diet and Mobility
    diet_order = models.CharField(
        _("Diet Order"),
        max_length=200,
        blank=True,
        null=True,
        help_text="e.g., NPO, Clear Liquids, Regular Diet"
    )
    mobility_status = models.CharField(
        _("Mobility Status"),
        max_length=200,
        blank=True,
        null=True,
        help_text="e.g., Bed Rest, Ambulatory with Assistance"
    )
    
    # Financial
    deposit_amount = models.DecimalField(
        _("Deposit Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_charges = models.DecimalField(
        _("Total Charges (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Accumulated charges during stay"
    )
    amount_paid = models.DecimalField(
        _("Amount Paid (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Insurance
    is_insured = models.BooleanField(_("Insured"), default=False)
    insurance_company = models.CharField(
        _("Insurance Company"),
        max_length=200,
        blank=True,
        null=True
    )
    insurance_policy_number = models.CharField(
        _("Policy Number"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        _("Emergency Contact Name"),
        max_length=200,
        blank=True,
        null=True
    )
    emergency_contact_phone = models.CharField(
        _("Emergency Contact Phone"),
        max_length=15,
        blank=True,
        null=True
    )
    emergency_contact_relationship = models.CharField(
        _("Relationship"),
        max_length=100,
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='admissions_created')
    
    class Meta:
        verbose_name = _("Inpatient Admission")
        verbose_name_plural = _("Inpatient Admissions")
        ordering = ['-admission_datetime']
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['patient', '-admission_datetime']),
            models.Index(fields=['status']),
            models.Index(fields=['bed']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate admission number
        if not self.admission_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = InpatientAdmission.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.admission_number = f"IPD-{date_str}-{count:05d}"
        
        # Check if this is a new admission and we have a bed
        is_new = self.pk is None
        has_bed = self.bed is not None
        
        # Save the admission first
        super().save(*args, **kwargs)
        
        # Now update bed if needed
        if is_new and has_bed and self.bed.status == 'AVAILABLE':
            self.bed.status = 'OCCUPIED'
            self.bed.current_admission = self
            self.bed.save()
    
    def __str__(self):
        return f"{self.admission_number} - {self.patient.first_name} {self.patient.last_name}"
    
    @property
    def length_of_stay(self):
        """Calculate length of stay in days"""
        if self.discharge_datetime:
            end_time = self.discharge_datetime
        else:
            end_time = timezone.now()
        
        delta = end_time - self.admission_datetime
        return delta.days + 1  # Include admission day
    
    @property
    def outstanding_balance(self):
        """Calculate outstanding balance"""
        return self.total_charges - self.amount_paid
    
    @property
    def ward_name(self):
        """Get ward name"""
        if self.bed:
            return self.bed.ward.ward_name
        return None
    
    def discharge(self, discharged_by, discharge_summary, discharge_diagnosis):
        """Discharge the patient"""
        self.status = 'DISCHARGED'
        self.discharge_datetime = timezone.now()
        self.discharged_by = discharged_by
        self.discharge_summary = discharge_summary
        self.discharge_diagnosis = discharge_diagnosis
        
        # Free up the bed
        if self.bed:
            self.bed.status = 'CLEANING'
            self.bed.current_admission = None
            self.bed.save()
        
        self.save()


class InpatientDailyCharge(models.Model):
    """
    Daily charges for inpatient stay
    Automatically tracks bed charges and services
    """
    CHARGE_TYPE_CHOICES = (
        ('BED', 'Bed Charge'),
        ('NURSING', 'Nursing Care'),
        ('DOCTOR_VISIT', 'Doctor Visit'),
        ('CONSULTATION', 'Consultation'),
        ('PROCEDURE', 'Procedure'),
        ('MEDICINE', 'Medicine'),
        ('LAB_TEST', 'Laboratory Test'),
        ('IMAGING', 'Imaging/Radiology'),
        ('SURGERY', 'Surgery'),
        ('THERAPY', 'Therapy'),
        ('OXYGEN', 'Oxygen'),
        ('MONITORING', 'Monitoring'),
        ('EQUIPMENT', 'Equipment Use'),
        ('SUPPLIES', 'Medical Supplies'),
        ('MEALS', 'Meals'),
        ('OTHER', 'Other'),
    )
    
    admission = models.ForeignKey(
        InpatientAdmission,
        on_delete=models.CASCADE,
        related_name='daily_charges'
    )
    
    charge_date = models.DateField(_("Charge Date"), default=timezone.now)
    charge_type = models.CharField(
        _("Charge Type"),
        max_length=20,
        choices=CHARGE_TYPE_CHOICES
    )
    
    description = models.CharField(_("Description"), max_length=500)
    quantity = models.DecimalField(
        _("Quantity"),
        max_digits=10,
        decimal_places=2,
        default=1
    )
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Links to services
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_charges'
    )
    lab_order = models.ForeignKey(
        'LabOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_charges'
    )
    prescription = models.ForeignKey(
        'Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_charges'
    )
    imaging_study = models.ForeignKey(
        'ImagingStudy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_charges'
    )
    
    # Staff who rendered service
    rendered_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services_rendered'
    )
    
    # Billing
    is_billed = models.BooleanField(_("Billed"), default=False)
    is_paid = models.BooleanField(_("Paid"), default=False)
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='charges_created'
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Inpatient Daily Charge")
        verbose_name_plural = _("Inpatient Daily Charges")
        ordering = ['-charge_date', '-created_at']
        indexes = [
            models.Index(fields=['admission', '-charge_date']),
            models.Index(fields=['charge_type']),
            models.Index(fields=['is_billed', 'is_paid']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.quantity * self.unit_price
        
        super().save(*args, **kwargs)
        
        # Update admission total charges
        self.admission.total_charges = self.admission.daily_charges.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0
        self.admission.save(update_fields=['total_charges'])
    
    def __str__(self):
        return f"{self.get_charge_type_display()} - {self.charge_date} - KSh {self.total_amount}"


class InpatientVitals(models.Model):
    """
    Regular vital signs monitoring for inpatients
    """
    admission = models.ForeignKey(
        InpatientAdmission,
        on_delete=models.CASCADE,
        related_name='vital_signs'
    )
    
    recorded_at = models.DateTimeField(_("Recorded At"), default=timezone.now)
    
    # Vital Signs
    temperature = models.DecimalField(
        _("Temperature (°C)"),
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(30), MinValueValidator(45)],
        blank=True,
        null=True
    )
    blood_pressure_systolic = models.IntegerField(
        _("BP Systolic (mmHg)"),
        blank=True,
        null=True
    )
    blood_pressure_diastolic = models.IntegerField(
        _("BP Diastolic (mmHg)"),
        blank=True,
        null=True
    )
    pulse_rate = models.IntegerField(
        _("Pulse Rate (bpm)"),
        blank=True,
        null=True
    )
    respiratory_rate = models.IntegerField(
        _("Respiratory Rate (breaths/min)"),
        blank=True,
        null=True
    )
    oxygen_saturation = models.IntegerField(
        _("Oxygen Saturation (%)"),
        blank=True,
        null=True
    )
    weight = models.DecimalField(
        _("Weight (kg)"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Additional Assessments
    pain_score = models.IntegerField(
        _("Pain Score (0-10)"),
        validators=[MinValueValidator(0), MinValueValidator(10)],
        blank=True,
        null=True
    )
    consciousness_level = models.CharField(
        _("Consciousness Level"),
        max_length=100,
        blank=True,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    recorded_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_vitals'
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Inpatient Vitals")
        verbose_name_plural = _("Inpatient Vitals")
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['admission', '-recorded_at']),
        ]
    
    def __str__(self):
        return f"Vitals for {self.admission.patient} - {self.recorded_at}"


class BedTransferHistory(models.Model):
    """
    Track bed transfers within the hospital
    """
    admission = models.ForeignKey(
        InpatientAdmission,
        on_delete=models.CASCADE,
        related_name='bed_transfers'
    )
    
    from_bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfers_from'
    )
    to_bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfers_to'
    )
    
    transfer_datetime = models.DateTimeField(_("Transfer Date/Time"), default=timezone.now)
    reason = models.TextField(_("Reason for Transfer"))
    
    authorized_by = models.ForeignKey(
        'Doctor',
        on_delete=models.SET_NULL,
        null=True,
        related_name='authorized_bed_transfers'
    )
    performed_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_bed_transfers'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Bed Transfer History")
        verbose_name_plural = _("Bed Transfer Histories")
        ordering = ['-transfer_datetime']
    
    def __str__(self):
        return f"{self.admission.patient} - {self.from_bed} to {self.to_bed}"


class InpatientMedicationAdministration(models.Model):
    """
    Track medication administration for inpatients
    """
    ADMINISTRATION_STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('ADMINISTERED', 'Administered'),
        ('MISSED', 'Missed'),
        ('REFUSED', 'Patient Refused'),
        ('HELD', 'Held'),
    )
    
    admission = models.ForeignKey(
        InpatientAdmission,
        on_delete=models.CASCADE,
        related_name='medication_administrations'
    )
    prescription = models.ForeignKey(
        'Prescription',
        on_delete=models.CASCADE,
        related_name='administrations',
        blank=True,  # ADD THIS
        null=True    # ADD THIS
    )
    
    scheduled_time = models.DateTimeField(_("Scheduled Time"))
    administered_time = models.DateTimeField(_("Administered Time"), blank=True, null=True)
    
    dosage = models.CharField(_("Dosage"), max_length=100)
    route = models.CharField(
        _("Route"),
        max_length=50,
        help_text="e.g., Oral, IV, IM, SC"
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ADMINISTRATION_STATUS_CHOICES,
        default='SCHEDULED'
    )
    
    administered_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medications_administered'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Medication Administration")
        verbose_name_plural = _("Medication Administrations")
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['admission', '-scheduled_time']),
            models.Index(fields=['status', '-scheduled_time']),
        ]
    
    def __str__(self):
        return f"{self.prescription.medicine.name} - {self.scheduled_time}"
    
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class InpatientMedicineRequest(models.Model):
    """
    Medicine requests from nurses for inpatient care
    Pharmacy approves and dispenses
    """
    REQUEST_STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved - Ready for Collection'),
        ('DISPENSED', 'Dispensed to Nurse'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency - STAT'),
    )
    
    # Request Identification
    request_number = models.CharField(
        _("Request Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Patient & Admission
    admission = models.ForeignKey(
        'InpatientAdmission',
        on_delete=models.CASCADE,
        related_name='medicine_requests'
    )
    
    # Medicine Details
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.CASCADE,
        related_name='inpatient_requests'
    )
    quantity_requested = models.PositiveIntegerField(
        _("Quantity Requested (Units)"),
        validators=[MinValueValidator(1)],
        help_text="Number of units needed (e.g., tablets, ml)"
    )
    
    # Clinical Information
    dosage = models.CharField(
        _("Dosage"),
        max_length=200,
        help_text="e.g., 500mg, 10ml"
    )
    route = models.CharField(
        _("Route"),
        max_length=50,
        default='Oral',
        help_text="e.g., Oral, IV, IM, SC"
    )
    frequency = models.CharField(
        _("Frequency"),
        max_length=200,
        blank=True,
        null=True,
        help_text="e.g., twice daily, every 6 hours"
    )
    duration = models.CharField(
        _("Duration"),
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 7 days, until discharge"
    )
    
    # Priority & Status
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='ROUTINE'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=REQUEST_STATUS_CHOICES,
        default='PENDING'
    )
    
    # Request Details
    clinical_notes = models.TextField(
        _("Clinical Notes"),
        blank=True,
        null=True,
        help_text="Patient condition, reason for medication"
    )
    
    # Staff - Requester (Nurse)
    requested_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        related_name='medicine_requests_made'
    )
    requested_at = models.DateTimeField(_("Requested At"), auto_now_add=True)
    
    # Staff - Pharmacy Approval
    approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests_approved'
    )
    approved_at = models.DateTimeField(_("Approved At"), blank=True, null=True)
    
    quantity_approved = models.PositiveIntegerField(
        _("Quantity Approved"),
        blank=True,
        null=True,
        help_text="Actual quantity approved (may differ from requested)"
    )
    
    # Staff - Dispensing
    dispensed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests_dispensed'
    )
    dispensed_at = models.DateTimeField(_("Dispensed At"), blank=True, null=True)
    
    # Staff - Collector (Nurse who collects)
    collected_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests_collected'
    )
    collected_at = models.DateTimeField(_("Collected At"), blank=True, null=True)
    
    # Rejection
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True,
        null=True
    )
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests_rejected'
    )
    rejected_at = models.DateTimeField(_("Rejected At"), blank=True, null=True)
    
    # Pricing (calculated at dispensing)
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_cost = models.DecimalField(
        _("Total Cost (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Link to prescription if exists
    prescription = models.ForeignKey(
        'Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests'
    )
    
    # Link to charge created
    daily_charge = models.ForeignKey(
        'InpatientDailyCharge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests'
    )
    
    # Link to medication administration
    medication_administration = models.ForeignKey(
        'InpatientMedicationAdministration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_requests'
    )
    
    notes = models.TextField(_("Additional Notes"), blank=True, null=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Inpatient Medicine Request")
        verbose_name_plural = _("Inpatient Medicine Requests")
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['admission', '-requested_at']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['medicine', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate request number
        if not self.request_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = InpatientMedicineRequest.objects.filter(
                requested_at__date=today.date()
            ).count() + 1
            self.request_number = f"MR-{date_str}-{count:05d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.request_number} - {self.medicine.name} ({self.get_status_display()})"
    
    @property
    def patient_name(self):
        """Get patient name"""
        return f"{self.admission.patient.first_name} {self.admission.patient.last_name}"
    
    @property
    def ward_name(self):
        """Get ward name"""
        if self.admission.bed:
            return self.admission.bed.ward.ward_name
        return "No Ward"
    
    @property
    def bed_number(self):
        """Get bed number"""
        if self.admission.bed:
            return self.admission.bed.bed_number
        return "No Bed"
    
    @property
    def is_pending(self):
        """Check if request is pending"""
        return self.status == 'PENDING'
    
    @property
    def is_approved(self):
        """Check if request is approved"""
        return self.status == 'APPROVED'
    
    @property
    def is_dispensed(self):
        """Check if request is dispensed"""
        return self.status == 'DISPENSED'
    
    @property
    def time_elapsed(self):
        """Time since request was made"""
        if self.status == 'DISPENSED' and self.dispensed_at:
            return self.dispensed_at - self.requested_at
        return timezone.now() - self.requested_at
    
    @property
    def time_elapsed_minutes(self):
        """Time elapsed in minutes"""
        delta = self.time_elapsed
        return int(delta.total_seconds() / 60)
    
    def approve(self, user, quantity_approved=None):
        """Approve the request"""
        if self.status != 'PENDING':
            raise ValueError("Only pending requests can be approved")
        
        # Check stock availability
        qty_to_approve = quantity_approved or self.quantity_requested
        
        if qty_to_approve > self.medicine.quantity_in_stock:
            raise ValueError(
                f"Insufficient stock. Available: {self.medicine.quantity_in_stock}, "
                f"Requested: {qty_to_approve}"
            )
        
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.quantity_approved = qty_to_approve
        self.save()
    
    def reject(self, user, reason):
        """Reject the request"""
        if self.status != 'PENDING':
            raise ValueError("Only pending requests can be rejected")
        
        self.status = 'REJECTED'
        self.rejected_by = user
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def dispense(self, user, collector_nurse):
        """Dispense the medication"""
        if self.status != 'APPROVED':
            raise ValueError("Only approved requests can be dispensed")
        
        qty_to_dispense = self.quantity_approved or self.quantity_requested
        
        # Check stock
        if qty_to_dispense > self.medicine.quantity_in_stock:
            raise ValueError(
                f"Insufficient stock. Available: {self.medicine.quantity_in_stock}"
            )
        
        # Calculate pricing
        is_insured = self.admission.is_insured
        if is_insured:
            unit_price = self.medicine.price_per_unit_insurance
        else:
            unit_price = self.medicine.price_per_unit_cash
        
        total_cost = qty_to_dispense * unit_price
        
        self.unit_price = unit_price
        self.total_cost = total_cost
        
        # Update stock
        previous_stock = self.medicine.quantity_in_stock
        self.medicine.quantity_in_stock -= qty_to_dispense
        self.medicine.save()
        
        # Record stock movement
        from .models import StockMovement
        StockMovement.objects.create(
            medicine=self.medicine,
            movement_type='SALE',
            quantity=-qty_to_dispense,
            previous_quantity=previous_stock,
            new_quantity=self.medicine.quantity_in_stock,
            reason=f"Dispensed for inpatient request {self.request_number} - {self.patient_name}",
            performed_by=user
        )
        
        # Create daily charge
        from .models import InpatientDailyCharge
        charge = InpatientDailyCharge.objects.create(
            admission=self.admission,
            charge_date=timezone.now().date(),
            charge_type='MEDICINE',
            description=f"{self.medicine.name} - {qty_to_dispense} {self.medicine.get_unit_type_display()} (Request: {self.request_number})",
            quantity=qty_to_dispense,
            unit_price=unit_price,
            total_amount=total_cost,
            prescription=self.prescription,
            rendered_by=user,
            created_by=user,
            notes=f"Request {self.request_number} - Dispensed by {user.get_full_name()} to {collector_nurse.first_name} {collector_nurse.last_name}"
        )
        
        self.daily_charge = charge
        
        # Update status
        self.status = 'DISPENSED'
        self.dispensed_by = user
        self.dispensed_at = timezone.now()
        self.collected_by = collector_nurse
        self.collected_at = timezone.now()
        self.save()
        
        return {
            'success': True,
            'message': f"Successfully dispensed {qty_to_dispense} {self.medicine.get_unit_type_display()} of {self.medicine.name}",
            'charge': charge,
            'total_cost': total_cost
        }
    
    def cancel(self):
        """Cancel the request"""
        if self.status in ['DISPENSED', 'REJECTED']:
            raise ValueError("Cannot cancel dispensed or rejected requests")
        
        self.status = 'CANCELLED'
        self.save()


# Add this to your existing models.py file   
# Add these models to your existing models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

# Add these models to your existing models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

class EmergencyBed(models.Model):
    """
    Dedicated emergency beds (not part of wards)
    These are for immediate treatment, not admission
    """
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Under Maintenance'),
    )
    
    bed_number = models.CharField(
        _("Emergency Bed Number"),
        max_length=20,
        unique=True,
        help_text="e.g., ER-01, ER-02, TRAUMA-01"
    )
    location = models.CharField(
        _("Location"),
        max_length=100,
        help_text="e.g., Emergency Room A, Trauma Bay 1"
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='AVAILABLE'
    )
    
    # Equipment
    has_oxygen = models.BooleanField(_("Has Oxygen"), default=True)
    has_monitor = models.BooleanField(_("Has Monitor"), default=True)
    has_suction = models.BooleanField(_("Has Suction"), default=True)
    
    # Current occupant
    current_emergency_visit = models.ForeignKey(
        'EmergencyVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_bed_assignment'
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Emergency Bed")
        verbose_name_plural = _("Emergency Beds")
        ordering = ['bed_number']
    
    def __str__(self):
        return f"{self.bed_number} - {self.get_status_display()}"


class EmergencyCharge(models.Model):
    """
    Track charges during emergency treatment
    """
    CHARGE_TYPE_CHOICES = (
        ('TREATMENT', 'Emergency Treatment'),
        ('MEDICINE', 'Medicine'),
        ('PROCEDURE', 'Procedure'),
        ('SUPPLIES', 'Medical Supplies'),
        ('OXYGEN', 'Oxygen'),
        ('MONITORING', 'Monitoring'),
        ('XRAY', 'X-Ray'),
        ('LAB_TEST', 'Lab Test'),
        ('SUTURING', 'Suturing/Stitches'),
        ('DRESSING', 'Wound Dressing'),
        ('IV_FLUIDS', 'IV Fluids'),
        ('BLOOD', 'Blood Transfusion'),
        ('CONSULTATION', 'Specialist Consultation'),
        ('OTHER', 'Other'),
    )
    
    emergency_visit = models.ForeignKey(
        'EmergencyVisit',
        on_delete=models.CASCADE,
        related_name='charges'
    )
    
    charge_type = models.CharField(
        _("Charge Type"),
        max_length=20,
        choices=CHARGE_TYPE_CHOICES
    )
    description = models.CharField(_("Description"), max_length=500)
    
    quantity = models.DecimalField(
        _("Quantity"),
        max_digits=10,
        decimal_places=2,
        default=1
    )
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    charged_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='emergency_charges_created'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Emergency Charge")
        verbose_name_plural = _("Emergency Charges")
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_charge_type_display()} - KSh {self.total_amount}"


# Replace your EmergencyVisit model with this clean version
# Keep EmergencyBed and EmergencyCharge as they are

class EmergencyVisit(models.Model):
    """
    Emergency/Casualty/Trauma specific details
    Enhanced with billing and bed tracking
    """
    TRIAGE_LEVEL_CHOICES = (
        ('RED', 'Red - Life Threatening'),
        ('ORANGE', 'Orange - Emergency'),
        ('YELLOW', 'Yellow - Urgent'),
        ('GREEN', 'Green - Less Urgent'),
        ('BLUE', 'Blue - Non-Urgent'),
    )
    
    ARRIVAL_MODE_CHOICES = (
        ('AMBULANCE', 'Ambulance'),
        ('POLICE', 'Police Vehicle'),
        ('PRIVATE', 'Private Vehicle'),
        ('WALK_IN', 'Walk In'),
        ('CARRIED', 'Carried/Stretcher'),
    )
    
    INJURY_TYPE_CHOICES = (
        ('RTA', 'Road Traffic Accident'),
        ('ASSAULT', 'Assault/Violence'),
        ('FALL', 'Fall'),
        ('BURN', 'Burn'),
        ('POISONING', 'Poisoning'),
        ('MEDICAL', 'Medical Emergency'),
        ('OBSTETRIC', 'Obstetric Emergency'),
        ('OTHER', 'Other'),
    )
    
    TREATMENT_STATUS_CHOICES = (
        ('IN_EMERGENCY', 'In Emergency'),
        ('STABILIZED', 'Stabilized'),
        ('READY_FOR_ADMISSION', 'Ready for Admission'),
        ('ADMITTED', 'Admitted to Ward'),
        ('DISCHARGED', 'Discharged'),
        ('REFERRED', 'Referred to Another Facility'),
        ('DECEASED', 'Deceased'),
    )
    
    # Link to visit
    visit = models.OneToOneField('PatientVisit',on_delete=models.CASCADE,related_name='emergency_details')
    
    # Emergency Details
    triage_level = models.CharField(_("Triage Level"),max_length=10,choices=TRIAGE_LEVEL_CHOICES,default='YELLOW')
    arrival_mode = models.CharField(_("Arrival Mode"),max_length=20,choices=ARRIVAL_MODE_CHOICES)
    injury_type = models.CharField(_("Type of Injury/Emergency"),max_length=20,choices=INJURY_TYPE_CHOICES)
    
    # Clinical Status
    is_conscious = models.BooleanField(_("Conscious"), default=True)
    is_breathing = models.BooleanField(_("Breathing Normally"), default=True)
    has_pulse = models.BooleanField(_("Has Pulse"), default=True)
    glasgow_coma_scale = models.IntegerField(_("Glasgow Coma Scale"),validators=[MinValueValidator(3), MaxValueValidator(15)],blank=True,null=True)
    
    # Immediate Actions Needed
    needs_resuscitation = models.BooleanField(_("Needs Resuscitation"), default=False)
    needs_oxygen = models.BooleanField(_("Needs Oxygen"), default=False)
    needs_intubation = models.BooleanField(_("Needs Intubation"), default=False)
    needs_surgery = models.BooleanField(_("Needs Emergency Surgery"), default=False)
    
    # Police/Legal
    police_case = models.BooleanField(_("Police Case"), default=False)
    police_station = models.CharField(_("Police Station"),max_length=200,blank=True,null=True)
    ob_number = models.CharField(_("OB Number"),max_length=100,blank=True,null=True)
    
    # Assessment
    initial_assessment = models.TextField(_("Initial Assessment"))
    immediate_treatment_given = models.TextField(_("Immediate Treatment Given"),blank=True,null=True)
    
    # Emergency Bed Assignment (NEW - for emergency beds, not ward beds)
    emergency_bed = models.ForeignKey('EmergencyBed',on_delete=models.SET_NULL,null=True,blank=True,related_name='emergency_visits',help_text="Emergency treatment bed (not ward bed)")
    
    # Treatment Status (NEW)
    treatment_status = models.CharField(_("Treatment Status"),max_length=30,choices=TREATMENT_STATUS_CHOICES,default='IN_EMERGENCY')
    
    # Monitoring duration (NEW)
    monitoring_started = models.DateTimeField(_("Monitoring Started"),default=timezone.now)
    monitoring_ended = models.DateTimeField(_("Monitoring Ended"),null=True,blank=True)
    
    # Requires extended monitoring (1+ days) (NEW)
    requires_extended_monitoring = models.BooleanField(_("Requires Extended Monitoring"),default=False,help_text="If True, bed charges will apply")
    
    # Billing (NEW)
    total_charges = models.DecimalField(_("Total Charges (KSh)"),max_digits=12,decimal_places=2,default=0)
    is_paid = models.BooleanField(_("Paid"), default=False)
    payment_method = models.CharField(_("Payment Method"),max_length=50,blank=True,null=True)
    
    # Admission details (NEW - if patient needs ward admission)
    needs_admission = models.BooleanField(_("Needs Admission"), default=False)
    admission_reason = models.TextField(_("Admission Reason"),blank=True,null=True)
    transferred_to_ward = models.ForeignKey('Ward',on_delete=models.SET_NULL,null=True,blank=True,related_name='emergency_transfers')
    transferred_to_admission = models.ForeignKey('InpatientAdmission',on_delete=models.SET_NULL,null=True,blank=True,related_name='emergency_transfers')
    transferred_at = models.DateTimeField(_("Transferred At"),null=True,blank=True)
    
    # Staff
    assessed_by = models.ForeignKey('Nurse',on_delete=models.SET_NULL,null=True,blank=True,related_name='emergency_assessments')
    # Add these new fields if not already present
    payment_status = models.CharField(_("Payment Status"),max_length=20,
        choices=[
            ('UNPAID', 'Unpaid'),
            ('PARTIAL', 'Partially Paid'),
            ('PAID', 'Paid'),
        ],default='UNPAID')
    discharge_summary = models.TextField(_("Discharge Summary"),blank=True,null=True)
    follow_up_instructions = models.TextField(_("Follow-up Instructions"),blank=True,null=True)
    last_observation_charge = models.DateTimeField(_("Last Observation Charge"),blank=True,null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Emergency Visit")
        verbose_name_plural = _("Emergency Visits")
        ordering = ['-monitoring_started']
    
    def auto_add_observation_charges(self):
        """
        Automatically add observation/monitoring charges if patient stays > 3 hours
        Charges hourly after 3 hours
        """
        if self.treatment_status not in ['IN_EMERGENCY', 'STABILIZED']:
            return
        
        # Calculate hours since admission
        time_elapsed = timezone.now() - self.monitoring_started
        hours_elapsed = int(time_elapsed.total_seconds() / 3600)
        
        # Only charge if > 3 hours
        if hours_elapsed <= 3:
            return
        
        # Determine last charge time
        if self.last_observation_charge:
            time_since_last_charge = timezone.now() - self.last_observation_charge
            hours_since_last_charge = int(time_since_last_charge.total_seconds() / 3600)
            
            # Only add charge if at least 1 hour passed
            if hours_since_last_charge < 1:
                return
        else:
            # First observation charge after 3 hours
            hours_since_last_charge = hours_elapsed - 3
        
        # Add observation charges for each hour
        if hours_since_last_charge >= 1:
            observation_rate = Decimal('200.00')  # KSh 200 per hour
            
            # Check if we already have a charge for this hour
            latest_charge = self.charges.filter(
                charge_type='MONITORING',
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).first()
            
            if not latest_charge:
                EmergencyCharge.objects.create(
                    emergency_visit=self,
                    charge_type='MONITORING',
                    description=f'Emergency Observation/Monitoring - Hour {hours_elapsed}',
                    quantity=1,
                    unit_price=observation_rate,
                    charged_by=None,  # System-generated
                    notes='Auto-generated observation charge'
                )
                
                self.last_observation_charge = timezone.now()
                self.save(update_fields=['last_observation_charge'])
    
    def calculate_total_charges(self):
        """
        Calculate total emergency charges including all services
        """
        total = self.charges.aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Update the stored total
        self.total_charges = total
        self.save(update_fields=['total_charges'])
        
        return total
    
    def calculate_amount_paid(self):
        """
        Calculate total amount paid for this emergency visit
        """
        from django.db.models import Sum
        
        payments =  EmergencyPayment.objects.filter(
            emergency_visit=self
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        return payments
    
    @property
    def monitoring_hours(self):
        """Calculate hours in emergency"""
        if self.monitoring_ended:
            duration = self.monitoring_ended - self.monitoring_started
        else:
            duration = timezone.now() - self.monitoring_started
        return int(duration.total_seconds() / 3600)
    
    @property
    def monitoring_days(self):
        """Calculate days in emergency"""
        if self.monitoring_ended:
            duration = self.monitoring_ended - self.monitoring_started
        else:
            duration = timezone.now() - self.monitoring_started
        return duration.days
    
    def __str__(self):
        return f"Emergency - {self.visit.visit_number}"
    
    def transfer_to_inpatient(self, ward, bed, doctor, reason):
        """Transfer patient from emergency to inpatient ward"""
        from .models import InpatientAdmission
        
        # Create inpatient admission
        admission = InpatientAdmission.objects.create(
            patient=self.visit.patient,
            admission_type='TRANSFER',
            bed=bed,
            admitting_diagnosis=reason,
            clinical_summary=f"Transferred from Emergency. Original complaint: {self.visit.chief_complaint}. "
                           f"Emergency assessment: {self.initial_assessment}",
            admitting_doctor=doctor,
            attending_doctor=doctor,
            admission_datetime=timezone.now(),
            notes=f"Emergency transfer from {self.visit.visit_number}. "
                  f"Emergency stay: {self.monitoring_hours} hours",
            created_by=doctor.user if doctor else None
        )
        
        # Update emergency visit
        self.treatment_status = 'ADMITTED'
        self.needs_admission = True
        self.transferred_to_ward = ward
        self.transferred_to_admission = admission
        self.transferred_at = timezone.now()
        self.monitoring_ended = timezone.now()
        self.save()
        
        # Update emergency bed
        if self.emergency_bed:
            self.emergency_bed.status = 'AVAILABLE'
            self.emergency_bed.current_emergency_visit = None
            self.emergency_bed.save()
        
        # Update ward bed
        bed.status = 'OCCUPIED'
        bed.current_admission = admission
        bed.save()
        
        # Update visit status
        self.visit.status = 'ADMITTED'
        self.visit.save()
        
        return admission


# Add EmergencyPayment model if not exists
class EmergencyPayment(models.Model):
    """
    Track payments for emergency visits
    """
    emergency_visit = models.ForeignKey(
        'EmergencyVisit',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    amount = models.DecimalField(
        _("Amount Paid (KSh)"),
        max_digits=10,
        decimal_places=2
    )
    
    payment_method = models.CharField(
        _("Payment Method"),
        max_length=20,
        choices=[
            ('CASH', 'Cash'),
            ('MPESA', 'M-Pesa'),
            ('CARD', 'Card'),
            ('INSURANCE', 'Insurance'),
            ('NHIF', 'NHIF'),
            ('SHA', 'SHA'),
        ]
    )
    
    mpesa_code = models.CharField(
        _("M-Pesa Code"),
        max_length=50,
        blank=True,
        null=True
    )
    
    processed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='emergency_payments_processed'
    )
    
    created_at = models.DateTimeField(_("Paid At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Emergency Payment")
        verbose_name_plural = _("Emergency Payments")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - KSh {self.amount}"


# Add these new models to your models.py file

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class EmergencyMedicineRequest(models.Model):
    """
    Medicine requests from emergency to pharmacy
    """
    REQUEST_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved & Dispensed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )
    
    emergency_visit = models.ForeignKey(
        'EmergencyVisit',
        on_delete=models.CASCADE,
        related_name='medicine_requests'
    )
    medicine = models.ForeignKey(
        'Medicine',
        on_delete=models.CASCADE,
        related_name='emergency_requests'
    )
    
    quantity_requested = models.DecimalField(
        _("Quantity Requested"),
        max_digits=10,
        decimal_places=2
    )
    quantity_dispensed = models.DecimalField(
        _("Quantity Dispensed"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    route = models.CharField(
        _("Administration Route"),
        max_length=20,
        choices=[
            ('ORAL', 'Oral'),
            ('IV', 'Intravenous'),
            ('IM', 'Intramuscular'),
            ('SC', 'Subcutaneous'),
            ('TOPICAL', 'Topical'),
            ('RECTAL', 'Rectal'),
            ('SUBLINGUAL', 'Sublingual'),
        ],
        default='ORAL'
    )
    
    urgency = models.CharField(
        _("Urgency"),
        max_length=20,
        choices=[
            ('STAT', 'STAT (Immediate)'),
            ('URGENT', 'Urgent'),
            ('ROUTINE', 'Routine'),
        ],
        default='URGENT'
    )
    
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=REQUEST_STATUS_CHOICES,
        default='PENDING'
    )
    
    # Request details
    requested_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='emergency_medicine_requests'
    )
    request_notes = models.TextField(_("Request Notes"), blank=True, null=True)
    requested_at = models.DateTimeField(_("Requested At"), auto_now_add=True)
    
    # Approval/Dispensing details
    dispensed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_emergency_medicines'
    )
    dispensed_at = models.DateTimeField(_("Dispensed At"), null=True, blank=True)
    dispensing_notes = models.TextField(_("Dispensing Notes"), blank=True, null=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Administration (after nurse receives)
    is_administered = models.BooleanField(_("Administered"), default=False)
    administered_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_emergency_medicines'
    )
    administered_at = models.DateTimeField(_("Administered At"), null=True, blank=True)
    administration_notes = models.TextField(_("Administration Notes"), blank=True, null=True)
    
    # Billing
    emergency_charge = models.ForeignKey(
        'EmergencyCharge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medicine_request'
    )
    
    class Meta:
        verbose_name = _("Emergency Medicine Request")
        verbose_name_plural = _("Emergency Medicine Requests")
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['emergency_visit', '-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} - {self.get_status_display()}"


class EmergencyMedicationLog(models.Model):
    """
    Audit log for all emergency medications
    Tracks the complete lifecycle: request → approval → administration
    """
    medicine_request = models.ForeignKey(
        'EmergencyMedicineRequest',
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    action = models.CharField(
        _("Action"),
        max_length=50,
        choices=[
            ('REQUESTED', 'Requested'),
            ('APPROVED', 'Approved & Dispensed'),
            ('REJECTED', 'Rejected'),
            ('ADMINISTERED', 'Administered'),
            ('CANCELLED', 'Cancelled'),
        ]
    )
    
    performed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    stock_before = models.DecimalField(
        _("Stock Before"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    stock_after = models.DecimalField(
        _("Stock After"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Emergency Medication Log")
        verbose_name_plural = _("Emergency Medication Logs")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.medicine_request.medicine.name}"
# ============================================================
# ADD EMERGENCY INSURANCE CLAIM MODEL
# ============================================================
# Add this to your models.py file

class EmergencyInsuranceClaim(models.Model):
    """Insurance claims for emergency visits"""
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved by Claims Officer'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Payment Confirmed by Cashier'),
    )
    
    claim_number = models.CharField(max_length=50, unique=True, editable=False)
    
    emergency_visit = models.OneToOneField(
        'EmergencyVisit',
        on_delete=models.CASCADE,
        related_name='insurance_claim'
    )
    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='emergency_claims'
    )
    
    member_number = models.CharField(max_length=100)
    member_name = models.CharField(max_length=200)
    
    total_charges = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    approved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    patient_copay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    charges_breakdown = models.JSONField(default=dict)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    claims_officer_approved = models.BooleanField(default=False)
    claims_officer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_emergency_claims'
    )
    claims_approved_at = models.DateTimeField(null=True, blank=True)
    claims_officer_comments = models.TextField(blank=True, null=True)
    
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_emergency_claims'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    payment_confirmed = models.BooleanField(default=False)
    payment_confirmed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_emergency_payments'
    )
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    payment_audit_log = models.ForeignKey(
        'PaymentAuditLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_insurance_claims'
    )
    
    submitted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_emergency_claims'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Emergency Insurance Claim"
        verbose_name_plural = "Emergency Insurance Claims"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = EmergencyInsuranceClaim.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.claim_number = f"EMER-CLM-{date_str}-{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.claim_number} - {self.emergency_visit.visit.visit_number}"
    
    def approve_by_claims_officer(self, claims_officer, approved_amount, patient_copay=0, comments=None):
        self.claims_officer_approved = True
        self.claims_officer = claims_officer
        self.claims_approved_at = timezone.now()
        self.claims_officer_comments = comments
        self.approved_amount = approved_amount
        self.patient_copay = patient_copay
        self.status = 'APPROVED'
        self.save()
    
    def reject_by_claims_officer(self, claims_officer, reason):
        self.status = 'REJECTED'
        self.rejected_by = claims_officer
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def confirm_payment(self, cashier, audit_log):
        if not self.claims_officer_approved:
            raise ValueError("Cannot confirm payment before claims officer approval")
        
        self.payment_confirmed = True
        self.payment_confirmed_by = cashier
        self.payment_confirmed_at = timezone.now()
        self.payment_audit_log = audit_log
        self.status = 'PAID'
        self.save()
        
class MaternityVisit(models.Model):
    """
    Maternity/Labor & Delivery specific details
    """
    VISIT_PURPOSE_CHOICES = (
        ('LABOR', 'Labor & Delivery'),
        ('ANTENATAL', 'Antenatal Check-up'),
        ('POSTNATAL', 'Postnatal Check-up'),
        ('EMERGENCY', 'Obstetric Emergency'),
        ('ABORTION', 'Abortion/Miscarriage'),
    )
    
    LABOR_STAGE_CHOICES = (
        ('EARLY', 'Early Labor (Latent Phase)'),
        ('ACTIVE', 'Active Labor'),
        ('TRANSITION', 'Transition'),
        ('PUSHING', 'Pushing Stage'),
        ('DELIVERY', 'Delivery Imminent'),
        ('DELIVERED', 'Already Delivered'),
    )
    
    visit = models.OneToOneField(
        'PatientVisit',
        on_delete=models.CASCADE,
        related_name='maternity_details'
    )
    
    # Visit Purpose
    visit_purpose = models.CharField(
        _("Visit Purpose"),
        max_length=20,
        choices=VISIT_PURPOSE_CHOICES,
        default='LABOR'
    )
    
    # Pregnancy Details
    gravida = models.IntegerField(
        _("Gravida (G)"),
        help_text="Total number of pregnancies"
    )
    para = models.IntegerField(
        _("Para (P)"),
        help_text="Number of deliveries after 28 weeks"
    )
    abortion = models.IntegerField(
        _("Abortion (A)"),
        default=0,
        help_text="Number of abortions/miscarriages"
    )
    gestational_age_weeks = models.IntegerField(
        _("Gestational Age (weeks)"),
        blank=True,
        null=True
    )
    expected_delivery_date = models.DateField(
        _("Expected Delivery Date (EDD)"),
        blank=True,
        null=True
    )
    
    # Labor Details (if in labor)
    is_in_labor = models.BooleanField(_("Currently In Labor"), default=False)
    labor_stage = models.CharField(
        _("Labor Stage"),
        max_length=20,
        choices=LABOR_STAGE_CHOICES,
        blank=True,
        null=True
    )
    contractions_frequency = models.CharField(
        _("Contractions Frequency"),
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 'Every 5 minutes', 'Every 3 minutes'"
    )
    membranes_ruptured = models.BooleanField(_("Membranes Ruptured"), default=False)
    time_of_rupture = models.DateTimeField(_("Time of Rupture"), blank=True, null=True)
    
    # Clinical Status
    cervical_dilation = models.IntegerField(
        _("Cervical Dilation (cm)"),
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        blank=True,
        null=True
    )
    fetal_heart_rate = models.IntegerField(
        _("Fetal Heart Rate (bpm)"),
        blank=True,
        null=True
    )
    maternal_blood_pressure = models.CharField(
        _("Maternal BP"),
        max_length=20,
        blank=True,
        null=True,
        help_text="e.g., 120/80"
    )
    
    # High Risk Factors
    is_high_risk = models.BooleanField(_("High Risk Pregnancy"), default=False)
    risk_factors = models.TextField(
        _("Risk Factors"),
        blank=True,
        null=True,
        help_text="e.g., Pre-eclampsia, Diabetes, Previous C-Section"
    )
    
    # Emergency Indicators
    needs_urgent_delivery = models.BooleanField(_("Needs Urgent Delivery"), default=False)
    needs_csection = models.BooleanField(_("Needs C-Section"), default=False)
    fetal_distress = models.BooleanField(_("Fetal Distress"), default=False)
    maternal_distress = models.BooleanField(_("Maternal Distress"), default=False)
    
    # Automatic Bed Assignment in Maternity Ward
    auto_assigned_bed = models.ForeignKey(
        'Bed',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maternity_assignments'
    )
    
    # Automatic Admission
    auto_admission = models.ForeignKey(
        'InpatientAdmission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maternity_visits'
    )
    
    initial_assessment = models.TextField(_("Initial Assessment"))
    special_instructions = models.TextField(
        _("Special Instructions"),
        blank=True,
        null=True
    )
    
    assessed_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        related_name='maternity_assessments'
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Maternity Visit")
        verbose_name_plural = _("Maternity Visits")
    
    def __str__(self):
        return f"Maternity - {self.visit.visit_number} - G{self.gravida}P{self.para}"


class MCHVisit(models.Model):
    """
    Mother & Child Health (Baby Clinic) visits
    """
    VISIT_TYPE_CHOICES = (
        ('IMMUNIZATION', 'Immunization'),
        ('GROWTH_MONITORING', 'Growth Monitoring'),
        ('SICK_CHILD', 'Sick Child'),
        ('NUTRITION', 'Nutrition Assessment'),
        ('DEVELOPMENTAL', 'Developmental Assessment'),
        ('FOLLOW_UP', 'Follow-up Visit'),
    )
    
    URGENCY_LEVEL_CHOICES = (
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent - Needs Quick Attention'),
        ('EMERGENCY', 'Emergency - Immediate Care'),
    )
    
    NUTRITIONAL_STATUS_CHOICES = (
        ('NORMAL', 'Normal'),
        ('MILD_MAL', 'Mild Malnutrition'),
        ('MODERATE_MAL', 'Moderate Malnutrition'),
        ('SEVERE_MAL', 'Severe Malnutrition'),
        ('OBESE', 'Obese'),
    )
    
    visit = models.OneToOneField(
        'PatientVisit',
        on_delete=models.CASCADE,
        related_name='mch_details'
    )
    
    # Visit Details
    visit_type = models.CharField(
        _("Visit Type"),
        max_length=20,
        choices=VISIT_TYPE_CHOICES
    )
    urgency_level = models.CharField(
        _("Urgency Level"),
        max_length=20,
        choices=URGENCY_LEVEL_CHOICES,
        default='ROUTINE'
    )
    
    # Child Details
    child_age_months = models.IntegerField(
        _("Child Age (months)"),
        validators=[MinValueValidator(0), MaxValueValidator(72)]
    )
    weight_kg = models.DecimalField(
        _("Weight (kg)"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    height_cm = models.DecimalField(
        _("Height (cm)"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    head_circumference = models.DecimalField(
        _("Head Circumference (cm)"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    temperature = models.DecimalField(
        _("Temperature (°C)"),
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True
    )
    
    # Immunization Details
    immunization_due = models.BooleanField(_("Immunization Due"), default=False)
    vaccines_to_administer = models.TextField(
        _("Vaccines to Administer"),
        blank=True,
        null=True,
        help_text="List vaccines needed"
    )
    
    # Nutritional Assessment
    nutritional_status = models.CharField(
        _("Nutritional Status"),
        max_length=20,
        choices=NUTRITIONAL_STATUS_CHOICES,
        blank=True,
        null=True
    )
    is_breastfeeding = models.BooleanField(_("Breastfeeding"), default=False)
    feeding_concerns = models.TextField(
        _("Feeding Concerns"),
        blank=True,
        null=True
    )
    
    # Developmental Milestones
    developmental_concerns = models.TextField(
        _("Developmental Concerns"),
        blank=True,
        null=True
    )
    
    # Danger Signs
    has_danger_signs = models.BooleanField(_("Has Danger Signs"), default=False)
    danger_signs = models.TextField(
        _("Danger Signs"),
        blank=True,
        null=True,
        help_text="e.g., Unable to feed, Convulsions, Lethargy, Severe malnutrition"
    )
    
    # Consultation Needed
    needs_doctor_consultation = models.BooleanField(
        _("Needs Doctor Consultation"),
        default=False
    )
    consultation_reason = models.TextField(
        _("Reason for Consultation"),
        blank=True,
        null=True
    )
    
    # Auto-payment flag for consultation
    consultation_fee_waived = models.BooleanField(
        _("Consultation Fee Waived"),
        default=False,
        help_text="True if emergency/danger signs present"
    )
    
    # Mother's Details
    mothers_name = models.CharField(
        _("Mother's Name"),
        max_length=200
    )
    mothers_phone = models.CharField(
        _("Mother's Phone"),
        max_length=15
    )
    
    assessment_notes = models.TextField(_("Assessment Notes"))
    action_taken = models.TextField(
        _("Immediate Action Taken"),
        blank=True,
        null=True
    )
    
    assessed_by = models.ForeignKey(
        'Nurse',
        on_delete=models.SET_NULL,
        null=True,
        related_name='mch_assessments'
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("MCH Visit")
        verbose_name_plural = _("MCH Visits")
    
    def __str__(self):
        return f"MCH - {self.visit.visit_number} - {self.child_age_months} months"
    
    def auto_determine_consultation_need(self):
        """
        Automatically determine if doctor consultation is needed
        """
        # Emergency conditions that need immediate doctor attention
        if self.urgency_level == 'EMERGENCY':
            self.needs_doctor_consultation = True
            self.consultation_fee_waived = True
        elif self.has_danger_signs:
            self.needs_doctor_consultation = True
            self.consultation_fee_waived = True
        elif self.nutritional_status in ['MODERATE_MAL', 'SEVERE_MAL']:
            self.needs_doctor_consultation = True
        elif self.temperature and float(self.temperature) >= 38.5:
            self.needs_doctor_consultation = True
        
        self.save()


class VisitBedAssignment(models.Model):
    """
    Track automatic bed assignments for emergency/maternity visits
    """
    visit = models.ForeignKey(
        'PatientVisit',
        on_delete=models.CASCADE,
        related_name='bed_assignments'
    )
    bed = models.ForeignKey(
        'Bed',
        on_delete=models.CASCADE,
        related_name='visit_assignments'
    )
    
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)
    assigned_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='bed_assignments_made'
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    released_at = models.DateTimeField(_("Released At"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Visit Bed Assignment")
        verbose_name_plural = _("Visit Bed Assignments")
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.visit.visit_number} - {self.bed.bed_number}"
    
    
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
import secrets
from datetime import timedelta


class HospitalWiFiNetwork(models.Model):
    """
    Stores approved hospital WiFi networks for attendance verification
    """
    network_name = models.CharField(
        _("Network SSID"),
        max_length=200,
        help_text="WiFi network name"
    )
    bssid = models.CharField(
        _("BSSID/MAC Address"),
        max_length=17,
        blank=True,
        null=True,
        help_text="Router MAC address for additional verification"
    )
    location = models.CharField(
        _("Location"),
        max_length=200,
        help_text="Physical location of this network"
    )
    ip_range = models.CharField(
        _("IP Range"),
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 192.168.1.0/24"
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Hospital WiFi Network")
        verbose_name_plural = _("Hospital WiFi Networks")
    
    def __str__(self):
        return f"{self.network_name} - {self.location}"


class AttendanceQRCode(models.Model):
    """
    QR codes generated by HR for attendance tracking
    Codes are time-limited and type-specific (check-in/check-out)
    """
    QR_TYPE_CHOICES = (
        ('CHECK_IN', 'Check In'),
        ('CHECK_OUT', 'Check Out'),
    )
    
    qr_code = models.CharField(
        _("QR Code"),
        max_length=100,
        unique=True,
        editable=False
    )
    qr_type = models.CharField(
        _("QR Type"),
        max_length=10,
        choices=QR_TYPE_CHOICES
    )
    
    # Time validity
    valid_from = models.DateTimeField(_("Valid From"))
    valid_until = models.DateTimeField(_("Valid Until"))
    
    # Date this QR is for
    attendance_date = models.DateField(_("Attendance Date"))
    
    # Additional metadata
    location = models.CharField(
        _("Location"),
        max_length=200,
        help_text="Where this QR code should be scanned"
    )
    
    # Tracking
    generated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_qr_codes',
        limit_choices_to={'user_type': 'HR'}
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    scan_count = models.IntegerField(_("Scan Count"), default=0)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Attendance QR Code")
        verbose_name_plural = _("Attendance QR Codes")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['qr_code']),
            models.Index(fields=['attendance_date', 'qr_type']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.qr_code:
            # Generate unique QR code
            self.qr_code = f"ATT-{secrets.token_urlsafe(32)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_qr_type_display()} - {self.attendance_date}"
    
    def is_valid(self):
        """Check if QR code is currently valid"""
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_until
        )


class Attendance(models.Model):
    """
    Daily attendance records for staff
    """
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Leave'),
        ('HOLIDAY', 'Holiday'),
    )
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    
    date = models.DateField(_("Date"))
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=STATUS_CHOICES,
        default='ABSENT'
    )
    
    # Check-in details
    check_in_time = models.DateTimeField(_("Check In Time"), blank=True, null=True)
    check_in_qr_code = models.ForeignKey(
        AttendanceQRCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_in_scans'
    )
    check_in_location = models.CharField(
        _("Check In Location"),
        max_length=200,
        blank=True,
        null=True
    )
    check_in_ip = models.GenericIPAddressField(
        _("Check In IP"),
        blank=True,
        null=True
    )
    check_in_wifi_network = models.ForeignKey(
        HospitalWiFiNetwork,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_in_records'
    )
    
    # Check-out details
    check_out_time = models.DateTimeField(_("Check Out Time"), blank=True, null=True)
    check_out_qr_code = models.ForeignKey(
        AttendanceQRCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_out_scans'
    )
    check_out_location = models.CharField(
        _("Check Out Location"),
        max_length=200,
        blank=True,
        null=True
    )
    check_out_ip = models.GenericIPAddressField(
        _("Check Out IP"),
        blank=True,
        null=True
    )
    check_out_wifi_network = models.ForeignKey(
        HospitalWiFiNetwork,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='check_out_records'
    )
    
    # Working hours
    total_hours = models.DecimalField(
        _("Total Hours"),
        max_digits=5,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )
    
    # Manual attendance (for corrections)
    is_manual = models.BooleanField(_("Manual Entry"), default=False)
    manual_reason = models.TextField(_("Manual Entry Reason"), blank=True, null=True)
    manual_approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_manual_attendance'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendance Records")
        ordering = ['-date', 'user']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.date} ({self.get_status_display()})"
    
    def calculate_hours(self):
        """Calculate total working hours"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            self.total_hours = round(delta.total_seconds() / 3600, 2)
            self.save(update_fields=['total_hours'])
    
    @property
    def is_late(self):
        """Check if check-in was late (after 8:30 AM)"""
        if self.check_in_time:
            late_threshold = self.check_in_time.replace(hour=8, minute=30, second=0)
            return self.check_in_time > late_threshold
        return False


class LeaveType(models.Model):
    """
    Types of leave available
    """
    name = models.CharField(_("Leave Type"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    
    # Leave allowance
    days_allowed_per_year = models.IntegerField(
        _("Days Allowed Per Year"),
        default=0,
        help_text="0 means unlimited or case-by-case"
    )
    
    # Rules
    requires_attachment = models.BooleanField(
        _("Requires Attachment"),
        default=False,
        help_text="e.g., medical certificate for sick leave"
    )
    is_paid = models.BooleanField(_("Paid Leave"), default=True)
    
    # Approval requirements
    requires_hr_approval = models.BooleanField(_("Requires HR Approval"), default=True)
    requires_supervisor_approval = models.BooleanField(
        _("Requires Supervisor Approval"),
        default=True
    )
    
    # Advance notice
    minimum_notice_days = models.IntegerField(
        _("Minimum Notice Days"),
        default=0,
        help_text="Days in advance required for application"
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LeaveApplication(models.Model):
    """
    Staff leave applications
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUPERVISOR_APPROVED', 'Supervisor Approved'),
        ('HR_APPROVED', 'HR Approved'),
        ('APPROVED', 'Fully Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )
    
    # Application identification
    application_number = models.CharField(
        _("Application Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='leave_applications'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='applications'
    )
    
    # Leave period
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    total_days = models.IntegerField(_("Total Days"), default=0)
    
    # Application details
    reason = models.TextField(_("Reason"))
    emergency_contact = models.CharField(
        _("Emergency Contact During Leave"),
        max_length=15,
        blank=True,
        null=True
    )
    
    # Attachment (e.g., medical certificate)
    attachment = models.FileField(
        _("Attachment"),
        upload_to='leave_applications/',
        blank=True,
        null=True
    )
    
    # Status and approvals
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Supervisor approval
    supervisor_approved = models.BooleanField(_("Supervisor Approved"), default=False)
    supervisor_approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_leave_approvals'
    )
    supervisor_approved_at = models.DateTimeField(
        _("Supervisor Approved At"),
        blank=True,
        null=True
    )
    supervisor_comments = models.TextField(
        _("Supervisor Comments"),
        blank=True,
        null=True
    )
    
    # HR approval
    hr_approved = models.BooleanField(_("HR Approved"), default=False)
    hr_approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_leave_approvals',
        limit_choices_to={'user_type': 'HR'}
    )
    hr_approved_at = models.DateTimeField(_("HR Approved At"), blank=True, null=True)
    hr_comments = models.TextField(_("HR Comments"), blank=True, null=True)
    
    # Rejection
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_leave_applications'
    )
    rejected_at = models.DateTimeField(_("Rejected At"), blank=True, null=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Cancellation
    cancelled_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_leave_applications'
    )
    cancelled_at = models.DateTimeField(_("Cancelled At"), blank=True, null=True)
    cancellation_reason = models.TextField(_("Cancellation Reason"), blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Leave Application")
        verbose_name_plural = _("Leave Applications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['application_number']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate application number
        if not self.application_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = LeaveApplication.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.application_number = f"LEAVE-{date_str}-{count:04d}"
        
        # Calculate total days
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.application_number} - {self.user.get_full_name()} ({self.leave_type.name})"
    
    @property
    def is_ongoing(self):
        """Check if leave is currently ongoing"""
        today = timezone.now().date()
        return (
            self.status == 'APPROVED' and
            self.start_date <= today <= self.end_date
        )
    
    def mark_attendance_on_leave(self):
        """Mark attendance as 'ON_LEAVE' for approved leave dates"""
        if self.status == 'APPROVED':
            current_date = self.start_date
            while current_date <= self.end_date:
                Attendance.objects.update_or_create(
                    user=self.user,
                    date=current_date,
                    defaults={
                        'status': 'ON_LEAVE',
                        'notes': f"On {self.leave_type.name} - {self.application_number}"
                    }
                )
                current_date += timedelta(days=1)


class LeaveBalance(models.Model):
    """
    Track leave balances for each user and leave type
    """
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances'
    )
    year = models.IntegerField(_("Year"))
    
    total_allocated = models.IntegerField(
        _("Total Allocated"),
        default=0,
        help_text="Total days allocated for this year"
    )
    days_used = models.IntegerField(_("Days Used"), default=0)
    days_remaining = models.IntegerField(_("Days Remaining"), default=0)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")
        unique_together = ['user', 'leave_type', 'year']
        ordering = ['-year', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.leave_type.name} ({self.year})"
    
    def update_balance(self):
        """Recalculate days used and remaining"""
        approved_leaves = LeaveApplication.objects.filter(
            user=self.user,
            leave_type=self.leave_type,
            status='APPROVED',
            start_date__year=self.year
        )
        
        self.days_used = sum(leave.total_days for leave in approved_leaves)
        self.days_remaining = self.total_allocated - self.days_used
        self.save()


class AttendanceReport(models.Model):
    """
    Pre-generated attendance reports for departments/periods
    """
    REPORT_TYPE_CHOICES = (
        ('DAILY', 'Daily Report'),
        ('WEEKLY', 'Weekly Report'),
        ('MONTHLY', 'Monthly Report'),
        ('CUSTOM', 'Custom Period'),
    )
    
    report_type = models.CharField(
        _("Report Type"),
        max_length=10,
        choices=REPORT_TYPE_CHOICES
    )
    
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    
    department = models.CharField(
        _("Department"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # Statistics
    total_staff = models.IntegerField(_("Total Staff"), default=0)
    total_present = models.IntegerField(_("Total Present"), default=0)
    total_absent = models.IntegerField(_("Total Absent"), default=0)
    total_on_leave = models.IntegerField(_("Total On Leave"), default=0)
    attendance_rate = models.DecimalField(
        _("Attendance Rate (%)"),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Report file
    report_file = models.FileField(
        _("Report File"),
        upload_to='attendance_reports/',
        blank=True,
        null=True
    )
    
    generated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_attendance_reports'
    )
    generated_at = models.DateTimeField(_("Generated At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Attendance Report")
        verbose_name_plural = _("Attendance Reports")
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} to {self.end_date}"
    
    
# Add these models to your existing models.py file

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class ConsultationInsuranceClaim(models.Model):
    """
    Tracks insurance claims for consultation fees
    Must be approved by Claims Officer before cashier can confirm payment
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved by Claims Officer'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Payment Confirmed by Cashier'),
    )
    
    # Claim identification
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Links
    patient_visit = models.ForeignKey(
        'PatientVisit',
        on_delete=models.CASCADE,
        related_name='insurance_claims'
    )
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='consultation_insurance_claims'
    )
    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='consultation_claims'
    )
    
    # Claim details
    consultation_fee = models.DecimalField(
        _("Consultation Fee (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    service_name = models.CharField(
        _("Service Name"),
        max_length=200,
        help_text="Name of the specialist service"
    )
    
    # Insurance details
    member_number = models.CharField(
        _("Member Number"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Insurance member/policy number"
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Claims Officer Approval
    claims_officer_approved = models.BooleanField(
        _("Claims Officer Approved"),
        default=False
    )
    claims_officer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_consultation_claims',
        limit_choices_to={'user_type': 'INSURANCE'}
    )
    claims_officer_approved_at = models.DateTimeField(
        _("Approved At"),
        blank=True,
        null=True
    )
    claims_officer_comments = models.TextField(
        _("Claims Officer Comments"),
        blank=True,
        null=True
    )
    
    # Rejection
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_consultation_claims'
    )
    rejected_at = models.DateTimeField(_("Rejected At"), blank=True, null=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Cashier Payment Confirmation
    payment_confirmed = models.BooleanField(_("Payment Confirmed"), default=False)
    payment_confirmed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_consultation_payments',
        limit_choices_to={'user_type': 'CASHIER'}
    )
    payment_confirmed_at = models.DateTimeField(
        _("Payment Confirmed At"),
        blank=True,
        null=True
    )
    
    # Payment audit log reference
    payment_audit_log = models.ForeignKey(
        'PaymentAuditLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultation_insurance_claims'
    )
    
    # Submitted by
    submitted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_consultation_claims'
    )
    
    insurance_payment_received = models.BooleanField(
        default=False,
        verbose_name="Insurance Payment Received"
    ) # This are filled later when you finnaly get paid by the insurance company
    insurance_payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Insurance Payment Date"
    )
    insurance_payment_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Insurance Payment Reference"
    )
    insurance_payment_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Insurance Payment Notes"
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Consultation Insurance Claim")
        verbose_name_plural = _("Consultation Insurance Claims")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['patient_visit']),
            models.Index(fields=['insurance_provider', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = ConsultationInsuranceClaim.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.claim_number = f"CONS-CLM-{date_str}-{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.claim_number} - {self.patient.first_name} {self.patient.last_name} ({self.status})"
    
    def approve_by_claims_officer(self, claims_officer, comments=None):
        """Approve claim by claims officer"""
        self.claims_officer_approved = True
        self.claims_officer = claims_officer
        self.claims_officer_approved_at = timezone.now()
        self.claims_officer_comments = comments
        self.status = 'APPROVED'
        self.save()
    
    def reject_by_claims_officer(self, claims_officer, reason):
        """Reject claim"""
        self.status = 'REJECTED'
        self.rejected_by = claims_officer
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def confirm_payment(self, cashier, payment_audit_log):
        """Confirm payment by cashier after claims officer approval"""
        if not self.claims_officer_approved:
            raise ValueError("Cannot confirm payment before claims officer approval")
        
        self.payment_confirmed = True
        self.payment_confirmed_by = cashier
        self.payment_confirmed_at = timezone.now()
        self.payment_audit_log = payment_audit_log
        self.status = 'PAID'
        self.save()
        
        
# Add to models.py

class PharmacyInsuranceClaim(models.Model):
    """
    Insurance claims for pharmacy/medicine sales
    Must be approved by Claims Officer before cashier can process payment
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved by Claims Officer'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Payment Confirmed by Cashier'),
    )
    
    CLAIM_TYPE_CHOICES = (
        ('PRESCRIPTION', 'Prescription'),
        ('OTC', 'Over-The-Counter'),
    )
    
    # Claim identification
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    claim_type = models.CharField(
        _("Claim Type"),
        max_length=20,
        choices=CLAIM_TYPE_CHOICES
    )
    
    # Links
    consultation = models.ForeignKey(
        'Consultation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pharmacy_insurance_claims'
    )
    otc_sale = models.ForeignKey(
        'OverTheCounterSale',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='insurance_claims'
    )
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='pharmacy_insurance_claims'
    )
    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='pharmacy_claims'
    )
    
    # Member details
    member_number = models.CharField(
        _("Member/Policy Number"),
        max_length=100
    )
    member_name = models.CharField(
        _("Member Name"),
        max_length=200
    )
    
    # Financial breakdown
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    insurance_covered = models.DecimalField(
        _("Insurance Covered (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    patient_copay = models.DecimalField(
        _("Patient Co-pay (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Item details (stored as JSON)
    items_breakdown = models.JSONField(
        _("Items Breakdown"),
        help_text="Detailed list of medicines and prices"
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Claims Officer Approval
    claims_officer_approved = models.BooleanField(
        _("Claims Officer Approved"),
        default=False
    )
    claims_officer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_pharmacy_claims',
        limit_choices_to={'user_type': 'INSURANCE'}
    )
    claims_approved_at = models.DateTimeField(
        _("Approved At"),
        blank=True,
        null=True
    )
    claims_officer_comments = models.TextField(
        _("Claims Officer Comments"),
        blank=True,
        null=True
    )
    
    # Rejection
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_pharmacy_claims'
    )
    rejected_at = models.DateTimeField(_("Rejected At"), blank=True, null=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Cashier Payment Confirmation
    payment_confirmed = models.BooleanField(_("Payment Confirmed"), default=False)
    payment_confirmed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_pharmacy_payments',
        limit_choices_to={'user_type': 'CASHIER'}
    )
    payment_confirmed_at = models.DateTimeField(
        _("Payment Confirmed At"),
        blank=True,
        null=True
    )
    
    # Payment details
    payment_method = models.CharField(
        _("Payment Method"),
        max_length=20,
        blank=True,
        null=True
    )
    mpesa_code = models.CharField(
        _("M-Pesa Code"),
        max_length=50,
        blank=True,
        null=True
    )
    mpesa_phone = models.CharField(
        _("M-Pesa Phone"),
        max_length=15,
        blank=True,
        null=True
    )
    
    # Payment audit log reference
    payment_audit_log = models.ForeignKey(
        'PaymentAuditLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pharmacy_insurance_claims'
    )
    
    # Submitted by
    submitted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_pharmacy_claims'
    )
    
    insurance_payment_received = models.BooleanField(
        default=False,
        verbose_name="Insurance Payment Received"
    )
    insurance_payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Insurance Payment Date"
    )
    insurance_payment_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Insurance Payment Reference"
    )
    insurance_payment_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Insurance Payment Notes"
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Pharmacy Insurance Claim")
        verbose_name_plural = _("Pharmacy Insurance Claims")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['insurance_provider', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = PharmacyInsuranceClaim.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.claim_number = f"PHRM-CLM-{date_str}-{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.claim_number} - {self.patient.first_name} {self.patient.last_name} ({self.status})"
    
    def approve_by_claims_officer(self, claims_officer, comments=None):
        """Approve claim by claims officer"""
        self.claims_officer_approved = True
        self.claims_officer = claims_officer
        self.claims_approved_at = timezone.now()
        self.claims_officer_comments = comments
        self.status = 'APPROVED'
        self.save()
    
    def reject_by_claims_officer(self, claims_officer, reason):
        """Reject claim"""
        self.status = 'REJECTED'
        self.rejected_by = claims_officer
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        
# models.py - Add this model to your existing models

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class InpatientInsuranceClaim(models.Model):
    """
    Insurance claims for inpatient admissions
    Must be approved by Claims Officer before cashier can process payment
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved by Claims Officer'),
        ('PARTIALLY_APPROVED', 'Partially Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Payment Confirmed by Cashier'),
    )
    
    # Claim Identification
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    # Links
    admission = models.OneToOneField(
        'InpatientAdmission',
        on_delete=models.CASCADE,
        related_name='insurance_claim'
    )
    insurance_provider = models.ForeignKey(
        'InsuranceProvider',
        on_delete=models.PROTECT,
        related_name='inpatient_claims'
    )
    
    # Member details
    member_number = models.CharField(
        _("Member/Policy Number"),
        max_length=100
    )
    member_name = models.CharField(
        _("Member Name"),
        max_length=200
    )
    
    # Financial breakdown
    total_charges = models.DecimalField(
        _("Total Charges (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Charge breakdown (stored as JSON)
    charges_breakdown = models.JSONField(
        _("Charges Breakdown"),
        help_text="Detailed breakdown by category",
        default=dict
    )
    
    # Approval amounts
    approved_amount = models.DecimalField(
        _("Approved Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    patient_copay = models.DecimalField(
        _("Patient Co-pay (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    # Claims Officer Approval
    claims_officer_approved = models.BooleanField(
        _("Claims Officer Approved"),
        default=False
    )
    claims_officer = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_inpatient_claims',
        limit_choices_to={'user_type': 'INSURANCE'}
    )
    claims_approved_at = models.DateTimeField(
        _("Approved At"),
        blank=True,
        null=True
    )
    claims_officer_comments = models.TextField(
        _("Claims Officer Comments"),
        blank=True,
        null=True
    )
    
    # Rejection
    rejected_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_inpatient_claims'
    )
    rejected_at = models.DateTimeField(_("Rejected At"), blank=True, null=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Cashier Payment Confirmation
    payment_confirmed = models.BooleanField(_("Payment Confirmed"), default=False)
    payment_confirmed_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_inpatient_payments',
        limit_choices_to={'user_type': 'CASHIER'}
    )
    payment_confirmed_at = models.DateTimeField(
        _("Payment Confirmed At"),
        blank=True,
        null=True
    )
    
    # Payment audit log reference
    payment_audit_log = models.ForeignKey(
        'PaymentAuditLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_insurance_claims'
    )
    
    insurance_payment_received = models.BooleanField(
        default=False,
        verbose_name="Insurance Payment Received"
    )
    insurance_payment_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Insurance Payment Date"
    )
    insurance_payment_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Insurance Payment Reference"
    )
    insurance_payment_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Insurance Payment Notes"
    )
    
    # Submitted by
    submitted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_inpatient_claims'
    )
    submitted_at = models.DateTimeField(_("Submitted At"), blank=True, null=True)
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Inpatient Insurance Claim")
        verbose_name_plural = _("Inpatient Insurance Claims")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['claim_number']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['admission']),
            models.Index(fields=['insurance_provider', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = InpatientInsuranceClaim.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.claim_number = f"IPD-CLM-{date_str}-{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.claim_number} - {self.admission.patient.first_name} {self.admission.patient.last_name} ({self.status})"
    
    def approve_by_claims_officer(self, claims_officer, approved_amount, patient_copay=0, comments=None):
        """Approve claim by claims officer"""
        self.claims_officer_approved = True
        self.claims_officer = claims_officer
        self.claims_approved_at = timezone.now()
        self.claims_officer_comments = comments
        self.approved_amount = approved_amount
        self.patient_copay = patient_copay
        self.status = 'APPROVED'
        self.save()
    
    def reject_by_claims_officer(self, claims_officer, reason):
        """Reject claim"""
        self.status = 'REJECTED'
        self.rejected_by = claims_officer
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def confirm_payment(self, cashier, payment_audit_log):
        """Confirm payment by cashier after claims officer approval"""
        if not self.claims_officer_approved:
            raise ValueError("Cannot confirm payment before claims officer approval")
        
        self.payment_confirmed = True
        self.payment_confirmed_by = cashier
        self.payment_confirmed_at = timezone.now()
        self.payment_audit_log = payment_audit_log
        self.status = 'PAID'
        self.save()
    
    def calculate_totals(self):
        """Calculate total charges from admission"""
        from decimal import Decimal
        
        # Get all charges for this admission
        total = self.admission.daily_charges.aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        self.total_charges = total
        self.save()
        
        return total
    
# eTIMS models 

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import uuid


class eTIMSConfiguration(models.Model):
    """
    eTIMS system configuration - Single instance model
    Stores credentials and settings for KRA eTIMS integration
    """
    # Hospital/Business Details
    tin_number = models.CharField(
        _("TIN Number"),
        max_length=20,
        unique=True,
        help_text="KRA Tax Identification Number"
    )
    business_name = models.CharField(_("Business Name"), max_length=200)
    branch_name = models.CharField(_("Branch Name"), max_length=200)
    
    # eTIMS Device Details
    device_serial_number = models.CharField(
        _("Device Serial Number"),
        max_length=100,
        blank=True,
        null=True
    )
    device_model = models.CharField(
        _("Device Model"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # API Configuration (will be used when APIs are available)
    api_base_url = models.URLField(
        _("API Base URL"),
        blank=True,
        null=True,
        help_text="KRA eTIMS API endpoint"
    )
    api_key = models.CharField(
        _("API Key"),
        max_length=500,
        blank=True,
        null=True
    )
    api_secret = models.CharField(
        _("API Secret"),
        max_length=500,
        blank=True,
        null=True
    )
    
    # Settings
    is_active = models.BooleanField(_("Active"), default=False)
    test_mode = models.BooleanField(
        _("Test Mode"),
        default=True,
        help_text="Enable for testing before going live"
    )
    auto_submit_invoices = models.BooleanField(
        _("Auto Submit Invoices"),
        default=False,
        help_text="Automatically submit invoices to eTIMS"
    )
    
    # Last sync information
    last_sync_date = models.DateTimeField(
        _("Last Sync Date"),
        blank=True,
        null=True
    )
    last_sync_status = models.CharField(
        _("Last Sync Status"),
        max_length=200,
        blank=True,
        null=True
    )
    
    # Branch/Location Management
    county = models.CharField(_("County"), max_length=100, blank=True)
    sub_county = models.CharField(_("Sub-County"), max_length=100, blank=True)

    # License & Registration
    business_license_number = models.CharField(
        _("Business License Number"), 
        max_length=100, 
        blank=True
    )
    pharmacy_board_license = models.CharField(
        _("Pharmacy Board License"), 
        max_length=100, 
        blank=True
    )

    # eTIMS Device Integration
    device_type = models.CharField(
        _("Device Type"),
        max_length=50,
        choices=(
            ('PAYPOINT', 'eTIMS Paypoint'),
            ('MULTI_PAYPOINT', 'eTIMS Multi Paypoint'),
            ('LITE_VAT', 'eTIMS Lite (VAT)'),
            ('LITE_NON_VAT', 'eTIMS Lite (Non-VAT)'),
        ),
        blank=True
    )

    # Privacy & Compliance
    data_anonymization_enabled = models.BooleanField(
        _("Enable Data Anonymization"),
        default=True,
        help_text="Anonymize patient data in eTIMS submissions for privacy compliance"
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("eTIMS Configuration")
        verbose_name_plural = _("eTIMS Configuration")
    
    def __str__(self):
        return f"eTIMS Config - {self.business_name} (TIN: {self.tin_number})"
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration exists
        if not self.pk and eTIMSConfiguration.objects.exists():
            raise ValueError("Only one eTIMS configuration is allowed. Please update the existing one.")
        return super().save(*args, **kwargs)


class eTIMSInvoice(models.Model):
    """
    Electronic Tax Invoice - Main invoice record for KRA
    Links to various payment types in the hospital
    """
    INVOICE_TYPE_CHOICES = (
        ('CONSULTATION', 'Consultation Payment'),
        ('PHARMACY', 'Pharmacy Sale'),
        ('LABORATORY', 'Laboratory Tests'),
        ('INPATIENT', 'Inpatient Billing'),
        ('OTHER', 'Other Services'),
    )
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Submission'),
        ('SUBMITTED', 'Submitted to KRA'),
        ('APPROVED', 'Approved by KRA'),
        ('REJECTED', 'Rejected by KRA'),
        ('CANCELLED', 'Cancelled'),
    )
    
    # Invoice Identification
    invoice_number = models.CharField(
        _("Invoice Number"),
        max_length=50,
        unique=True,
        editable=False,
        help_text="Hospital internal invoice number"
    )
    
    etims_invoice_number = models.CharField(
        _("eTIMS Invoice Number"),
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Invoice number from KRA eTIMS"
    )
    
    etims_cu_invoice_number = models.CharField(
        _("eTIMS CU Invoice Number"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Control Unit invoice number from device"
    )
    
    # Invoice Details
    invoice_type = models.CharField(
        _("Invoice Type"),
        max_length=20,
        choices=INVOICE_TYPE_CHOICES
    )
    invoice_date = models.DateTimeField(_("Invoice Date"), default=timezone.now)
    
    # Customer/Patient Details
    customer_tin = models.CharField(
        _("Customer TIN"),
        max_length=20,
        blank=True,
        null=True,
        help_text="Patient/Customer TIN if available"
    )
    customer_name = models.CharField(_("Customer Name"), max_length=200)
    customer_phone = models.CharField(
        _("Customer Phone"),
        max_length=15,
        blank=True,
        null=True
    )
    
    # Links to Hospital Records
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices'
    )
    
    medicine_sale = models.ForeignKey(
        'MedicineSale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices'
    )
    
    otc_sale = models.ForeignKey(
        'OverTheCounterSale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices'
    )
    
    lab_order = models.ForeignKey(
        'LabOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices'
    )
    
    patient_visit = models.ForeignKey(
        'PatientVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices'
    )
    
    inpatient_admission = models.ForeignKey(
        'InpatientAdmission',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices'
    )
    
    # Financial Details
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    taxable_amount = models.DecimalField(
        _("Taxable Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    vat_rate = models.DecimalField(
        _("VAT Rate (%)"),
        max_digits=5,
        decimal_places=2,
        default=16.00,
        help_text="Current KRA VAT rate"
    )
    
    vat_amount = models.DecimalField(
        _("VAT Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Payment Details
    payment_method = models.CharField(
        _("Payment Method"),
        max_length=20,
        choices=(
            ('CASH', 'Cash'),
            ('MPESA', 'M-Pesa'),
            ('CARD', 'Card'),
            ('BANK', 'Bank Transfer'),
            ('INSURANCE', 'Insurance'),
            ('OTHER', 'Other'),
        )
    )
    
    mpesa_code = models.CharField(
        _("M-Pesa Code"),
        max_length=50,
        blank=True,
        null=True
    )
    
    # Status and Submission
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    submitted_to_etims = models.BooleanField(
        _("Submitted to eTIMS"),
        default=False
    )
    submitted_at = models.DateTimeField(
        _("Submitted At"),
        blank=True,
        null=True
    )
    
    # KRA Response
    etims_response = models.JSONField(
        _("eTIMS Response"),
        blank=True,
        null=True,
        help_text="Full response from KRA eTIMS API"
    )
    
    etims_qr_code = models.TextField(
        _("eTIMS QR Code"),
        blank=True,
        null=True,
        help_text="QR code data from KRA for receipt"
    )
    
    etims_verification_url = models.URLField(
        _("eTIMS Verification URL"),
        blank=True,
        null=True,
        help_text="URL to verify invoice on KRA portal"
    )
    
    # Rejection/Error Details
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True,
        null=True
    )
    
    # Staff
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='etims_invoices_created'
    )
    
    submitted_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_invoices_submitted'
    )
    
    # Insurance & Claims Management
    insurance_company = models.CharField(
        _("Insurance Company"),
        max_length=200,
        blank=True,
        null=True
    )
    insurance_policy_number = models.CharField(
        _("Insurance Policy Number"),
        max_length=100,
        blank=True,
        null=True
    )
    insurance_claim_number = models.CharField(
        _("Insurance Claim Number"),
        max_length=100,
        blank=True,
        null=True,
        help_text="For tracking insurance reimbursements"
    )
    insurance_approval_code = models.CharField(
        _("Insurance Approval Code"),
        max_length=100,
        blank=True,
        null=True
    )

    # NHIF/SHA (Social Health Authority) Integration
    nhif_member_number = models.CharField(
        _("NHIF/SHA Member Number"),
        max_length=50,
        blank=True,
        null=True
    )
    sha_scheme = models.CharField(
        _("SHA Scheme"),
        max_length=50,
        choices=(
            ('SHIF', 'Social Health Insurance Fund'),
            ('PHC', 'Primary Healthcare Fund'),
            ('EDCH', 'Emergency & Chronic Disease Fund'),
            ('PRIVATE', 'Private Insurance'),
            ('SELF_PAY', 'Self Pay'),
        ),
        blank=True,
        null=True
    )

    # Payment Status (critical for revenue recognition)
    payment_status = models.CharField(
        _("Payment Status"),
        max_length=20,
        choices=(
            ('PAID', 'Fully Paid'),
            ('PARTIAL', 'Partially Paid'),
            ('PENDING', 'Pending Payment'),
            ('INSURANCE_PENDING', 'Insurance Claim Pending'),
            ('WAIVED', 'Waived/Charity Care'),
        ),
        default='PENDING'
    )
    amount_paid = models.DecimalField(
        _("Amount Paid (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    amount_pending = models.DecimalField(
        _("Amount Pending (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    payment_due_date = models.DateField(
        _("Payment Due Date"),
        blank=True,
        null=True
    )

    # Privacy Protection
    anonymized_customer_name = models.CharField(
        _("Anonymized Customer Name"),
        max_length=200,
        blank=True,
        help_text="Patient identifier without revealing identity (e.g., PATIENT-001)"
    )
    use_anonymized_data = models.BooleanField(
        _("Use Anonymized Data for eTIMS"),
        default=False
    )

    # Service Details (for privacy-compliant invoicing)
    service_category = models.CharField(
        _("Service Category"),
        max_length=100,
        blank=True,
        help_text="General category without diagnosis details (e.g., 'Medical Consultation')"
    )

    # Exemptions & Waivers
    is_exempt = models.BooleanField(
        _("VAT Exempt"),
        default=True,
        help_text="Most medical services are VAT exempt in Kenya"
    )
    exemption_reason = models.CharField(
        _("Exemption Reason"),
        max_length=200,
        blank=True,
        choices=(
            ('MEDICAL_SERVICES', 'Medical Services (VAT Exempt)'),
            ('EMERGENCY_CARE', 'Emergency Care'),
            ('CHARITY_CARE', 'Charity/Waived Care'),
        )
    )

    # Receipt Information
    printed_receipt_number = models.CharField(
        _("Printed Receipt Number"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Physical receipt number for cash transactions"
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("eTIMS Invoice")
        verbose_name_plural = _("eTIMS Invoices")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['etims_invoice_number']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['invoice_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = eTIMSInvoice.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.invoice_number = f"INV-{date_str}-{count:06d}"
        
        # Calculate VAT if not set
        if self.taxable_amount > 0 and self.vat_amount == 0:
            self.vat_amount = (self.taxable_amount * self.vat_rate) / 100
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name} (KSh {self.total_amount})"
    
    @property
    def can_submit(self):
        """Check if invoice can be submitted to eTIMS"""
        return (
            self.status == 'DRAFT' and
            not self.submitted_to_etims and
            self.total_amount > 0
        )


class eTIMSInvoiceItem(models.Model):
    """
    Individual line items in an eTIMS invoice
    Represents each product/service sold
    """
    TAX_TYPE_CHOICES = (
        ('A', 'VAT Standard Rate (16%)'),
        ('B', 'VAT Exempt'),
        ('C', 'Zero Rated'),
        ('D', 'Special Rate'),
    )
    
    invoice = models.ForeignKey(
        eTIMSInvoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Item Details
    item_sequence = models.IntegerField(
        _("Item Sequence"),
        help_text="Line number in invoice"
    )
    
    item_code = models.CharField(
        _("Item Code"),
        max_length=100,
        help_text="Internal product/service code"
    )
    
    item_name = models.CharField(
        _("Item Name"),
        max_length=200
    )
    
    item_description = models.TextField(
        _("Item Description"),
        blank=True,
        null=True
    )
    
    # KRA Classification
    tax_type = models.CharField(
        _("Tax Type"),
        max_length=1,
        choices=TAX_TYPE_CHOICES,
        default='A'
    )
    
    # Quantity and Pricing
    quantity = models.DecimalField(
        _("Quantity"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    unit_of_measure = models.CharField(
        _("Unit of Measure"),
        max_length=50,
        default='Units'
    )
    
    unit_price = models.DecimalField(
        _("Unit Price (KSh)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Discounts
    discount_amount = models.DecimalField(
        _("Discount Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Tax Calculation
    taxable_amount = models.DecimalField(
        _("Taxable Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    tax_amount = models.DecimalField(
        _("Tax Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    total_amount = models.DecimalField(
        _("Total Amount (KSh)"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("eTIMS Invoice Item")
        verbose_name_plural = _("eTIMS Invoice Items")
        ordering = ['invoice', 'item_sequence']
        unique_together = ['invoice', 'item_sequence']
    
    def save(self, *args, **kwargs):
        # Calculate amounts
        subtotal = (self.quantity * self.unit_price) - self.discount_amount
        
        if self.tax_type == 'A':  # VAT Standard Rate
            self.taxable_amount = subtotal
            self.tax_amount = (subtotal * Decimal('16')) / Decimal('100')
        elif self.tax_type == 'B':  # VAT Exempt
            self.taxable_amount = 0
            self.tax_amount = 0
        elif self.tax_type == 'C':  # Zero Rated
            self.taxable_amount = subtotal
            self.tax_amount = 0
        
        self.total_amount = subtotal + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} x KSh {self.unit_price}"


class eTIMSCreditNote(models.Model):
    """
    Credit notes for refunds/cancellations
    Required by KRA for transaction reversals
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted to KRA'),
        ('APPROVED', 'Approved by KRA'),
        ('REJECTED', 'Rejected by KRA'),
    )
    
    REASON_CHOICES = (
        ('REFUND', 'Refund'),
        ('RETURN', 'Return of Goods'),
        ('ERROR', 'Invoice Error'),
        ('CANCELLATION', 'Cancellation'),
        ('DISCOUNT', 'Post-sale Discount'),
        ('OTHER', 'Other'),
    )
    
    # Credit Note Identification
    credit_note_number = models.CharField(
        _("Credit Note Number"),
        max_length=50,
        unique=True,
        editable=False
    )
    
    etims_credit_note_number = models.CharField(
        _("eTIMS Credit Note Number"),
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    
    # Original Invoice
    original_invoice = models.ForeignKey(
        eTIMSInvoice,
        on_delete=models.CASCADE,
        related_name='credit_notes'
    )
    
    # Credit Note Details
    credit_note_date = models.DateTimeField(_("Credit Note Date"), default=timezone.now)
    reason = models.CharField(
        _("Reason"),
        max_length=20,
        choices=REASON_CHOICES
    )
    reason_description = models.TextField(_("Reason Description"))
    
    # Financial
    credit_amount = models.DecimalField(
        _("Credit Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    vat_amount = models.DecimalField(
        _("VAT Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    
    submitted_to_etims = models.BooleanField(_("Submitted to eTIMS"), default=False)
    submitted_at = models.DateTimeField(_("Submitted At"), blank=True, null=True)
    
    # KRA Response
    etims_response = models.JSONField(
        _("eTIMS Response"),
        blank=True,
        null=True
    )
    
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True, null=True)
    
    # Staff
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='credit_notes_created'
    )
    
    approved_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_notes_approved'
    )
    
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("eTIMS Credit Note")
        verbose_name_plural = _("eTIMS Credit Notes")
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.credit_note_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            count = eTIMSCreditNote.objects.filter(
                created_at__date=today.date()
            ).count() + 1
            self.credit_note_number = f"CN-{date_str}-{count:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.credit_note_number} - KSh {self.credit_amount}"


class eTIMSTransactionLog(models.Model):
    """
    Comprehensive log of all eTIMS API interactions
    For debugging and audit trail
    """
    TRANSACTION_TYPE_CHOICES = (
        ('INVOICE_SUBMIT', 'Invoice Submission'),
        ('INVOICE_QUERY', 'Invoice Query'),
        ('CREDIT_NOTE_SUBMIT', 'Credit Note Submission'),
        ('STOCK_UPDATE', 'Stock Update'),
        ('DEVICE_STATUS', 'Device Status Check'),
        ('OTHER', 'Other'),
    )
    
    transaction_type = models.CharField(
        _("Transaction Type"),
        max_length=30,
        choices=TRANSACTION_TYPE_CHOICES
    )
    
    # Related records
    invoice = models.ForeignKey(
        eTIMSInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaction_logs'
    )
    
    credit_note = models.ForeignKey(
        eTIMSCreditNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaction_logs'
    )
    
    # Request Details
    request_endpoint = models.CharField(_("API Endpoint"), max_length=500)
    request_method = models.CharField(_("HTTP Method"), max_length=10, default='POST')
    request_payload = models.JSONField(_("Request Payload"), blank=True, null=True)
    
    # Response Details
    response_status_code = models.IntegerField(_("Response Status Code"), blank=True, null=True)
    response_body = models.JSONField(_("Response Body"), blank=True, null=True)
    response_time_ms = models.IntegerField(_("Response Time (ms)"), blank=True, null=True)
    
    # Status
    success = models.BooleanField(_("Success"), default=False)
    error_message = models.TextField(_("Error Message"), blank=True, null=True)
    
    # User tracking
    initiated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_transactions'
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("eTIMS Transaction Log")
        verbose_name_plural = _("eTIMS Transaction Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.get_transaction_type_display()} - {status} ({self.created_at})"


class eTIMSInsuranceClaim(models.Model):
    """
    Track insurance claims and their relationship to eTIMS invoices
    Critical for revenue recognition timing
    """
    CLAIM_STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted to Insurance'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('PARTIALLY_APPROVED', 'Partially Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    )
    
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=100,
        unique=True
    )
    invoice = models.ForeignKey(
        eTIMSInvoice,
        on_delete=models.CASCADE,
        related_name='insurance_claims'
    )
    insurance_company = models.CharField(
        _("Insurance Company"),
        max_length=200
    )
    claim_amount = models.DecimalField(
        _("Claim Amount"),
        max_digits=12,
        decimal_places=2
    )
    approved_amount = models.DecimalField(
        _("Approved Amount"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    paid_amount = models.DecimalField(
        _("Paid Amount"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=CLAIM_STATUS_CHOICES,
        default='SUBMITTED'
    )
    submission_date = models.DateField(_("Submission Date"))
    approval_date = models.DateField(
        _("Approval Date"),
        blank=True,
        null=True
    )
    payment_date = models.DateField(
        _("Payment Date"),
        blank=True,
        null=True
    )
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True
    )
    requires_etims_credit_note = models.BooleanField(
        _("Requires Credit Note"),
        default=False,
        help_text="If rejected/partially approved, may need credit note"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("eTIMS Insurance Claim")
        verbose_name_plural = _("eTIMS Insurance Claims")
        
        
class eTIMSDailySummary(models.Model):
    """
    Daily summary of eTIMS transactions
    For reporting and reconciliation
    """
    summary_date = models.DateField(_("Summary Date"), unique=True)
    
    # Invoice Statistics
    total_invoices = models.IntegerField(_("Total Invoices"), default=0)
    submitted_invoices = models.IntegerField(_("Submitted Invoices"), default=0)
    approved_invoices = models.IntegerField(_("Approved Invoices"), default=0)
    rejected_invoices = models.IntegerField(_("Rejected Invoices"), default=0)
    pending_invoices = models.IntegerField(_("Pending Invoices"), default=0)
    
    # Financial Summary
    total_sales = models.DecimalField(
        _("Total Sales (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_vat = models.DecimalField(
        _("Total VAT (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Credit Notes
    total_credit_notes = models.IntegerField(_("Total Credit Notes"), default=0)
    total_credit_amount = models.DecimalField(
        _("Total Credit Amount (KSh)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Payment Methods Breakdown
    cash_sales = models.DecimalField(_("Cash Sales"), max_digits=12, decimal_places=2, default=0)
    mpesa_sales = models.DecimalField(_("M-Pesa Sales"), max_digits=12, decimal_places=2, default=0)
    card_sales = models.DecimalField(_("Card Sales"), max_digits=12, decimal_places=2, default=0)
    insurance_sales = models.DecimalField(_("Insurance Sales"), max_digits=12, decimal_places=2, default=0)
    
    # Payment Status Breakdown
    fully_paid_invoices = models.IntegerField(
        _("Fully Paid Invoices"),
        default=0
    )
    insurance_pending_invoices = models.IntegerField(
        _("Insurance Pending Invoices"),
        default=0
    )
    insurance_pending_amount = models.DecimalField(
        _("Insurance Pending Amount"),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # SHA/NHIF Breakdown
    sha_shif_sales = models.DecimalField(
        _("SHA/SHIF Sales"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    nhif_sales = models.DecimalField(
        _("NHIF Sales (Legacy)"),
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Service Type Breakdown
    consultation_revenue = models.DecimalField(
        _("Consultation Revenue"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    pharmacy_revenue = models.DecimalField(
        _("Pharmacy Revenue"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    laboratory_revenue = models.DecimalField(
        _("Laboratory Revenue"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    inpatient_revenue = models.DecimalField(
        _("Inpatient Revenue"),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Generation info
    generated_at = models.DateTimeField(_("Generated At"), auto_now=True)
    generated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etims_summaries_generated'
    )
    
    class Meta:
        verbose_name = _("eTIMS Daily Summary")
        verbose_name_plural = _("eTIMS Daily Summaries")
        ordering = ['-summary_date']
    
    def __str__(self):
        return f"eTIMS Summary - {self.summary_date}"