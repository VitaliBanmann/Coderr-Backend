from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from orders_app.models import Order
from users_app.models import User


class OrderApiTests(APITestCase):
    """Test order endpoints and their role-based permissions."""

    def setUp(self):
        self.customer = User.objects.create_user(
            "order-customer", password="secure-pass", type=User.CUSTOMER
        )
        self.business = User.objects.create_user(
            "order-business", password="secure-pass", type=User.BUSINESS
        )
        offer = Offer.objects.create(
            user=self.business, title="Design", description="Design package"
        )
        self.detail = OfferDetail.objects.create(
            offer=offer,
            title="Basic design",
            revisions=2,
            delivery_time_in_days=5,
            price=150,
            features=["Logo"],
            offer_type="basic",
        )
        self.order = Order.objects.create(
            customer_user=self.customer,
            business_user=self.business,
            title=self.detail.title,
            revisions=self.detail.revisions,
            delivery_time_in_days=self.detail.delivery_time_in_days,
            price=self.detail.price,
            features=self.detail.features,
            offer_type=self.detail.offer_type,
        )

    def test_customer_creates_order_and_lists_only_their_own(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(
            "/api/orders/",
            {"offer_detail_id": self.detail.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        listing = self.client.get("/api/orders/")
        self.assertEqual(listing.data[0]["customer_user"], self.customer.pk)

    def test_business_updates_status_but_customer_cannot(self):
        self.assertEqual(str(self.order), "Basic design (in_progress)")
        self.client.force_authenticate(self.business)
        allowed = self.client.patch(
            f"/api/orders/{self.order.pk}/",
            {"status": "completed"},
            format="json",
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.data["status"], "completed")
        self.assertEqual(allowed.data["customer_user"], self.customer.pk)
        self.assertRegex(
            allowed.data["created_at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",
        )
        self.client.force_authenticate(self.customer)
        denied = self.client.patch(
            f"/api/orders/{self.order.pk}/",
            {"status": "cancelled"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

    def test_order_counts_track_status(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(f"/api/order-count/{self.business.pk}/")
        self.assertEqual(response.data["order_count"], 1)
        self.order.status = Order.Status.COMPLETED
        self.order.save()
        response = self.client.get(
            f"/api/completed-order-count/{self.business.pk}/"
        )
        self.assertEqual(response.data["completed_order_count"], 1)

    def test_orders_require_auth_and_hide_other_users_orders(self):
        self.assertEqual(self.client.get("/api/orders/").status_code, 401)
        stranger = User.objects.create_user(
            "order-stranger", password="secure-pass", type=User.CUSTOMER
        )
        self.client.force_authenticate(stranger)
        self.assertEqual(self.client.get("/api/orders/").data, [])
        self.assertEqual(
            self.client.get(f"/api/orders/{self.order.pk}/").status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                "/api/orders/", {"offer_detail_id": 999999}, format="json"
            ).status_code,
            400,
        )

    def test_order_status_validation_and_unknown_business_count(self):
        self.client.force_authenticate(self.business)
        invalid = self.client.patch(
            f"/api/orders/{self.order.pk}/",
            {"status": "unknown"},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(
            self.client.get("/api/order-count/999999/").status_code,
            404,
        )

    def test_business_cannot_create_orders_and_staff_can_delete(self):
        self.client.force_authenticate(self.business)
        denied = self.client.post(
            "/api/orders/",
            {"offer_detail_id": self.detail.pk},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
        staff = User.objects.create_superuser(
            "admin", "admin@example.test", "secure-pass"
        )
        self.client.force_authenticate(staff)
        deleted = self.client.delete(f"/api/orders/{self.order.pk}/")
        self.assertEqual(deleted.status_code, 204)
