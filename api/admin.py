from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, RequestCategory, ServiceRequest, Assignment, StatusUpdateLog, Notification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone", "department")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Dates", {"fields": ("date_joined",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": (
            "email", "first_name", "last_name", "role", "password1", "password2"
        )}),
    )

admin.site.register(Role)

@admin.register(RequestCategory)
class RequestCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "icon", "is_active", "created_at"]

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ["reference_number", "title", "category", "requester", "priority", "status", "created_at"]
    list_filter = ["status", "priority", "category"]
    search_fields = ["reference_number", "title", "requester__email"]
    readonly_fields = ["reference_number", "created_at", "updated_at"]

admin.site.register(Assignment)
admin.site.register(StatusUpdateLog)
admin.site.register(Notification)
