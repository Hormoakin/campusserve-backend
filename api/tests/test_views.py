from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Role, User, RequestCategory, ServiceRequest, Assignment


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role   = Role.objects.create(name="student")

    def test_register_success(self):
        res = self.client.post("/api/auth/register/", {
            "email": "new@uni.edu", "first_name": "New", "last_name": "User",
            "role_id": self.role.id, "password": "StrongP@ss1",
            "confirm_password": "StrongP@ss1",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", res.data)
        self.assertEqual(res.data["user"]["email"], "new@uni.edu")

    def test_register_password_mismatch(self):
        res = self.client.post("/api/auth/register/", {
            "email": "x@uni.edu", "first_name": "X", "last_name": "Y",
            "role_id": self.role.id, "password": "abc12345",
            "confirm_password": "different",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email="dup@uni.edu", password="pass1234",
            first_name="D", last_name="U", role=self.role,
        )
        res = self.client.post("/api/auth/register/", {
            "email": "dup@uni.edu", "first_name": "D", "last_name": "U",
            "role_id": self.role.id, "password": "pass1234",
            "confirm_password": "pass1234",
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(
            email="u@uni.edu", password="pass1234",
            first_name="U", last_name="User", role=self.role,
        )
        res = self.client.post("/api/auth/login/", {
            "email": "u@uni.edu", "password": "pass1234"
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access",  res.data)
        self.assertIn("refresh", res.data)
        self.assertIn("user",    res.data)
        self.assertEqual(res.data["user"]["role"]["name"], "student")

    def test_login_wrong_password(self):
        User.objects.create_user(
            email="w@uni.edu", password="correct",
            first_name="W", last_name="User", role=self.role,
        )
        res = self.client.post("/api/auth/login/", {
            "email": "w@uni.edu", "password": "wrong"
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_rejected(self):
        res = self.client.get("/api/requests/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ServiceRequestTests(TestCase):
    def setUp(self):
        self.client       = APIClient()
        self.student_role = Role.objects.create(name="student")
        self.admin_role   = Role.objects.create(name="admin")
        self.officer_role = Role.objects.create(name="maintenance_officer")
        self.cat          = RequestCategory.objects.create(name="Electricity")
        self.student = User.objects.create_user(
            email="s@uni.edu", password="pass1234",
            first_name="Student", last_name="One", role=self.student_role,
        )
        self.admin = User.objects.create_user(
            email="a@uni.edu", password="pass1234",
            first_name="Admin", last_name="One", role=self.admin_role,
        )
        self.officer = User.objects.create_user(
            email="o@uni.edu", password="pass1234",
            first_name="Officer", last_name="One", role=self.officer_role,
        )

    def _make_request(self, user=None):
        u = user or self.student
        self.client.force_authenticate(user=u)
        return self.client.post("/api/requests/", {
            "title": "AC broken in Lab 3",
            "description": "The air conditioning unit stopped working.",
            "category_id": self.cat.id,
            "location": "Lab 3, Engineering Block",
            "priority": "high",
        })

    def test_create_request_as_student(self):
        res = self._make_request()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "pending")
        self.assertTrue(res.data["reference_number"].startswith("SR"))
        self.assertEqual(len(res.data["reference_number"]), 10)

    def test_status_log_created_on_submit(self):
        res = self._make_request()
        self.assertEqual(len(res.data["status_logs"]), 1)
        self.assertEqual(res.data["status_logs"][0]["new_status"], "pending")

    def test_student_cannot_see_others_requests(self):
        other = User.objects.create_user(
            email="other@uni.edu", password="pass1234",
            first_name="Other", last_name="Student", role=self.student_role,
        )
        ServiceRequest.objects.create(
            title="Other request",
            description="Something needs fixing here in block B.",
            category=self.cat, requester=other,
            location="Block C", priority="low",
        )
        self.client.force_authenticate(user=self.student)
        res = self.client.get("/api/requests/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 0)

    def test_admin_sees_all_requests(self):
        self._make_request(self.student)
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/requests/")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.data["count"], 1)

    def test_admin_assigns_request(self):
        create_res = self._make_request()
        req_id     = create_res.data["id"]
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(f"/api/requests/{req_id}/assign/", {
            "officer_id": str(self.officer.id),
            "notes": "Please handle urgently.",
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "assigned")
        self.assertEqual(res.data["assignment"]["officer"]["email"], "o@uni.edu")

    def test_officer_updates_to_in_progress(self):
        sr = ServiceRequest.objects.create(
            title="T", description="Desc long enough for the test to pass here.",
            category=self.cat, requester=self.student,
            location="Block A", priority="medium", status="assigned",
        )
        Assignment.objects.create(
            service_request=sr, officer=self.officer, assigned_by=self.admin,
        )
        self.client.force_authenticate(user=self.officer)
        res = self.client.post(
            f"/api/requests/{sr.id}/update_status/",
            {"status": "in_progress", "comment": "Started work."},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "in_progress")

    def test_invalid_status_transition_rejected(self):
        sr = ServiceRequest.objects.create(
            title="T2", description="Desc long enough for the test to pass here two.",
            category=self.cat, requester=self.student,
            location="Block A", priority="medium", status="pending",
        )
        self.client.force_authenticate(user=self.officer)
        res = self.client.post(
            f"/api/requests/{sr.id}/update_status/",
            {"status": "completed"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_csv_requires_admin(self):
        self.client.force_authenticate(user=self.student)
        res = self.client.get("/api/requests/export_csv/")
        self.assertEqual(res.status_code, 403)

    def test_export_csv_works_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/requests/export_csv/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/csv")

    def test_stats_endpoint(self):
        self._make_request()
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/requests/stats/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total",       res.data)
        self.assertIn("pending",     res.data)
        self.assertIn("completed",   res.data)
        self.assertIn("by_category", res.data)

    def test_search_requests(self):
        self._make_request()
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/requests/?search=AC+broken")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.data["count"], 1)

    def test_filter_by_status(self):
        self._make_request()
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/requests/?status=pending")
        self.assertEqual(res.status_code, 200)
        for r in res.data["results"]:
            self.assertEqual(r["status"], "pending")
