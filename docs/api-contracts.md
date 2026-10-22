# Implemented API contract

The source of truth is the supplied Coderr API endpoint document. The routes below are relative to `/api/`. Unless stated otherwise, protected routes require a DRF token in `Authorization: Token <token>`.

Timestamp fields use ISO-8601 UTC values with a trailing `Z`. The customer
profile-list field `uploaded_at` is the stored profile image's modification
time, formatted as `YYYY-MM-DDTHH:mm:ss` without a timezone suffix; it is null
when no profile image is set.

## Authentication and profiles

- `POST registration/`: creates a customer or business account; `username`, `email`, `password`, `repeated_password` and `type` are required. Returns a token and user identity with `201`.
- `POST login/`: authenticates with `username` and `password`; returns a token and user identity with `200`.
- `GET profile/{pk}/`: retrieves an authenticated user's profile. `PATCH` is restricted to the profile owner. Empty profile text fields serialize as empty strings; uploaded profile images use `file`.
- `GET profiles/business/`: authenticated, unpaginated profile arrays with `user`, `username`, names, image, and business profile fields.
- `GET profiles/customer/`: authenticated, unpaginated profile arrays with `user`, `username`, names, image, `uploaded_at`, and `type`.

## Offers

- `GET offers/`: public page-number-paginated results (six per page by default, configurable with `page_size` up to 100), with `creator_id`, `min_price`, `max_delivery_time`, `search`, and `ordering` filters. Results include absolute package-detail links, the lowest price, the shortest delivery time, and creator information.
- `POST offers/`: business users only. A new offer must provide exactly one each of `basic`, `standard`, and `premium` package details.
- `GET offers/{id}/`: authenticated offer detail. `PATCH` and `DELETE` are restricted to its owner. Nested partial updates preserve detail IDs; each updated detail must include its `offer_type`, and may include its ID.
- `GET offerdetails/{id}/`: authenticated package detail.

## Orders

- `GET orders/`: returns only orders belonging to the authenticated customer or business user.
- `POST orders/`: customer users only; accepts `offer_detail_id` and snapshots the selected package into a new `in_progress` order.
- `GET orders/{id}/`: authenticated order detail.
- `PATCH orders/{id}/`: only the owning business user may update `status` (`in_progress`, `completed` or `cancelled`).
- `DELETE orders/{id}/`: staff users only; returns `204`.
- `GET order-count/{business_user_id}/` and `GET completed-order-count/{business_user_id}/`: authenticated counts for the corresponding business profile.

## Reviews and platform statistics

- `GET reviews/`: authenticated list, filterable by `business_user_id` and `reviewer_id`, sortable by `updated_at` or `rating`.
- `POST reviews/`: authenticated customer users only. A customer may review a business profile once; the reviewer identity comes from the token.
- `GET reviews/{id}/`: authenticated detail. `PATCH` and `DELETE` are restricted to the review author; deletion returns `204`.
- `GET base-info/`: public counts and the average rating rounded to one decimal place; an empty review set returns `0.0`.

Input validation uses DRF's standard `400`, unauthenticated calls return `401`, and authenticated calls failing owner/role checks return `403`. Missing resources return `404`.
