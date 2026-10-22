from django.core.management.base import BaseCommand

from offers_app.models import Offer, OfferDetail
from users_app.models import User


DEMO_PACKAGES = (
    ("basic", 100, 5),
    ("standard", 200, 7),
    ("premium", 500, 10),
)


SELLER_OFFERS = (
    (
        "Website Development",
        "Responsive websites with HTML, CSS and JavaScript.",
        ((100, 5, 2), (200, 7, 3), (350, 10, 5)),
    ),
    (
        "REST API with Django",
        "Backend APIs built with Django REST Framework.",
        ((150, 5, 2), (300, 8, 3), (500, 12, 5)),
    ),
    (
        "Logo and Branding",
        "Logo design and a simple brand guide.",
        ((50, 3, 1), (120, 5, 2), (250, 7, 4)),
    ),
)
PACKAGE_TYPES = ("basic", "standard", "premium")


class Command(BaseCommand):
    help = "Create local-only Coderr demo accounts and sample offers."

    def handle(self, *args, **options):
        self._create_seller_offers()
        self._create_demo_user(
            "andrey", "asdasd", "customer", "andrey@example.test"
        )
        business = self._create_demo_user(
            "kevin", "asdasd24", "business", "kevin@example.test"
        )
        self._create_demo_offer(business)
        self.stdout.write(
            self.style.SUCCESS("Created local Coderr demo data.")
        )

    def _create_seller_offers(self):
        seller = self._create_demo_user(
            "VitaliBanmannSeller",
            "asdasd24",
            "business",
            "seller@example.test",
        )
        for title, description, packages in SELLER_OFFERS:
            self._create_seller_offer(
                seller, title, description, packages
            )

    def _create_seller_offer(self, seller, title, description, packages):
        if Offer.objects.filter(user=seller, title=title).exists():
            return
        offer = Offer.objects.create(
            user=seller, title=title, description=description
        )
        for kind, values in zip(PACKAGE_TYPES, packages):
            self._create_seller_package(offer, kind, values)

    def _create_seller_package(self, offer, kind, values):
        price, days, revisions = values
        OfferDetail.objects.create(
            offer=offer,
            offer_type=kind,
            title=kind.title(),
            revisions=revisions,
            delivery_time_in_days=days,
            price=price,
            features=["Feature A", "Feature B"],
        )

    def _create_demo_user(self, username, password, user_type, email):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "type": user_type},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

    def _create_demo_offer(self, business):
        if Offer.objects.filter(user=business).exists():
            return
        offer = Offer.objects.create(
            user=business,
            title="Demo web development",
            description="A sample freelancer offer for local testing.",
        )
        self._create_demo_packages(offer)

    def _create_demo_packages(self, offer):
        for package, price, days in DEMO_PACKAGES:
            self._create_demo_package(offer, package, price, days)

    def _create_demo_package(self, offer, package, price, days):
        OfferDetail.objects.create(
            offer=offer,
            offer_type=package,
            title=f"{package.title()} web package",
            revisions=2,
            delivery_time_in_days=days,
            price=price,
            features=["Web development", "Responsive layout"],
        )
