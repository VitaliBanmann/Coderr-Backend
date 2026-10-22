from rest_framework.test import APITestCase

from offers_app.models import Offer
from reviews_app.models import Review
from users_app.models import User


class BaseInfoApiTests(APITestCase):
    """Test the public platform statistics endpoint."""

    def test_base_info_returns_platform_counts_and_average(self):
        customer = User.objects.create_user("stats-customer")
        business = User.objects.create_user(
            "stats-business", type=User.BUSINESS
        )
        Review.objects.create(
            reviewer=customer,
            business_user=business,
            rating=5,
            description="Great service",
        )
        Offer.objects.create(
            user=business,
            title="Stats offer",
            description="An offer for statistics tests.",
        )

        response = self.client.get("/api/base-info/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "review_count": 1,
                "average_rating": 5.0,
                "business_profile_count": 1,
                "offer_count": 1,
            },
        )

    def test_base_info_returns_zero_for_empty_review_average(self):
        response = self.client.get("/api/base-info/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["average_rating"], 0.0)
