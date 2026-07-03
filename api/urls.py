from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r"users",         views.UserViewSet,            basename="users")
router.register(r"requests",      views.ServiceRequestViewSet,  basename="requests")
router.register(r"categories",    views.RequestCategoryViewSet, basename="categories")
router.register(r"notifications", views.NotificationViewSet,    basename="notifications")

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(),              name="register"),
    path("auth/login/",    views.CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/",  TokenRefreshView.as_view(),                name="token_refresh"),
    path("", include(router.urls)),
]
