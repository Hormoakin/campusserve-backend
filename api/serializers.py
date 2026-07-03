from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Role, RequestCategory, ServiceRequest, Assignment, StatusUpdateLog, Notification

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False)
    full_name = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = ["id","email","first_name","last_name","phone","role","role_id",
                  "department","is_active","date_joined","full_name"]
        read_only_fields = ["id","date_joined"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source="role")
    class Meta:
        model = User
        fields = ["email","first_name","last_name","phone","department","role_id","password","confirm_password"]
    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()
    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)
    def validate(self, data):
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError({"new_password": "New passwords do not match."})
        return data

class RequestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestCategory
        fields = ["id","name","description","icon","is_active"]

class StatusUpdateLogSerializer(serializers.ModelSerializer):
    updated_by = UserSerializer(read_only=True)
    class Meta:
        model = StatusUpdateLog
        fields = ["id","old_status","new_status","comment","updated_by","created_at"]

class AssignmentSerializer(serializers.ModelSerializer):
    officer = UserSerializer(read_only=True)
    assigned_by = UserSerializer(read_only=True)
    class Meta:
        model = Assignment
        fields = ["id","officer","assigned_by","assigned_at","notes","expected_completion_date"]

class ServiceRequestSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    category = RequestCategorySerializer(read_only=True)
    assignment = AssignmentSerializer(read_only=True)
    status_logs = StatusUpdateLogSerializer(many=True, read_only=True)
    class Meta:
        model = ServiceRequest
        fields = ["id","reference_number","title","description","category","requester",
                  "location","building","room_number","priority","status","evidence_image",
                  "admin_notes","assignment","status_logs","created_at","updated_at"]
        read_only_fields = ["id","reference_number","requester","status","created_at","updated_at"]

class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=RequestCategory.objects.filter(is_active=True), source="category")
    class Meta:
        model = ServiceRequest
        fields = ["title","description","category_id","location","building","room_number","priority","evidence_image"]
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value
    def validate_description(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Please provide more detail (min 20 characters).")
        return value

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id","title","message","notification_type","is_read","reference_id","created_at"]
