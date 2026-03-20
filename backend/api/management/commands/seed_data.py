"""
MediCore HMS — Seed Data Management Command
============================================
Usage:
    python manage.py seed_data

Options:
    --flush     Wipe all seeded data before re-seeding (use with caution)

All demo users are created with password: password123
"""

from django.core.management.base import BaseCommand
from django.db import transaction


PASSWORD = "password123"


class Command(BaseCommand):
    help = "Seed essential reference data and demo users for MediCore HMS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing seeded records before inserting (use with caution)",
        )

    def handle(self, *args, **options):
        self.flush = options["flush"]

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 58))
        self.stdout.write(self.style.MIGRATE_HEADING("   MediCore HMS — Seed Data"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 58))

        with transaction.atomic():
            self._seed_users()
            self._seed_triage_categories()
            self._seed_insurance_providers()
            self._seed_specialized_services()
            self._seed_wards_and_beds()
            self._seed_emergency_beds()
            self._seed_lab_tests()
            self._seed_medicine_categories()
            self._seed_medicines()
            self._seed_icd10_codes()

        self._print_summary()

    # ─── Helpers ──────────────────────────────────────────────

    def section(self, title):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"  {title}"))
        self.stdout.write(self.style.MIGRATE_HEADING("  " + "-" * 50))

    def ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f"    +  {msg}"))

    def skip(self, msg):
        self.stdout.write(self.style.WARNING(f"    ~  {msg}  (already exists - skipped)"))

    def info(self, msg):
        self.stdout.write(f"    {msg}")

    def err(self, msg):
        self.stdout.write(self.style.ERROR(f"    !  {msg}"))

    # ─── 1. Users ─────────────────────────────────────────────

    def _seed_users(self):
        from api.models import User

        self.section("Users")

        usernames_to_flush = [
            "admin", "receptionist", "nurse1", "doctor1", "doctor2",
            "pharmacist1", "cashier1", "labtech1", "insurance1",
            "procurement1", "accountant1", "hr1",
        ]

        if self.flush:
            User.objects.filter(username__in=usernames_to_flush).delete()
            self.info("Flushed existing demo users.")

        # (username, first_name, last_name, email, user_type, is_superuser)
        # user_type must match USER_TYPE_CHOICES in your User model:
        # ADMIN, DOCTOR, RECEPTIONIST, NURSE, PROCUREMENT,
        # LAB_TECH, CASHIER, PHARMACIST, ACCOUNTANT, INSURANCE, HR
        users = [
            ("admin",        "System",   "Admin",    "admin@medicore.ke",        "ADMIN",         True),
            ("receptionist", "Mary",     "Wanjiku",  "reception@medicore.ke",    "RECEPTIONIST",  False),
            ("nurse1",       "Grace",    "Achieng",  "nurse@medicore.ke",        "NURSE",         False),
            ("doctor1",      "James",    "Kariuki",  "doctor@medicore.ke",       "DOCTOR",        False),
            ("doctor2",      "Amina",    "Hassan",   "amina@medicore.ke",        "DOCTOR",        False),
            ("pharmacist1",  "Peter",    "Otieno",   "pharmacy@medicore.ke",     "PHARMACIST",    False),
            ("cashier1",     "Susan",    "Njeri",    "cashier@medicore.ke",      "CASHIER",       False),
            ("labtech1",     "Kevin",    "Mutua",    "lab@medicore.ke",          "LAB_TECH",      False),
            ("insurance1",   "David",    "Mwangi",   "insurance@medicore.ke",    "INSURANCE",     False),
            ("procurement1", "Alice",    "Kamau",    "procurement@medicore.ke",  "PROCUREMENT",   False),
            ("accountant1",  "Brian",    "Odhiambo", "accounts@medicore.ke",     "ACCOUNTANT",    False),
            ("hr1",          "Lilian",   "Chebet",   "hr@medicore.ke",           "HR",            False),
        ]

        created = 0
        for username, first, last, email, utype, superuser in users:
            if User.objects.filter(username=username).exists():
                self.skip(username)
                continue

            try:
                u = User.objects.create_user(
                    username=username,
                    password=PASSWORD,
                    first_name=first,
                    last_name=last,
                    email=email,
                    user_type=utype,
                    phone_number=f"07{abs(hash(username)) % 100000000:08d}",
                )
                if superuser:
                    u.is_staff = True
                    u.is_superuser = True
                    u.save()

                self.ok(f"{utype:<14}  {username:<16}  ({first} {last})")
                created += 1
            except Exception as e:
                self.err(f"Failed to create {username}: {e}")

        self.info(f"{created} user(s) created. Password: {PASSWORD}")

    # ─── 2. Triage Categories ─────────────────────────────────

    def _seed_triage_categories(self):
        from api.models import TriageCategory

        self.section("Triage Categories")

        if self.flush:
            TriageCategory.objects.all().delete()
            self.info("Flushed triage categories.")

        # priority_level, name, color_code, max_wait_time (mins), description
        # Must match PRIORITY_CHOICES and COLOR_CHOICES in your model
        categories = [
            (1, "Immediate",   "RED",    0,   "Life-threatening — immediate care required"),
            (2, "Very Urgent", "ORANGE", 10,  "Potentially life-threatening — seen within 10 minutes"),
            (3, "Urgent",      "YELLOW", 30,  "Serious condition — seen within 30 minutes"),
            (4, "Standard",    "GREEN",  60,  "Less urgent — seen within 60 minutes"),
            (5, "Non-Urgent",  "BLUE",   120, "Minor complaint — seen within 120 minutes"),
        ]

        for priority, name, color, wait, desc in categories:
            obj, created = TriageCategory.objects.get_or_create(
                priority_level=priority,
                defaults=dict(
                    name=name,
                    color_code=color,
                    max_wait_time=wait,
                    description=desc,
                    is_active=True,
                ),
            )
            if created:
                self.ok(f"Priority {priority}  [{color:<6}]  {name}  (max wait: {wait} min)")
            else:
                self.skip(f"Priority {priority}  [{color}]  {name}")

    # ─── 3. Insurance Providers ───────────────────────────────

    def _seed_insurance_providers(self):
        from api.models import InsuranceProvider

        self.section("Insurance Providers")

        if self.flush:
            InsuranceProvider.objects.all().delete()
            self.info("Flushed insurance providers.")

        # Your InsuranceProvider model only has: name
        providers = [
            "SHA",
            "NHIF",
            "AAR",
            "Jubilee",
            "Resolution",
            "CIC",
            "Britam",
            "Madison",
            "GA Insurance",
            "UAP Old Mutual",
            "Minet",
            "APA Insurance",
        ]

        for name in providers:
            obj, created = InsuranceProvider.objects.get_or_create(name=name)
            if created:
                self.ok(name)
            else:
                self.skip(name)

    # ─── 4. Specialized Services ──────────────────────────────

    def _seed_specialized_services(self):
        from api.models import SpecializedService

        self.section("Specialized Services / Clinics")

        if self.flush:
            SpecializedService.objects.all().delete()
            self.info("Flushed specialized services.")

        # Your SpecializedService model has: name, consultation_fee, description
        services = [
            ("General OPD",             500,  "General outpatient consultation"),
            ("Paediatrics Clinic",      700,  "Children's health consultations (0–12 years)"),
            ("Antenatal Care (ANC)",    600,  "Maternal and prenatal care"),
            ("Postnatal Care (PNC)",    600,  "Postnatal mother and baby care"),
            ("Dental Clinic",           800,  "Dental examinations and procedures"),
            ("Eye Clinic",              750,  "Ophthalmology consultations"),
            ("Physiotherapy",           900,  "Physiotherapy and rehabilitation"),
            ("ENT Clinic",              850,  "Ear, nose and throat consultations"),
            ("Mental Health / Psych",   1000, "Psychiatry and counselling services"),
            ("Nutrition & Dietetics",   600,  "Nutritional assessment and counselling"),
            ("VCT / HIV Clinic",        0,    "Voluntary counselling and testing"),
            ("Surgical Clinic",         1200, "Surgical outpatient consultations"),
            ("Orthopaedic Clinic",      1000, "Bone and joint consultations"),
            ("Dermatology Clinic",      900,  "Skin disease consultations"),
            ("Cardiology Clinic",       1500, "Heart disease consultations"),
        ]

        for name, fee, desc in services:
            obj, created = SpecializedService.objects.get_or_create(
                name=name,
                defaults=dict(
                    consultation_fee=fee,
                    description=desc,
                ),
            )
            if created:
                self.ok(f"{name:<30}  KSh {fee:,}")
            else:
                self.skip(name)

    # ─── 5. Wards & Beds ──────────────────────────────────────

    def _seed_wards_and_beds(self):
        from api.models import Ward, Bed

        self.section("Wards & Beds")

        if self.flush:
            Bed.objects.all().delete()
            Ward.objects.all().delete()
            self.info("Flushed wards and beds.")

        # (ward_name, ward_type, bed_count, bed_prefix, daily_rate)
        # ward_type must match WARD_TYPE_CHOICES:
        # GENERAL, PRIVATE, ICU, HDU, MATERNITY, PEDIATRIC, SURGICAL, MEDICAL, ISOLATION, EMERGENCY
        wards = [
            ("Male General Ward",   "GENERAL",   20, "MG",  1500),
            ("Female General Ward", "GENERAL",   20, "FG",  1500),
            ("Paediatric Ward",     "PEDIATRIC", 10, "PED", 1500),
            ("Maternity Ward",      "MATERNITY",  8, "MAT", 2000),
            ("ICU",                 "ICU",         6, "ICU", 8000),
            ("HDU",                 "HDU",         8, "HDU", 5000),
            ("Private Wing",        "PRIVATE",    10, "PVT", 4000),
            ("Surgical Ward",       "SURGICAL",   12, "SRG", 2000),
            ("Medical Ward",        "MEDICAL",    15, "MED", 1500),
            ("Isolation Ward",      "ISOLATION",   4, "ISO", 3000),
        ]

        total_wards = 0
        total_beds = 0

        for ward_name, ward_type, bed_count, prefix, rate in wards:
            ward, w_created = Ward.objects.get_or_create(
                ward_name=ward_name,
                defaults=dict(
                    ward_code=prefix,
                    ward_type=ward_type,
                    total_beds=bed_count,
                    is_active=True,
                ),
            )

            if not w_created:
                self.skip(f"Ward: {ward_name}")
                continue

            total_wards += 1
            beds_created = 0

            for i in range(1, bed_count + 1):
                bed_num = f"{prefix}-{i:02d}"

                # bed_type must match BED_TYPE_CHOICES:
                # STANDARD, ICU, ELECTRIC, PEDIATRIC, MATERNITY, ISOLATION
                if ward_type == "ICU":
                    bed_type = "ICU"
                elif ward_type == "PEDIATRIC":
                    bed_type = "PEDIATRIC"
                elif ward_type == "MATERNITY":
                    bed_type = "MATERNITY"
                elif ward_type == "ISOLATION":
                    bed_type = "ISOLATION"
                else:
                    bed_type = "STANDARD"

                _, bc = Bed.objects.get_or_create(
                    bed_number=bed_num,
                    defaults=dict(
                        ward=ward,
                        bed_type=bed_type,
                        status="AVAILABLE",
                        daily_rate=rate,
                        has_oxygen=(ward_type in ["ICU", "HDU", "MATERNITY"]),
                        has_monitor=(ward_type in ["ICU", "HDU"]),
                        is_active=True,
                    ),
                )
                if bc:
                    beds_created += 1
                    total_beds += 1

            self.ok(f"Ward: {ward_name:<25}  {beds_created} bed(s)  KSh {rate:,}/day")

        self.info(f"Total: {total_wards} ward(s), {total_beds} bed(s) created.")

    # ─── 6. Emergency Beds ────────────────────────────────────

    def _seed_emergency_beds(self):
        from api.models import EmergencyBed

        self.section("Emergency / Casualty Beds")

        if self.flush:
            EmergencyBed.objects.all().delete()
            self.info("Flushed emergency beds.")

        # Your EmergencyBed model has: bed_number, location, status, has_oxygen,
        # has_monitor, has_suction, is_active, notes
        # status choices: AVAILABLE, OCCUPIED, MAINTENANCE
        beds = [
            ("RESUS-01",  "Resuscitation Bay 1",   True,  True,  True),
            ("RESUS-02",  "Resuscitation Bay 2",   True,  True,  True),
            ("TRIAGE-01", "Triage Area 1",          True,  False, False),
            ("TRIAGE-02", "Triage Area 2",          True,  False, False),
            ("TRIAGE-03", "Triage Area 3",          False, False, False),
            ("TREAT-01",  "Treatment Room A - Bed 1", True, True, True),
            ("TREAT-02",  "Treatment Room A - Bed 2", True, False, True),
            ("TREAT-03",  "Treatment Room B - Bed 1", True, True, True),
            ("TREAT-04",  "Treatment Room B - Bed 2", True, False, False),
            ("OBS-01",    "Observation Bay - Bed 1",  True, True, False),
            ("OBS-02",    "Observation Bay - Bed 2",  True, True, False),
            ("OBS-03",    "Observation Bay - Bed 3",  False, False, False),
        ]

        for num, location, oxygen, monitor, suction in beds:
            obj, created = EmergencyBed.objects.get_or_create(
                bed_number=num,
                defaults=dict(
                    location=location,
                    status="AVAILABLE",
                    has_oxygen=oxygen,
                    has_monitor=monitor,
                    has_suction=suction,
                    is_active=True,
                ),
            )
            if created:
                self.ok(f"{num:<14}  {location}")
            else:
                self.skip(num)

    # ─── 7. Lab Tests ─────────────────────────────────────────

    def _seed_lab_tests(self):
        from api.models import LabTest, LabTestCategory

        self.section("Laboratory Tests")

        if self.flush:
            LabTest.objects.all().delete()
            LabTestCategory.objects.all().delete()
            self.info("Flushed lab tests and categories.")

        # Create categories first
        # category_type must match CATEGORY_TYPE_CHOICES:
        # HEMATOLOGY, BIOCHEMISTRY, MICROBIOLOGY, SEROLOGY, IMMUNOLOGY,
        # PARASITOLOGY, HISTOPATHOLOGY, CYTOLOGY, MOLECULAR,
        # RADIOLOGY, ULTRASOUND, XRAY, CT_SCAN, MRI, OTHER
        cat_defs = [
            ("Haematology",   "HEMATOLOGY",   "Haematology Lab"),
            ("Biochemistry",  "BIOCHEMISTRY", "Chemistry Lab"),
            ("Microbiology",  "MICROBIOLOGY", "Microbiology Lab"),
            ("Parasitology",  "PARASITOLOGY", "Parasitology Lab"),
            ("Serology",      "SEROLOGY",     "Serology Lab"),
            ("Immunology",    "IMMUNOLOGY",   "Immunology Lab"),
            ("Coagulation",   "HEMATOLOGY",   "Haematology Lab"),
            ("Molecular",     "MOLECULAR",    "Molecular Lab"),
            ("Endocrinology", "BIOCHEMISTRY", "Chemistry Lab"),
        ]

        cat_map = {}
        for cat_name, cat_type, dept in cat_defs:
            cat, _ = LabTestCategory.objects.get_or_create(
                name=cat_name,
                defaults=dict(
                    category_type=cat_type,
                    department=dept,
                    is_active=True,
                ),
            )
            cat_map[cat_name] = cat

        # sample_type must match SAMPLE_TYPE_CHOICES:
        # BLOOD, URINE, STOOL, SPUTUM, CSF, SWAB, TISSUE, FLUID, NONE, OTHER
        tests = [
            # (code, name, category, sample_type, cost, turnaround_hours, nhif, sha)
            ("FBC",        "Full Blood Count",                   "Haematology",   "BLOOD",  350,  2,  True,  True),
            ("RBS",        "Random Blood Sugar",                 "Biochemistry",  "BLOOD",  150,  1,  True,  True),
            ("FBS",        "Fasting Blood Sugar",               "Biochemistry",  "BLOOD",  150,  1,  True,  True),
            ("HBA1C",      "Glycated Haemoglobin (HbA1c)",      "Biochemistry",  "BLOOD",  1200, 4,  True,  True),
            ("LFT",        "Liver Function Tests",               "Biochemistry",  "BLOOD",  1800, 4,  True,  True),
            ("RFT",        "Renal Function Tests",               "Biochemistry",  "BLOOD",  1800, 4,  True,  True),
            ("LIPID",      "Lipid Profile",                      "Biochemistry",  "BLOOD",  1500, 4,  True,  True),
            ("TSH",        "Thyroid Stimulating Hormone",        "Endocrinology", "BLOOD",  1800, 6,  True,  True),
            ("T3T4",       "T3 and T4 Thyroid Panel",           "Endocrinology", "BLOOD",  2200, 6,  False, True),
            ("URINE",      "Urinalysis (Urine RE/ME)",          "Microbiology",  "URINE",  300,  2,  True,  True),
            ("UCSSS",      "Urine Culture & Sensitivity",       "Microbiology",  "URINE",  1200, 48, True,  True),
            ("MALARIA",    "Malaria RDT",                       "Parasitology",  "BLOOD",  250,  1,  True,  True),
            ("MFILM",      "Malaria Thick & Thin Film",         "Parasitology",  "BLOOD",  400,  2,  True,  True),
            ("HIV",        "HIV Rapid Test",                    "Serology",      "BLOOD",  200,  1,  True,  True),
            ("HEPB",       "Hepatitis B Surface Antigen",       "Serology",      "BLOOD",  600,  2,  True,  True),
            ("HEPC",       "Hepatitis C Antibody",              "Serology",      "BLOOD",  800,  2,  True,  True),
            ("WIDAL",      "Widal Test (Typhoid)",              "Serology",      "BLOOD",  500,  4,  True,  True),
            ("VDRL",       "VDRL (Syphilis)",                   "Serology",      "BLOOD",  400,  2,  True,  True),
            ("CRP",        "C-Reactive Protein",                "Immunology",    "BLOOD",  800,  4,  True,  True),
            ("ESR",        "Erythrocyte Sedimentation Rate",    "Haematology",   "BLOOD",  300,  2,  True,  True),
            ("PT",         "Prothrombin Time / INR",            "Coagulation",   "BLOOD",  900,  3,  True,  True),
            ("APTT",       "Activated Partial Thromboplastin",  "Coagulation",   "BLOOD",  900,  3,  False, True),
            ("STOOL",      "Stool Microscopy & Culture",        "Microbiology",  "STOOL",  600,  48, True,  True),
            ("SPUTUM",     "Sputum GeneXpert (TB)",             "Microbiology",  "SPUTUM", 0,    24, True,  True),
            ("SPUTUM_CS",  "Sputum Culture & Sensitivity",     "Microbiology",  "SPUTUM", 1500, 72, True,  True),
            ("CD4",        "CD4 Count",                         "Immunology",    "BLOOD",  1500, 6,  True,  True),
            ("VL",         "HIV Viral Load",                    "Molecular",     "BLOOD",  3000, 72, True,  True),
            ("PREG",       "Pregnancy Test (Urine HCG)",        "Biochemistry",  "URINE",  200,  1,  True,  True),
            ("CREATININE", "Serum Creatinine",                  "Biochemistry",  "BLOOD",  500,  2,  True,  True),
            ("UREA",       "Blood Urea Nitrogen",               "Biochemistry",  "BLOOD",  400,  2,  True,  True),
            ("ELECTRO",    "Serum Electrolytes (Na, K, Cl)",    "Biochemistry",  "BLOOD",  1200, 3,  True,  True),
            ("URIC",       "Uric Acid",                         "Biochemistry",  "BLOOD",  500,  2,  False, True),
            ("PSA",        "Prostate Specific Antigen",         "Serology",      "BLOOD",  2000, 4,  True,  True),
            ("BGROUP",     "Blood Group & Rhesus Factor",       "Haematology",   "BLOOD",  300,  1,  True,  True),
            ("CROSS",      "Cross-Match",                       "Haematology",   "BLOOD",  800,  2,  True,  True),
            ("SWAB_CS",    "Swab Culture & Sensitivity",        "Microbiology",  "SWAB",   1200, 48, True,  True),
        ]

        created_count = 0
        for code, name, cat_name, sample, cost, tat, nhif, sha in tests:
            if cat_name not in cat_map:
                self.err(f"Category '{cat_name}' not found for test {code}")
                continue

            obj, created = LabTest.objects.get_or_create(
                test_code=code,
                defaults=dict(
                    test_name=name,
                    category=cat_map[cat_name],
                    sample_type=sample,
                    cost=cost,
                    turnaround_time=tat,
                    nhif_covered=nhif,
                    sha_covered=sha,
                    is_active=True,
                ),
            )
            if created:
                created_count += 1

        self.info(f"{created_count} lab test(s) created out of {len(tests)} defined.")

    # ─── 8. Medicine Categories ───────────────────────────────

    def _seed_medicine_categories(self):
        from api.models import MedicineCategory

        self.section("Medicine Categories")

        if self.flush:
            MedicineCategory.objects.all().delete()
            self.info("Flushed medicine categories.")

        categories = [
            ("Antibiotics",       "Medicines that fight bacterial infections"),
            ("Analgesics",        "Pain relief medicines"),
            ("Antipyretics",      "Fever reducing medicines"),
            ("Antifungals",       "Medicines that fight fungal infections"),
            ("Antivirals",        "Medicines that fight viral infections"),
            ("Antiparasitics",    "Medicines that fight parasitic infections"),
            ("Antimalarials",     "Medicines for malaria treatment and prevention"),
            ("ARVs",              "Antiretroviral medicines for HIV/AIDS"),
            ("Antituberculars",   "Medicines for tuberculosis treatment"),
            ("Cardiovascular",    "Heart and blood pressure medicines"),
            ("Antidiabetics",     "Medicines for diabetes management"),
            ("GI Medicines",      "Gastrointestinal medicines"),
            ("Respiratory",       "Medicines for respiratory conditions"),
            ("Steroids",          "Corticosteroid medicines"),
            ("Antihistamines",    "Allergy medicines"),
            ("Supplements",       "Vitamins, minerals and nutritional supplements"),
            ("Vitamins",          "Vitamin supplements"),
            ("IV Fluids",         "Intravenous fluids and solutions"),
            ("Topical",           "Creams, ointments and topical applications"),
            ("Obstetrics",        "Medicines for maternal and obstetric care"),
            ("Anaesthetics",      "Local and general anaesthetic agents"),
            ("Ophthalmology",     "Eye drops and eye medicines"),
            ("Dermatology",       "Skin condition medicines"),
            ("CNS",               "Central nervous system medicines"),
            ("Other",             "Other medicines not categorised above"),
        ]

        created_count = 0
        for name, desc in categories:
            obj, created = MedicineCategory.objects.get_or_create(
                name=name,
                defaults=dict(description=desc),
            )
            if created:
                created_count += 1
                self.ok(name)
            else:
                self.skip(name)

        self.info(f"{created_count} medicine category/ies created.")

    # ─── 9. Medicines ─────────────────────────────────────────

    def _seed_medicines(self):
        from api.models import Medicine, MedicineCategory

        self.section("Medicines (Essential Formulary)")

        if self.flush:
            Medicine.objects.all().delete()
            self.info("Flushed medicines.")

        # Build category map
        cat_map = {c.name: c for c in MedicineCategory.objects.all()}

        # unit_type must match UNIT_TYPE_CHOICES in your Medicine model:
        # TABLET, CAPSULE, SYRUP_ML, INJECTION, CREAM_TUBE, DROPS, SACHET, SUPPOSITORY
        #
        # Fields on your Medicine model:
        # name, category(FK), description, manufacturer,
        # unit_type, units_per_pack, pack_name,
        # quantity_in_stock, reorder_level,
        # cost_per_unit_cash, price_per_unit_cash, price_per_unit_insurance
        #
        # (name, category, unit_type, units_per_pack, pack_name,
        #  qty_in_stock, reorder_level, cost_per_unit, cash_price, ins_price)

        medicines = [
            # ANTIBIOTICS
            ("Amoxicillin 500mg Capsules",         "Antibiotics",    "CAPSULE",   10,  "Strip",  500,  100, 4,    8,    6),
            ("Amoxicillin 250mg Syrup 100ml",      "Antibiotics",    "SYRUP_ML",  100, "Bottle", 100,  30,  0.8,  1.5,  1.1),
            ("Azithromycin 500mg Tablets",         "Antibiotics",    "TABLET",    3,   "Pack",   200,  50,  45,   90,   65),
            ("Cotrimoxazole 480mg Tablets",        "Antibiotics",    "TABLET",    100, "Pack",   1000, 200, 0.5,  1.0,  0.7),
            ("Cotrimoxazole 240mg/5ml Syrup",      "Antibiotics",    "SYRUP_ML",  100, "Bottle", 100,  30,  0.6,  1.2,  0.85),
            ("Metronidazole 400mg Tablets",        "Antibiotics",    "TABLET",    10,  "Strip",  500,  100, 0.5,  1.2,  0.8),
            ("Ciprofloxacin 500mg Tablets",        "Antibiotics",    "TABLET",    10,  "Strip",  300,  60,  2.0,  4.5,  3.0),
            ("Erythromycin 250mg Tablets",         "Antibiotics",    "TABLET",    10,  "Strip",  300,  60,  1.5,  3.5,  2.5),
            ("Doxycycline 100mg Capsules",         "Antibiotics",    "CAPSULE",   10,  "Strip",  200,  50,  1.0,  2.5,  1.8),
            ("Cloxacillin 250mg Capsules",         "Antibiotics",    "CAPSULE",   10,  "Strip",  200,  50,  3.0,  7.0,  5.0),
            ("Amoxicillin/Clavulanate 625mg",      "Antibiotics",    "TABLET",    10,  "Strip",  150,  40,  25,   55,   40),
            ("Ceftriaxone 1g Injection",           "Antibiotics",    "INJECTION", 1,   "Vial",   100,  30,  150,  350,  250),
            ("Gentamicin 80mg/2ml Injection",      "Antibiotics",    "INJECTION", 1,   "Ampoule",50,   20,  80,   180,  130),
            ("Penicillin G 1MU Injection",         "Antibiotics",    "INJECTION", 1,   "Vial",   50,   20,  60,   140,  100),

            # ANALGESICS / ANTIPYRETICS
            ("Paracetamol 500mg Tablets",          "Analgesics",     "TABLET",    24,  "Pack",   2000, 300, 0.2,  0.5,  0.3),
            ("Paracetamol 120mg/5ml Syrup 100ml",  "Analgesics",     "SYRUP_ML",  100, "Bottle", 200,  50,  0.6,  1.2,  0.85),
            ("Paracetamol 1g/100ml IV Infusion",   "Analgesics",     "INJECTION", 100, "Bag",    50,   20,  4.5,  10,   7.5),
            ("Ibuprofen 400mg Tablets",            "Analgesics",     "TABLET",    10,  "Strip",  500,  100, 0.8,  2.0,  1.4),
            ("Diclofenac 50mg Tablets",            "Analgesics",     "TABLET",    10,  "Strip",  400,  80,  1.0,  2.5,  1.8),
            ("Diclofenac 75mg/3ml Injection",      "Analgesics",     "INJECTION", 1,   "Ampoule",100,  30,  50,   120,  80),
            ("Tramadol 50mg Capsules",             "Analgesics",     "CAPSULE",   10,  "Strip",  200,  50,  5.0,  12,   8.5),
            ("Morphine 10mg/ml Injection",         "Analgesics",     "INJECTION", 1,   "Ampoule",30,   10,  200,  500,  380),
            ("Pethidine 100mg/2ml Injection",      "Analgesics",     "INJECTION", 1,   "Ampoule",20,   10,  150,  380,  280),

            # ANTIMALARIALS
            ("Artemether/Lumefantrine 20/120mg",   "Antimalarials",  "TABLET",    24,  "Pack",   200,  50,  5.0,  12,   8.5),
            ("Artesunate 60mg Injection",          "Antimalarials",  "INJECTION", 1,   "Vial",   50,   20,  350,  800,  580),
            ("Quinine 300mg Tablets",              "Antimalarials",  "TABLET",    10,  "Strip",  100,  30,  1.5,  3.5,  2.5),
            ("Quinine 300mg/ml Injection",         "Antimalarials",  "INJECTION", 1,   "Ampoule",50,   20,  80,   200,  145),
            ("Chloroquine 250mg Tablets",          "Antimalarials",  "TABLET",    10,  "Strip",  100,  30,  1.0,  2.5,  1.8),
            ("Primaquine 15mg Tablets",            "Antimalarials",  "TABLET",    14,  "Strip",  100,  30,  5.0,  12,   8.5),

            # ARVs (usually free via KEMSA — selling price 0)
            ("Nevirapine 200mg Tablets",           "ARVs",           "TABLET",    60,  "Pack",   200,  60,  2.5,  0,    0),
            ("Efavirenz 600mg Tablets",            "ARVs",           "TABLET",    30,  "Pack",   200,  60,  4.0,  0,    0),
            ("Tenofovir 300mg Tablets",            "ARVs",           "TABLET",    30,  "Pack",   200,  60,  4.5,  0,    0),
            ("Lamivudine 150mg Tablets",           "ARVs",           "TABLET",    60,  "Pack",   200,  60,  2.0,  0,    0),
            ("TDF/3TC/EFV (Triomune) Tablets",     "ARVs",           "TABLET",    30,  "Pack",   150,  50,  8.0,  0,    0),
            ("Zidovudine 300mg Tablets",           "ARVs",           "TABLET",    60,  "Pack",   150,  50,  3.0,  0,    0),

            # GI MEDICINES
            ("Omeprazole 20mg Capsules",           "GI Medicines",   "CAPSULE",   14,  "Strip",  300,  60,  1.5,  3.5,  2.5),
            ("Ranitidine 150mg Tablets",           "GI Medicines",   "TABLET",    10,  "Strip",  200,  50,  1.0,  2.5,  1.8),
            ("Metronidazole 200mg/5ml Syrup",      "GI Medicines",   "SYRUP_ML",  100, "Bottle", 100,  30,  0.8,  1.6,  1.1),
            ("Hyoscine Butylbromide 10mg Tablets", "GI Medicines",   "TABLET",    10,  "Strip",  200,  50,  2.0,  5.0,  3.5),
            ("Hyoscine 20mg/ml Injection",         "GI Medicines",   "INJECTION", 1,   "Ampoule",50,   20,  50,   120,  85),
            ("ORS Sachets",                        "GI Medicines",   "SACHET",    1,   "Sachet", 500,  100, 15,   30,   20),
            ("Loperamide 2mg Capsules",            "GI Medicines",   "CAPSULE",   10,  "Strip",  200,  50,  2.0,  5.0,  3.5),

            # CARDIOVASCULAR
            ("Amlodipine 5mg Tablets",             "Cardiovascular", "TABLET",    30,  "Pack",   300,  60,  0.8,  2.0,  1.4),
            ("Amlodipine 10mg Tablets",            "Cardiovascular", "TABLET",    30,  "Pack",   200,  50,  1.0,  2.5,  1.8),
            ("Lisinopril 5mg Tablets",             "Cardiovascular", "TABLET",    30,  "Pack",   200,  50,  1.2,  3.0,  2.2),
            ("Lisinopril 10mg Tablets",            "Cardiovascular", "TABLET",    30,  "Pack",   200,  50,  1.5,  3.5,  2.5),
            ("Atenolol 50mg Tablets",              "Cardiovascular", "TABLET",    28,  "Pack",   200,  50,  0.8,  2.0,  1.4),
            ("Atenolol 100mg Tablets",             "Cardiovascular", "TABLET",    28,  "Pack",   200,  50,  1.2,  3.0,  2.2),
            ("Furosemide 40mg Tablets",            "Cardiovascular", "TABLET",    28,  "Pack",   200,  50,  0.5,  1.2,  0.85),
            ("Furosemide 20mg/2ml Injection",      "Cardiovascular", "INJECTION", 1,   "Ampoule",50,   20,  30,   70,   50),
            ("Hydrochlorothiazide 25mg Tablets",   "Cardiovascular", "TABLET",    28,  "Pack",   200,  50,  0.5,  1.2,  0.85),
            ("Digoxin 0.25mg Tablets",             "Cardiovascular", "TABLET",    28,  "Pack",   100,  30,  1.5,  3.5,  2.5),
            ("Aspirin 75mg Tablets",               "Cardiovascular", "TABLET",    28,  "Pack",   300,  60,  0.3,  0.8,  0.55),
            ("Atorvastatin 10mg Tablets",          "Cardiovascular", "TABLET",    30,  "Pack",   200,  50,  3.0,  7.0,  5.0),

            # ANTIDIABETICS
            ("Metformin 500mg Tablets",            "Antidiabetics",  "TABLET",    30,  "Pack",   300,  60,  0.8,  2.0,  1.4),
            ("Metformin 850mg Tablets",            "Antidiabetics",  "TABLET",    30,  "Pack",   200,  50,  1.2,  2.8,  2.0),
            ("Glibenclamide 5mg Tablets",          "Antidiabetics",  "TABLET",    28,  "Pack",   200,  50,  0.8,  1.8,  1.3),
            ("Glimepiride 2mg Tablets",            "Antidiabetics",  "TABLET",    30,  "Pack",   150,  40,  2.0,  5.0,  3.5),
            ("Human Insulin Actrapid 100IU/ml",    "Antidiabetics",  "INJECTION", 1,   "Vial",   20,   8,   850,  1800, 1200),
            ("Human Insulin Mixtard 30/70",        "Antidiabetics",  "INJECTION", 1,   "Vial",   20,   8,   900,  1900, 1300),
            ("50% Dextrose 50ml Injection",        "Antidiabetics",  "INJECTION", 1,   "Vial",   50,   20,  120,  250,  180),

            # STEROIDS
            ("Dexamethasone 4mg Injection",        "Steroids",       "INJECTION", 1,   "Ampoule",100,  30,  40,   90,   65),
            ("Dexamethasone 0.5mg Tablets",        "Steroids",       "TABLET",    10,  "Strip",  200,  50,  1.5,  3.5,  2.5),
            ("Prednisolone 5mg Tablets",           "Steroids",       "TABLET",    30,  "Pack",   300,  60,  0.5,  1.2,  0.85),
            ("Hydrocortisone 100mg Injection",     "Steroids",       "INJECTION", 1,   "Vial",   50,   20,  150,  350,  250),
            ("Bethametasone 4mg/ml Injection",     "Steroids",       "INJECTION", 1,   "Ampoule",30,   10,  180,  420,  300),

            # RESPIRATORY
            ("Salbutamol 100mcg Inhaler",          "Respiratory",    "DROPS",     200, "Inhaler",50,   15,  2.25, 4.75, 3.25),
            ("Beclomethasone 100mcg Inhaler",      "Respiratory",    "DROPS",     200, "Inhaler",30,   10,  3.0,  6.0,  4.25),
            ("Aminophylline 250mg/10ml Injection", "Respiratory",    "INJECTION", 1,   "Ampoule",30,   10,  80,   200,  145),
            ("Salbutamol Nebules 2.5mg/2.5ml",     "Respiratory",    "DROPS",     20,  "Box",    50,   20,  15,   35,   25),

            # ANTIHISTAMINES
            ("Loratadine 10mg Tablets",            "Antihistamines", "TABLET",    10,  "Strip",  200,  50,  0.8,  1.8,  1.3),
            ("Chlorpheniramine 4mg Tablets",       "Antihistamines", "TABLET",    10,  "Strip",  200,  50,  0.3,  0.8,  0.55),
            ("Promethazine 25mg Tablets",          "Antihistamines", "TABLET",    10,  "Strip",  200,  50,  0.5,  1.2,  0.85),
            ("Promethazine 25mg/ml Injection",     "Antihistamines", "INJECTION", 1,   "Ampoule",50,   20,  40,   100,  72),

            # SUPPLEMENTS & VITAMINS
            ("Ferrous Sulphate 200mg Tablets",     "Supplements",    "TABLET",    30,  "Pack",   500,  100, 0.5,  1.2,  0.85),
            ("Folic Acid 5mg Tablets",             "Supplements",    "TABLET",    28,  "Pack",   500,  100, 0.3,  0.8,  0.55),
            ("Zinc 20mg Tablets",                  "Supplements",    "TABLET",    10,  "Strip",  300,  60,  0.5,  1.2,  0.85),
            ("Vitamin B Complex Tablets",          "Vitamins",       "TABLET",    30,  "Pack",   300,  60,  0.8,  2.0,  1.4),
            ("Vitamin C 250mg Tablets",            "Vitamins",       "TABLET",    30,  "Pack",   300,  60,  0.5,  1.2,  0.85),
            ("Vitamin K 1mg/0.5ml Injection",      "Vitamins",       "INJECTION", 1,   "Ampoule",50,   20,  80,   180,  130),
            ("Calcium Carbonate 500mg Tablets",    "Supplements",    "TABLET",    30,  "Pack",   200,  50,  1.0,  2.5,  1.8),
            ("Multivitamin Tablets",               "Vitamins",       "TABLET",    30,  "Pack",   200,  50,  1.2,  3.0,  2.2),

            # IV FLUIDS
            ("Normal Saline 0.9% 500ml",           "IV Fluids",      "SYRUP_ML",  500, "Bag",    100,  30,  0.24, 0.5,  0.36),
            ("Ringer's Lactate 500ml",             "IV Fluids",      "SYRUP_ML",  500, "Bag",    100,  30,  0.26, 0.54, 0.38),
            ("5% Dextrose 500ml",                  "IV Fluids",      "SYRUP_ML",  500, "Bag",    100,  30,  0.24, 0.5,  0.36),
            ("10% Dextrose 500ml",                 "IV Fluids",      "SYRUP_ML",  500, "Bag",    50,   20,  0.40, 0.85, 0.60),
            ("Dextrose Saline 500ml",              "IV Fluids",      "SYRUP_ML",  500, "Bag",    100,  30,  0.24, 0.5,  0.36),

            # TOPICAL
            ("Mupirocin 2% Ointment 15g",          "Topical",        "CREAM_TUBE",1,   "Tube",   30,   10,  280,  600,  420),
            ("Hydrocortisone 1% Cream 15g",        "Topical",        "CREAM_TUBE",1,   "Tube",   30,   10,  150,  320,  230),
            ("Betamethasone 0.1% Cream 15g",       "Topical",        "CREAM_TUBE",1,   "Tube",   30,   10,  180,  400,  290),
            ("Silver Sulfadiazine 1% Cream",       "Topical",        "CREAM_TUBE",1,   "Tube",   20,   8,   350,  800,  580),
            ("Calamine Lotion 100ml",              "Topical",        "SYRUP_ML",  100, "Bottle", 30,   10,  0.5,  1.2,  0.85),

            # ANTIFUNGALS
            ("Clotrimazole 1% Cream 20g",          "Antifungals",    "CREAM_TUBE",1,   "Tube",   30,   10,  120,  280,  200),
            ("Fluconazole 150mg Capsules",         "Antifungals",    "CAPSULE",   1,   "Capsule",100,  30,  30,   70,   50),
            ("Fluconazole 200mg/100ml Infusion",   "Antifungals",    "INJECTION", 100, "Bag",    20,   8,   350,  800,  580),
            ("Nystatin 100,000IU Pessaries",       "Antifungals",    "SUPPOSITORY",6,  "Pack",   50,   20,  60,   140,  100),
            ("Griseofulvin 125mg Tablets",         "Antifungals",    "TABLET",    30,  "Pack",   100,  30,  3.0,  7.0,  5.0),

            # OBSTETRICS
            ("Oxytocin 10IU/ml Injection",         "Obstetrics",     "INJECTION", 1,   "Ampoule",100,  30,  50,   120,  85),
            ("Magnesium Sulphate 50% 10ml Inj",    "Obstetrics",     "INJECTION", 1,   "Ampoule",50,   20,  80,   180,  130),
            ("Misoprostol 200mcg Tablets",         "Obstetrics",     "TABLET",    1,   "Tablet", 50,   20,  80,   200,  145),
            ("Methyldopa 250mg Tablets",           "Obstetrics",     "TABLET",    30,  "Pack",   100,  30,  2.0,  5.0,  3.5),
            ("Nifedipine 10mg Capsules",           "Obstetrics",     "CAPSULE",   30,  "Pack",   100,  30,  1.0,  2.5,  1.8),
            ("Iron/Folic Acid Tablets",            "Obstetrics",     "TABLET",    30,  "Pack",   200,  50,  0.5,  1.2,  0.85),
        ]

        created_count = 0
        skipped_count = 0

        for row in medicines:
            name, cat_name, unit_type, units_per_pack, pack_name, qty, reorder, cost, cash, ins = row

            if cat_name not in cat_map:
                self.err(f"Category '{cat_name}' not found for '{name}'")
                continue

            _, created = Medicine.objects.get_or_create(
                name=name,
                defaults=dict(
                    category=cat_map[cat_name],
                    unit_type=unit_type,
                    units_per_pack=units_per_pack,
                    pack_name=pack_name,
                    quantity_in_stock=qty,
                    reorder_level=reorder,
                    cost_per_unit_cash=cost,
                    price_per_unit_cash=cash,
                    price_per_unit_insurance=ins,
                ),
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.info(f"{created_count} medicine(s) created, {skipped_count} skipped out of {len(medicines)} defined.")

    # ─── 10. ICD-10 Codes ─────────────────────────────────────

    def _seed_icd10_codes(self):
        from api.models import ICD10Code, ICD10Category

        self.section("ICD-10 Codes (Common Diagnoses)")

        if self.flush:
            ICD10Code.objects.all().delete()
            ICD10Category.objects.all().delete()
            self.info("Flushed ICD-10 codes and categories.")

        # Create ICD-10 categories (chapters)
        icd_categories = [
            ("I",    "A00-B99", "Certain infectious and parasitic diseases"),
            ("II",   "C00-D48", "Neoplasms"),
            ("III",  "D50-D89", "Diseases of the blood and blood-forming organs"),
            ("IV",   "E00-E90", "Endocrine, nutritional and metabolic diseases"),
            ("V",    "F00-F99", "Mental and behavioural disorders"),
            ("VI",   "G00-G99", "Diseases of the nervous system"),
            ("VII",  "H00-H59", "Diseases of the eye and adnexa"),
            ("VIII", "H60-H95", "Diseases of the ear and mastoid process"),
            ("IX",   "I00-I99", "Diseases of the circulatory system"),
            ("X",    "J00-J99", "Diseases of the respiratory system"),
            ("XI",   "K00-K93", "Diseases of the digestive system"),
            ("XII",  "L00-L99", "Diseases of the skin and subcutaneous tissue"),
            ("XIII", "M00-M99", "Diseases of the musculoskeletal system"),
            ("XIV",  "N00-N99", "Diseases of the genitourinary system"),
            ("XV",   "O00-O99", "Pregnancy, childbirth and the puerperium"),
            ("XVI",  "P00-P96", "Conditions originating in the perinatal period"),
            ("XVII", "Q00-Q99", "Congenital malformations and chromosomal abnormalities"),
            ("XVIII","R00-R99", "Symptoms, signs and abnormal clinical findings"),
            ("XIX",  "S00-T98", "Injury, poisoning and external causes"),
            ("XXI",  "Z00-Z99", "Factors influencing health status"),
        ]

        cat_map = {}
        for chapter, code_range, cat_name in icd_categories:
            cat, _ = ICD10Category.objects.get_or_create(
                chapter_number=chapter,
                defaults=dict(
                    code_range=code_range,
                    category_name=cat_name,
                    is_active=True,
                ),
            )
            cat_map[chapter] = cat

        # (code, chapter, short_desc, local_name, is_notifiable, nhif_eligible, is_common)
        codes = [
            # Infectious diseases
            ("A00.9",  "I",    "Cholera, unspecified",                        "Cholera",           True,  True,  True),
            ("A01.0",  "I",    "Typhoid fever",                               "Typhoid",           True,  True,  True),
            ("A06.0",  "I",    "Acute amoebic dysentery",                     "Amoebic Dysentery", False, True,  True),
            ("A09",    "I",    "Gastroenteritis and colitis",                 "Diarrhoea",         False, True,  True),
            ("A15.9",  "I",    "Respiratory tuberculosis, unspecified",       "TB (Respiratory)",  True,  True,  True),
            ("A16.9",  "I",    "Respiratory tuberculosis without bacteriol.", "TB (Suspected)",    True,  True,  True),

            # HIV
            ("B20",    "I",    "HIV disease",                                 "HIV/AIDS",          True,  True,  True),
            ("B24",    "I",    "Unspecified HIV disease",                     "HIV (Unspecified)", True,  True,  False),

            # Malaria
            ("B50.0",  "I",    "Plasmodium falciparum malaria with cerebral malaria", "Cerebral Malaria", True, True, True),
            ("B50.9",  "I",    "Plasmodium falciparum malaria, unspecified",  "Malaria (Falciparum)", True, True, True),
            ("B54",    "I",    "Unspecified malaria",                         "Malaria",           True,  True,  True),

            # Other infections
            ("B01.9",  "I",    "Varicella without complication (Chickenpox)", "Chickenpox",        False, True,  True),
            ("B05.9",  "I",    "Measles without complication",                "Measles",           True,  True,  True),

            # Endocrine
            ("E10.9",  "IV",   "Type 1 diabetes mellitus without complications", "DM Type 1",    False, True,  True),
            ("E11.9",  "IV",   "Type 2 diabetes mellitus without complications", "DM Type 2",    False, True,  True),
            ("E11.6",  "IV",   "Type 2 diabetes with other specified complications", "DM Complications", False, True, True),
            ("E03.9",  "IV",   "Hypothyroidism, unspecified",                 "Hypothyroidism",    False, True,  True),
            ("E05.9",  "IV",   "Thyrotoxicosis, unspecified",                 "Hyperthyroidism",   False, True,  False),
            ("E46",    "IV",   "Unspecified protein-energy malnutrition",     "Malnutrition",      False, True,  True),
            ("E43",    "IV",   "Severe protein-energy malnutrition",          "Severe Malnutrition", False, True, True),

            # Mental health
            ("F32.9",  "V",    "Depressive episode, unspecified",             "Depression",        False, True,  True),
            ("F20.9",  "V",    "Schizophrenia, unspecified",                  "Schizophrenia",     False, True,  False),

            # Cardiovascular
            ("I10",    "IX",   "Essential (primary) hypertension",            "Hypertension",      False, True,  True),
            ("I11.0",  "IX",   "Hypertensive heart disease with heart failure","Hypertensive HF",  False, True,  True),
            ("I21.9",  "IX",   "Acute myocardial infarction, unspecified",    "Heart Attack",      False, True,  True),
            ("I50.0",  "IX",   "Congestive heart failure",                    "CCF",               False, True,  True),
            ("I50.9",  "IX",   "Heart failure, unspecified",                  "Heart Failure",     False, True,  True),
            ("I63.9",  "IX",   "Cerebral infarction, unspecified",            "Stroke",            False, True,  True),
            ("I64",    "IX",   "Stroke, not specified as haemorrhage or infarction", "Stroke (Unspecified)", False, True, True),

            # Respiratory
            ("J00",    "X",    "Acute nasopharyngitis (common cold)",         "Common Cold",       False, True,  True),
            ("J02.9",  "X",    "Acute pharyngitis, unspecified",              "Sore Throat",       False, True,  True),
            ("J03.9",  "X",    "Acute tonsillitis, unspecified",              "Tonsillitis",       False, True,  True),
            ("J06.9",  "X",    "Acute upper respiratory infection, unspecified", "URTI",           False, True,  True),
            ("J11.1",  "X",    "Influenza with other respiratory manifestations", "Flu",           False, True,  True),
            ("J18.9",  "X",    "Pneumonia, unspecified organism",             "Pneumonia",         False, True,  True),
            ("J45.9",  "X",    "Asthma, unspecified",                         "Asthma",            False, True,  True),
            ("J96.9",  "X",    "Respiratory failure, unspecified",            "Resp. Failure",     False, True,  False),

            # Digestive
            ("K21.0",  "XI",   "Gastroesophageal reflux disease with oesophagitis", "GERD",       False, True,  True),
            ("K25.9",  "XI",   "Gastric ulcer, unspecified",                  "Peptic Ulcer",      False, True,  True),
            ("K29.7",  "XI",   "Gastritis, unspecified",                      "Gastritis",         False, True,  True),
            ("K35.9",  "XI",   "Acute appendicitis, unspecified",             "Appendicitis",      False, True,  True),
            ("K80.2",  "XI",   "Calculus of gallbladder without cholecystitis", "Gallstones",     False, True,  True),
            ("K92.1",  "XI",   "Melaena",                                     "Melaena",           False, True,  True),

            # Skin
            ("L02.9",  "XII",  "Cutaneous abscess, unspecified",              "Abscess/Boil",      False, True,  True),
            ("L03.9",  "XII",  "Cellulitis, unspecified",                     "Cellulitis",        False, True,  True),

            # Genitourinary
            ("N18.9",  "XIV",  "Chronic kidney disease, unspecified",         "CKD",               False, True,  True),
            ("N17.9",  "XIV",  "Acute renal failure, unspecified",            "ARF",               False, True,  True),
            ("N39.0",  "XIV",  "Urinary tract infection, site not specified", "UTI",               False, True,  True),
            ("N40",    "XIV",  "Benign prostatic hyperplasia",                "BPH",               False, True,  True),

            # Obstetrics
            ("O00.9",  "XV",   "Ectopic pregnancy, unspecified",              "Ectopic Pregnancy", False, True,  True),
            ("O14.0",  "XV",   "Mild to moderate pre-eclampsia",              "Pre-eclampsia (Mild)", False, True, True),
            ("O14.1",  "XV",   "Severe pre-eclampsia",                        "Pre-eclampsia (Severe)", False, True, True),
            ("O15.0",  "XV",   "Eclampsia in pregnancy",                      "Eclampsia",         False, True,  True),
            ("O20.0",  "XV",   "Threatened abortion",                         "Threatened Abortion", False, True, True),
            ("O72.1",  "XV",   "Other immediate postpartum haemorrhage",      "PPH",               False, True,  True),
            ("O80",    "XV",   "Encounter for full-term uncomplicated delivery", "Normal SVD",     False, True,  True),
            ("O82",    "XV",   "Encounter for caesarean delivery",            "C-Section",         False, True,  True),

            # Perinatal
            ("P07.3",  "XVI",  "Other preterm infants",                       "Prematurity",       False, True,  True),
            ("P21.9",  "XVI",  "Birth asphyxia, unspecified",                 "Birth Asphyxia",    False, True,  True),

            # Signs & Symptoms
            ("R00.0",  "XVIII","Tachycardia, unspecified",                    "Tachycardia",       False, False, True),
            ("R05",    "XVIII","Cough",                                        "Cough",             False, False, True),
            ("R50.9",  "XVIII","Fever, unspecified",                          "Fever",             False, True,  True),
            ("R51",    "XVIII","Headache",                                     "Headache",          False, False, True),

            # Injury / Trauma
            ("S00.9",  "XIX",  "Superficial injury of head, unspecified",     "Head Injury",       False, True,  True),
            ("S09.9",  "XIX",  "Unspecified injury of head",                  "Head Trauma",       False, True,  True),
            ("S52.9",  "XIX",  "Fracture of forearm, unspecified",            "Forearm Fracture",  False, True,  True),
            ("S72.9",  "XIX",  "Fracture of femur, unspecified",              "Femur Fracture",    False, True,  True),
            ("T14.0",  "XIX",  "Superficial injury of unspecified body region", "Wound (Minor)",   False, True,  True),
            ("T14.1",  "XIX",  "Open wound of unspecified body region",       "Open Wound",        False, True,  True),
            ("T30.0",  "XIX",  "Burn of unspecified degree",                  "Burn",              False, True,  True),

            # Preventive / Administrative
            ("Z00.0",  "XXI",  "Encounter for general adult examination",     "Routine Checkup",   False, True,  True),
            ("Z34.9",  "XXI",  "Encounter for supervision of normal pregnancy, unspecified", "ANC", False, True, True),
            ("Z38.0",  "XXI",  "Liveborn infant, born in hospital",           "Newborn",           False, True,  True),
            ("Z76.2",  "XXI",  "Encounter for health supervision of child",   "Child Clinic",      False, True,  True),
        ]

        created_count = 0
        skipped_count = 0

        for code, chapter, short_desc, local_name, notifiable, nhif, common in codes:
            if chapter not in cat_map:
                self.err(f"Chapter '{chapter}' not found for code {code}")
                continue

            _, created = ICD10Code.objects.get_or_create(
                code=code,
                defaults=dict(
                    category=cat_map[chapter],
                    description=short_desc,
                    short_description=short_desc[:200],
                    local_name=local_name,
                    is_notifiable=notifiable,
                    nhif_eligible=nhif,
                    is_common=common,
                    is_active=True,
                ),
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.info(f"{created_count} ICD-10 code(s) created, {skipped_count} skipped out of {len(codes)} defined.")

    # ─── Summary ──────────────────────────────────────────────

    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 58))
        self.stdout.write(self.style.SUCCESS("  Seed complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 58))
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("  Login credentials  (password: password123)"))
        self.stdout.write("")

        logins = [
            ("admin",        "Admin / Superuser"),
            ("receptionist", "Receptionist"),
            ("nurse1",       "Nurse"),
            ("doctor1",      "Doctor — General Medicine"),
            ("doctor2",      "Doctor — Paediatrics"),
            ("pharmacist1",  "Pharmacist"),
            ("cashier1",     "Cashier"),
            ("labtech1",     "Lab Technician"),
            ("insurance1",   "Insurance / Claims Officer"),
            ("procurement1", "Procurement Officer"),
            ("accountant1",  "Accountant"),
            ("hr1",          "HR Officer"),
        ]

        self.stdout.write(f"  {'Username':<16}  {'Role':<35}  Password")
        self.stdout.write(f"  {'-'*16}  {'-'*35}  {'-'*11}")
        for uname, role in logins:
            self.stdout.write(f"  {uname:<16}  {role:<35}  {PASSWORD}")

        self.stdout.write("")