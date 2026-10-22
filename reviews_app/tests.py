from rest_framework.test import APITestCase

from reviews_app.models import Review
from users_app.models import User


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            "review-customer", password="secure-pass", type=User.CUSTOMER
        )
        self.business = User.objects.create_user(
            "review-business", password="secure-pass", type=User.BUSINESS
        )

    def test_customer_creates_review_once_and_author_edits(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(
            "/api/reviews/",
            {
                "business_user": self.business.pk,
                "rating": 4,
                "description": "Great work",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self._assert_utc_timestamps(response.data)
        duplicate = self.client.post(
            "/api/reviews/",
            {
                "business_user": self.business.pk,
                "rating": 5,
                "description": "Another review",
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        review = Review.objects.get()
        updated = self.client.patch(
            f"/api/reviews/{review.pk}/",
            {"rating": 5},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["rating"], 5)
        self._assert_utc_timestamps(updated.data)
        detail = self.client.get(f"/api/reviews/{review.pk}/")
        listing = self.client.get("/api/reviews/")
        self._assert_utc_timestamps(detail.data)
        self._assert_utc_timestamps(listing.data[0])
        immutable_business = self.client.patch(
            f"/api/reviews/{review.pk}/",
            {"business_user": self.customer.pk},
            format="json",
        )
        self.assertEqual(immutable_business.status_code, 400)

    def _assert_utc_timestamps(self, data):
        pattern = (
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
        )
        for field in ("created_at", "updated_at"):
            self.assertRegex(data[field], pattern)

    def test_business_cannot_review_and_only_author_deletes(self):
        review = Review.objects.create(
            reviewer=self.customer,
            business_user=self.business,
            rating=4,
            description="Good work",
        )
        self.client.force_authenticate(self.business)
        denied_create = self.client.post(
            "/api/reviews/",
            {
                "business_user": self.business.pk,
                "rating": 3,
                "description": "Review",
            },
            format="json",
        )
        self.assertEqual(denied_create.status_code, 403)
        denied_delete = self.client.delete(f"/api/reviews/{review.pk}/")
        self.assertEqual(denied_delete.status_code, 403)

    def test_reviews_are_filterable_and_base_info_is_public(self):
        Review.objects.create(
            reviewer=self.customer,
            business_user=self.business,
            rating=5,
            description="Excellent",
        )
        self.client.force_authenticate(self.customer)
        filtered = self.client.get(
            f"/api/reviews/?business_user_id={self.business.pk}"
            "&ordering=rating"
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(len(filtered.data), 1)
        self.client.force_authenticate(user=None)
        stats = self.client.get("/api/base-info/")
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.data["average_rating"], 5.0)

    def test_review_filters_and_rating_validation(self):
        self.client.force_authenticate(self.customer)
        invalid_filter = self.client.get("/api/reviews/?reviewer_id=invalid")
        self.assertEqual(invalid_filter.status_code, 400)
        invalid_ordering = self.client.get("/api/reviews/?ordering=created_at")
        self.assertEqual(invalid_ordering.status_code, 400)
        invalid_rating = self.client.post(
            "/api/reviews/",
            {
                "business_user": self.business.pk,
                "rating": 6,
                "description": "Out of range",
            },
            format="json",
        )
        self.assertEqual(invalid_rating.status_code, 400)

    def test_review_author_can_delete_and_empty_stats_are_zero(self):
        review = Review.objects.create(
            reviewer=self.customer,
            business_user=self.business,
            rating=3,
            description="Okay",
        )
        self.assertEqual(str(review), "3/5 for review-business")
        self.client.force_authenticate(self.customer)
        self.assertEqual(
            self.client.delete(f"/api/reviews/{review.pk}/").status_code,
            204,
        )
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get("/api/base-info/").data["average_rating"],
            0.0,
        )
