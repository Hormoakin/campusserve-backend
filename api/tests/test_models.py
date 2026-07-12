from django.test import TestCase
from api.models import Role, User, RequestCategory, ServiceRequest


class TestUserModel(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="student")

    def test_create_user(self):
        user = User.objects.create_user(
            email="test@uni.edu", password="pass1234",
            first_name="Test", last_name="User", role=self.role,
        )
        self.assertEqual(user.email, "test@uni.edu")
        self.assertTrue(user.check_password("pass1234"))
        self.assertEqual(user.full_name, "Test User")

    def test_email_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass1234")

    def test_full_name_property(self):
        user = User.objects.create_user(
            email="fn@uni.edu", password="pass1234",
            first_name="Ahmed", last_name="Salman", role=self.role,
        )
        self.assertEqual(user.full_name, "Ahmed Salman")

    def test_default_is_active(self):
        user = User.objects.create_user(
            email="active@uni.edu", password="pass1234",
            first_name="A", last_name="B", role=self.role,
        )
        self.assertTrue(user.is_active)


class TestServiceRequestModel(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="student")
        self.cat  = RequestCategory.objects.create(name="Electricity")
        self.user = User.objects.create_user(
            email="s@uni.edu", password="pass1234",
            first_name="Student", last_name="One", role=self.role,
        )

    def test_reference_number_auto_generated(self):
        sr = ServiceRequest.objects.create(
            title="Broken light",
            description="Light out in corridor block A",
            category=self.cat, requester=self.user,
            location="Block A", priority="medium",
        )
        self.assertTrue(sr.reference_number.startswith("SR"))
        self.assertEqual(len(sr.reference_number), 10)

    def test_default_status_is_pending(self):
        sr = ServiceRequest.objects.create(
            title="Leaking tap",
            description="Toilet tap is dripping constantly",
            category=self.cat, requester=self.user,
            location="Block B", priority="high",
        )
        self.assertEqual(sr.status, "pending")

    def test_reference_numbers_are_unique(self):
        sr1 = ServiceRequest.objects.create(
            title="Issue 1",
            description="Description long enough to pass validation here",
            category=self.cat, requester=self.user,
            location="Block A", priority="low",
        )
        sr2 = ServiceRequest.objects.create(
            title="Issue 2",
            description="Another description long enough for this test case",
            category=self.cat, requester=self.user,
            location="Block B", priority="low",
        )
        self.assertNotEqual(sr1.reference_number, sr2.reference_number)
