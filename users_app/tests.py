from datetime import datetime, timezone
from unittest.mock import patch

from django.core.management import call_command
from rest_framework.test import APITestCase

from users_app.models import User


class AuthenticationAndProfileTests(APITestCase):
    def test_registration_and_login_return_token(self):
        response = self.client.post(
            "/api/registration/",
            {
                "username": "new-customer",
                "email": "customer@example.test",
                "password": "A-valid-password-2026!",
                "repeated_password": "A-valid-password-2026!",
                "type": "customer",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        login = self.client.post(
            "/api/login/",
            {"username": "new-customer", "password": "A-valid-password-2026!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["user_id"], response.data["user_id"])

    def test_registration_rejects_password_mismatch(self):
        response = self.client.post(
            "/api/registration/",
            {
                "username": "mismatch",
                "email": "mismatch@example.test",
                "password": "A-valid-password-2026!",
                "repeated_password": "not-the-same",
                "type": "customer",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        weak_password = self.client.post(
            "/api/registration/",
            {
                "username": "weak-user",
                "email": "weak@example.test",
                "password": "password",
                "repeated_password": "password",
                "type": "customer",
            },
            format="json",
        )
        self.assertEqual(weak_password.status_code, 400)

    def test_login_rejects_wrong_password_and_profile_get_requires_auth(self):
        user = User.objects.create_user(
            "login-user", password="secure-pass", type=User.CUSTOMER
        )
        login = self.client.post(
            "/api/login/",
            {"username": user.username, "password": "incorrect"},
            format="json",
        )
        self.assertEqual(login.status_code, 400)
        profile = self.client.get(f"/api/profile/{user.pk}/")
        self.assertEqual(profile.status_code, 401)

    def test_profile_is_private_and_owner_can_update(self):
        owner = User.objects.create_user(
            "profile-owner", password="secure-pass", type=User.BUSINESS
        )
        other = User.objects.create_user(
            "other-user", password="secure-pass", type=User.CUSTOMER
        )
        owner.type = User.CUSTOMER
        owner.save(update_fields=["type"])
        self.assertEqual(str(owner), "profile-owner")
        self.client.force_authenticate(owner)
        profile = self.client.get(f"/api/profile/{owner.pk}/")
        self.assertEqual(profile.status_code, 200)
        self.assertRegex(
            profile.data["created_at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",
        )
        response = self.client.patch(
            f"/api/profile/{owner.pk}/",
            {"location": "Berlin"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["location"], "Berlin")
        self.assertRegex(
            response.data["created_at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",
        )
        self.assertEqual(response.data["first_name"], "")
        denied = self.client.patch(
            f"/api/profile/{other.pk}/",
            {"location": "Hamburg"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

    def test_profile_lists_are_unpaginated(self):
        User.objects.create_user("business", type=User.BUSINESS)
        self.client.force_authenticate(
            User.objects.create_user("customer", type=User.CUSTOMER)
        )
        response = self.client.get("/api/profiles/business/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(
            set(response.data[0]),
            {
                "user",
                "username",
                "first_name",
                "last_name",
                "file",
                "location",
                "tel",
                "description",
                "working_hours",
                "type",
            },
        )

    def test_customer_profile_list_formats_image_upload_timestamp(self):
        customer = User.objects.create_user(
            "customer-with-image", type=User.CUSTOMER
        )
        customer.profile_image.name = "profiles/avatar.jpg"
        customer.save(update_fields=["profile_image"])
        self.client.force_authenticate(customer)
        uploaded_at = datetime(2023, 9, 15, 9, tzinfo=timezone.utc)
        with patch(
            "django.core.files.storage.FileSystemStorage.get_modified_time",
            return_value=uploaded_at,
        ):
            response = self.client.get("/api/profiles/customer/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data[0]),
            {
                "user",
                "username",
                "first_name",
                "last_name",
                "file",
                "uploaded_at",
                "type",
            },
        )
        self.assertEqual(
            response.data[0]["uploaded_at"], "2023-09-15T09:00:00"
        )

    def test_demo_seed_creates_frontend_guest_accounts_and_is_repeatable(self):
        call_command("seed_demo")
        call_command("seed_demo")
        self.assertTrue(
            User.objects.get(username="andrey").check_password("asdasd")
        )
        self.assertTrue(
            User.objects.get(username="kevin").check_password("asdasd24")
        )
