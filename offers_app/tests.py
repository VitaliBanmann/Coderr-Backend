from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail
from users_app.models import User


def offer_payload():
    return {
        "title": "API testing",
        "description": "Searchable test description",
        "details": [
            {
                "title": package.title(),
                "revisions": 2,
                "delivery_time_in_days": days,
                "price": price,
                "features": ["Feature one"],
                "offer_type": package,
            }
            for package, price, days in [
                ("basic", 100, 5),
                ("standard", 200, 7),
                ("premium", 500, 10),
            ]
        ],
    }


class OfferApiTests(APITestCase):
    def setUp(self):
        self.business = User.objects.create_user(
            "offer-owner", password="secure-pass", type=User.BUSINESS
        )
        self.customer = User.objects.create_user(
            "offer-customer", password="secure-pass", type=User.CUSTOMER
        )

    def test_business_creates_offer_and_public_list_is_paginated(self):
        self.client.force_authenticate(self.business)
        created = self.client.post(
            "/api/offers/", offer_payload(), format="json"
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(len(created.data["details"]), 3)
        details = OfferDetail.objects.filter(offer_id=created.data["id"])
        self.assertEqual(details.count(), 3)
        self.client.force_authenticate(user=None)
        listing = self.client.get(
            "/api/offers/?search=testing"
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data["count"], 1)
        result = listing.data["results"][0]
        self.assertEqual(result["min_price"], 100.0)
        self.assertEqual(result["min_delivery_time"], 5)

    def test_customers_cannot_create_and_only_owner_can_edit(self):
        offer = self._create_offer()
        self.client.force_authenticate(self.customer)
        denied_create = self.client.post(
            "/api/offers/", offer_payload(), format="json"
        )
        self.assertEqual(denied_create.status_code, 403)
        denied_update = self.client.patch(
            f"/api/offers/{offer.pk}/", {"title": "Changed"}, format="json"
        )
        self.assertEqual(denied_update.status_code, 403)

    def test_partial_detail_update_preserves_detail_id(self):
        offer = self._create_offer()
        detail = offer.details.get(offer_type="basic")
        self.client.force_authenticate(self.business)
        response = self.client.patch(
            f"/api/offers/{offer.pk}/",
            {
                "details": [
                    {
                        "id": detail.pk,
                        "offer_type": "basic",
                        "title": "Updated basic",
                        "revisions": 3,
                        "delivery_time_in_days": 6,
                        "price": "120.00",
                        "features": ["Updated feature"],
                    }
                ]
            },
            format="json",
        )
        detail.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(detail.pk, response.data["details"][0]["id"])
        self.assertEqual(detail.title, "Updated basic")
        response = self.client.patch(
            f"/api/offers/{offer.pk}/",
            {
                "details": [
                    {"offer_type": "basic", "title": "Updated by type"}
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["details"][0]["id"], detail.pk)
        detail.refresh_from_db()
        self.assertEqual(detail.title, "Updated by type")
        response = self.client.patch(
            f"/api/offers/{offer.pk}/",
            {
                "details": [
                    {
                        "id": detail.pk,
                        "title": "Updated without offer type",
                    }
                ]
            },
            format="json",
        )
        detail.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(detail.title, "Updated by type")

    def test_offer_detail_requires_authentication(self):
        offer = self._create_offer()
        response = self.client.get(f"/api/offers/{offer.pk}/")
        self.assertEqual(response.status_code, 401)

    def test_offer_filters_detail_lookup_and_owner_delete(self):
        offer = self._create_offer()
        self.assertEqual(str(offer), "API testing")
        self.assertEqual(str(offer.details.first()), "API testing (basic)")
        listing = self.client.get("/api/offers/")
        self.assertRegex(
            listing.data["results"][0]["created_at"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$",
        )
        frontend_query = self.client.get(
            "/api/offers/?creator_id=&search=&ordering=&page=1"
            "&max_delivery_time="
        )
        self.assertEqual(frontend_query.status_code, 200)
        self.assertEqual(frontend_query.data["count"], 1)
        query = (
            f"/api/offers/?creator_id={self.business.pk}"
            "&min_price=100&max_delivery_time=5&ordering=min_price"
        )
        listing = self.client.get(query)
        self.assertEqual(listing.data["count"], 1)
        details = self.client.get(
            f"/api/offerdetails/{offer.details.first().pk}/"
        )
        self.client.force_authenticate(self.customer)
        self.assertEqual(details.status_code, 401)
        self.client.force_authenticate(self.business)
        offer_detail = self.client.get(f"/api/offers/{offer.pk}/")
        self.assertEqual(offer_detail.status_code, 200)
        self.assertEqual(len(offer_detail.data["details"]), 3)
        details = self.client.get(
            f"/api/offerdetails/{offer.details.first().pk}/"
        )
        self.assertEqual(details.data["price"], 100.0)
        deleted = self.client.delete(f"/api/offers/{offer.pk}/")
        self.assertEqual(deleted.status_code, 204)

    def test_offer_page_size_query_parameter_limits_results(self):
        self._create_offer()
        self._create_offer()
        response = self.client.get("/api/offers/?page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)

    def test_offer_filters_and_missing_or_foreign_details_are_rejected(self):
        offer = self._create_offer()
        invalid_queries = [
            "/api/offers/?creator_id=bad",
            "/api/offers/?creator_id=-1",
            "/api/offers/?min_price=NaN",
            "/api/offers/?min_price=-1",
            "/api/offers/?max_delivery_time=bad",
            "/api/offers/?max_delivery_time=-1",
            "/api/offers/?ordering=title",
        ]
        for query in invalid_queries:
            with self.subTest(query=query):
                self.assertEqual(self.client.get(query).status_code, 400)
        self.client.force_authenticate(self.business)
        missing_details = self.client.post(
            "/api/offers/",
            {"title": "Missing packages", "description": "Incomplete"},
            format="json",
        )
        self.assertEqual(missing_details.status_code, 400)
        foreign_update = self.client.patch(
            f"/api/offers/{offer.pk}/",
            {
                "details": [
                    {
                        "id": 999999,
                        "offer_type": "basic",
                        "title": "Not this offer",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(foreign_update.status_code, 400)
        mismatched_update = self.client.patch(
            f"/api/offers/{offer.pk}/",
            {
                "details": [
                    {
                        "id": offer.details.get(offer_type="basic").pk,
                        "offer_type": "standard",
                        "title": "Mismatched detail",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(mismatched_update.status_code, 400)
        invalid_details = offer_payload()
        invalid_details["details"][0]["revisions"] = -2
        self.assertEqual(
            self.client.post(
                "/api/offers/", invalid_details, format="json"
            ).status_code,
            400,
        )
        invalid_details = offer_payload()
        invalid_details["details"][0]["features"] = "not-a-list"
        self.assertEqual(
            self.client.post(
                "/api/offers/", invalid_details, format="json"
            ).status_code,
            400,
        )
        invalid_details = offer_payload()
        invalid_details["details"][1]["offer_type"] = "basic"
        self.assertEqual(
            self.client.post(
                "/api/offers/", invalid_details, format="json"
            ).status_code,
            400,
        )
        invalid_details = offer_payload()
        invalid_details["details"][0]["id"] = 9
        self.assertEqual(
            self.client.post(
                "/api/offers/", invalid_details, format="json"
            ).status_code,
            400,
        )

    def _create_offer(self):
        payload = offer_payload()
        offer = Offer.objects.create(
            user=self.business,
            title=payload["title"],
            description=payload["description"],
        )
        for detail in payload["details"]:
            OfferDetail.objects.create(offer=offer, **detail)
        return offer
