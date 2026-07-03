from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid, random, string

class Role(models.Model):
    ROLE_CHOICES = [
        ("student","Student"),("staff","Staff"),
        ("maintenance_officer","Maintenance Officer"),("admin","Administrator"),
    ]
    name = models.CharField(max_length=30, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.get_name_display()

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email: raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    @property
    def full_name(self): return f"{self.first_name} {self.last_name}"
    def __str__(self): return f"{self.full_name} <{self.email}>"

class RequestCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: verbose_name_plural = "Request Categories"
    def __str__(self): return self.name

class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ("pending","Pending"),("assigned","Assigned"),("in_progress","In Progress"),
        ("completed","Completed"),("rejected","Rejected"),("cancelled","Cancelled"),
    ]
    PRIORITY_CHOICES = [
        ("low","Low"),("medium","Medium"),("high","High"),("urgent","Urgent"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(RequestCategory, on_delete=models.PROTECT, related_name="requests")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_requests")
    location = models.CharField(max_length=200)
    building = models.CharField(max_length=100, blank=True)
    room_number = models.CharField(max_length=20, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    evidence_image = models.ImageField(upload_to="evidence/", blank=True, null=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def _generate_ref(self):
        while True:
            ref = "SR" + "".join(random.choices(string.digits, k=8))
            if not ServiceRequest.objects.filter(reference_number=ref).exists():
                return ref
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_ref()
        super().save(*args, **kwargs)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.reference_number} — {self.title}"

class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, related_name="assignment")
    officer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_requests")
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignments_made")
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    def __str__(self): return f"{self.service_request.reference_number} -> {self.officer.full_name}"

class StatusUpdateLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="status_logs")
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="status_updates")
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.service_request.reference_number}: {self.old_status} -> {self.new_status}"

class Notification(models.Model):
    TYPE_CHOICES = [("info","Info"),("success","Success"),("warning","Warning"),("error","Error")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="info")
    is_read = models.BooleanField(default=False)
    reference_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"-> {self.user.email}: {self.title}"
