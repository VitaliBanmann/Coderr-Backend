from django.db.models import Avg
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from reviews_app.models import Review
from users_app.models import User


class BaseInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rating = Review.objects.aggregate(average=Avg("rating"))["average"]
        return Response(
            {
                "review_count": Review.objects.count(),
                "average_rating": (
                    round(rating, 1) if rating is not None else 0.0
                ),
                "business_profile_count": User.objects.filter(
                    type=User.BUSINESS
                ).count(),
                "offer_count": Offer.objects.count(),
            }
        )
