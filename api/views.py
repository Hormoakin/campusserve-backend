from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
import csv
from django.http import HttpResponse

from .models import Role, RequestCategory, ServiceRequest, Assignment, StatusUpdateLog, Notification
from .serializers import (
    RoleSerializer, UserSerializer, RegisterSerializer, ChangePasswordSerializer,
    RequestCategorySerializer, ServiceRequestSerializer, ServiceRequestCreateSerializer,
    StatusUpdateLogSerializer, NotificationSerializer,
)
from .permissions import IsAdmin, IsMaintenanceOfficer, IsAdminOrOfficer
from .pagination import StandardResultsSetPagination

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["role"] = user.role.name if user.role else None
        return token
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Registration successful. You may now log in.",
                         "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("role").all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["email","first_name","last_name","department"]
    filterset_fields = ["role__name","is_active"]

    def get_permissions(self):
        if self.action in ["list","destroy","stats"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["patch"], url_path="me/update")
    def update_me(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="me/change_password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Incorrect current password."}, status=400)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"message": "Password changed successfully."})

    @action(detail=False, methods=["get"])
    def maintenance_officers(self, request):
        officers = User.objects.filter(role__name="maintenance_officer", is_active=True).select_related("role")
        return Response(UserSerializer(officers, many=True).data)

    @action(detail=True, methods=["patch"])
    def toggle_active(self, request, pk=None):
        if not request.user.role or request.user.role.name != "admin":
            return Response({"detail": "Forbidden."}, status=403)
        user = self.get_object()
        if user == request.user:
            return Response({"detail": "You cannot deactivate your own account."}, status=400)
        user.is_active = not user.is_active
        user.save()
        return Response({"id": str(user.id), "is_active": user.is_active})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return Response({
            "total": User.objects.count(),
            "students": User.objects.filter(role__name="student").count(),
            "staff": User.objects.filter(role__name="staff").count(),
            "officers": User.objects.filter(role__name="maintenance_officer").count(),
            "admins": User.objects.filter(role__name="admin").count(),
            "active": User.objects.filter(is_active=True).count(),
            "inactive": User.objects.filter(is_active=False).count(),
        })

class RequestCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = RequestCategorySerializer
    def get_queryset(self):
        if (self.request.user.is_authenticated and self.request.user.role
                and self.request.user.role.name == "admin"):
            return RequestCategory.objects.all()
        return RequestCategory.objects.filter(is_active=True)
    def get_permissions(self):
        if self.action in ["list","retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]

class ServiceRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ["title","description","reference_number","location","building"]
    filterset_fields = ["status","priority","category"]
    ordering_fields = ["created_at","updated_at","priority","status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if not user.role: return ServiceRequest.objects.none()
        role = user.role.name
        qs = ServiceRequest.objects.select_related(
            "requester__role","category","assignment__officer","assignment__assigned_by"
        ).prefetch_related("status_logs__updated_by")
        if role == "admin": return qs.all()
        if role == "maintenance_officer":
            return qs.filter(Q(assignment__officer=user) | Q(status="pending")).distinct()
        return qs.filter(requester=user)

    def get_serializer_class(self):
        if self.action == "create": return ServiceRequestCreateSerializer
        return ServiceRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        full = ServiceRequestSerializer(serializer.instance, context={"request": request})
        return Response(full.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.action in ["update","partial_update","destroy"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def _notify(self, user, title, message, ref_id, ntype="info"):
        Notification.objects.create(user=user, title=title, message=message,
                                    notification_type=ntype, reference_id=ref_id)

    def perform_create(self, serializer):
        sr = serializer.save(requester=self.request.user)
        StatusUpdateLog.objects.create(
            service_request=sr, updated_by=self.request.user,
            old_status="", new_status="pending", comment="Service request submitted.")
        for admin in User.objects.filter(role__name="admin", is_active=True):
            self._notify(admin, "New Service Request",
                         f"New request {sr.reference_number}: {sr.title}", sr.id)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        if not request.user.role or request.user.role.name != "admin":
            return Response({"detail": "Only administrators can assign requests."}, status=403)
        sr = self.get_object()
        if sr.status in ["completed","rejected","cancelled"]:
            return Response({"detail": f"Cannot assign a request with status {sr.status!r}."}, status=400)
        officer_id = request.data.get("officer_id")
        if not officer_id:
            return Response({"detail": "officer_id is required."}, status=400)
        try:
            officer = User.objects.get(id=officer_id, role__name="maintenance_officer", is_active=True)
        except User.DoesNotExist:
            return Response({"detail": "Active maintenance officer not found."}, status=404)
        old_status = sr.status
        Assignment.objects.update_or_create(
            service_request=sr,
            defaults={"officer": officer, "assigned_by": request.user,
                      "notes": request.data.get("notes",""),
                      "expected_completion_date": request.data.get("expected_completion_date")})
        sr.status = "assigned"
        sr.save()
        StatusUpdateLog.objects.create(
            service_request=sr, updated_by=request.user,
            old_status=old_status, new_status="assigned",
            comment=f"Assigned to {officer.full_name}.")
        self._notify(officer, "New Assignment",
                     f"You have been assigned to {sr.reference_number}: {sr.title}.", sr.id)
        self._notify(sr.requester, "Request Assigned",
                     f"Your request {sr.reference_number} has been assigned.", sr.id)
        return Response(ServiceRequestSerializer(sr).data)

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        sr = self.get_object()
        user = request.user
        role = user.role.name if user.role else None
        new_status = request.data.get("status","").strip()
        comment = request.data.get("comment","").strip()
        if not new_status:
            return Response({"detail": "status is required."}, status=400)
        transitions = {
            "maintenance_officer": {
                "assigned": ["in_progress"], "in_progress": ["completed"]},
            "admin": {
                "pending": ["assigned","rejected"], "assigned": ["in_progress","rejected"],
                "in_progress": ["completed","rejected"]},
        }
        allowed = transitions.get(role, {}).get(sr.status, [])
        if new_status not in allowed:
            return Response({"detail": f"Cannot transition from {sr.status!r} to {new_status!r} as {role}."}, status=400)
        old_status = sr.status
        sr.status = new_status
        sr.save()
        StatusUpdateLog.objects.create(
            service_request=sr, updated_by=user, old_status=old_status,
            new_status=new_status, comment=comment or f"Status updated to {new_status}.")
        ntype = "success" if new_status == "completed" else ("error" if new_status == "rejected" else "info")
        label = new_status.replace("_"," ").title()
        self._notify(sr.requester, "Request Status Updated",
                     f"Your request {sr.reference_number} is now {label!r}.", sr.id, ntype)
        return Response(ServiceRequestSerializer(sr).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        user = request.user
        role = user.role.name if user.role else None
        if role == "admin": qs = ServiceRequest.objects.all()
        elif role == "maintenance_officer":
            qs = ServiceRequest.objects.filter(
                Q(assignment__officer=user) | Q(status="pending")).distinct()
        else: qs = ServiceRequest.objects.filter(requester=user)
        return Response({
            "total": qs.count(), "pending": qs.filter(status="pending").count(),
            "assigned": qs.filter(status="assigned").count(),
            "in_progress": qs.filter(status="in_progress").count(),
            "completed": qs.filter(status="completed").count(),
            "rejected": qs.filter(status="rejected").count(),
            "by_category": list(qs.values("category__name").annotate(count=Count("id")).order_by("-count")),
            "by_priority": list(qs.values("priority").annotate(count=Count("id")).order_by("-count")),
        })

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        if not request.user.role or request.user.role.name != "admin":
            return Response({"detail": "Only administrators can export data."}, status=403)
        filename = f"campusserve_requests_{timezone.now().date()}.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(["Reference","Title","Category","Requester","Location",
                         "Building","Room","Priority","Status","Assigned To","Created","Updated"])
        for r in ServiceRequest.objects.select_related("category","requester","assignment__officer").all():
            officer = (r.assignment.officer.full_name
                       if hasattr(r, "assignment") and r.assignment else "Unassigned")
            writer.writerow([r.reference_number, r.title, r.category.name,
                             r.requester.full_name, r.location, r.building, r.room_number,
                             r.get_priority_display(), r.get_status_display(), officer,
                             r.created_at.strftime("%Y-%m-%d %H:%M"),
                             r.updated_at.strftime("%Y-%m-%d %H:%M")])
        return response

class NotificationViewSet(viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get","patch","delete","head","options"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(NotificationSerializer(page, many=True).data)
        return Response(NotificationSerializer(qs, many=True).data)

    def partial_update(self, request, pk=None):
        notif = self.get_queryset().filter(pk=pk).first()
        if not notif: return Response(status=404)
        notif.is_read = request.data.get("is_read", notif.is_read)
        notif.save()
        return Response(NotificationSerializer(notif).data)

    def destroy(self, request, pk=None):
        notif = self.get_queryset().filter(pk=pk).first()
        if not notif: return Response(status=404)
        notif.delete()
        return Response(status=204)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": f"{updated} notification(s) marked as read."})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"count": count})
