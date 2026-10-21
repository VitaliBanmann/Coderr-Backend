# Coderr Backend

Developed as part of the Developer Akademie training programme.

This repository contains the Django REST Framework API for the Coderr freelancer marketplace. The separately licensed frontend is maintained in the [Coderr-Frontend repository](https://github.com/VitaliBanmann/Coderr-Frontend) and is intentionally not part of this backend repository (locally it lives in `../frontend/`).

## Requirements

- Python 3.10 or newer
- pip

## Local setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`; the Django admin is at `http://127.0.0.1:8000/admin/`.

The optional `seed_demo` command creates the frontend's local guest accounts:

- Customer: `andrey` / `asdasd`
- Business: `kevin` / `asdasd24`
- Business seller with three sample offers: `VitaliBanmannSeller` / `asdasd24`

These are public demo credentials for local learning only. Do not use the demo seed or these passwords outside a local development environment. Create an administrator with `python manage.py createsuperuser`.

## Frontend

Run the frontend from `../frontend/` using VS Code Live Server on port `5500` (or `5501`). Those local origins are allowed by the development CORS configuration. The API base URL is configured in `frontend/shared/scripts/config.js`.

## API

All routes use the `/api/` prefix. Token authentication uses the `Authorization: Token <token>` header.

| Area | Endpoints |
| --- | --- |
| Authentication | `POST registration/`, `POST login/` |
| Profiles | `GET/PATCH profile/{pk}/`, `GET profiles/business/`, `GET profiles/customer/` |
| Offers | `GET/POST offers/`, `GET/PATCH/DELETE offers/{id}/`, `GET offerdetails/{id}/` |
| Orders | `GET/POST orders/`, `GET/PATCH/DELETE orders/{id}/`, `GET order-count/{business_user_id}/`, `GET completed-order-count/{business_user_id}/` |
| Reviews | `GET/POST reviews/`, `GET/PATCH/DELETE reviews/{id}/` |
| Platform statistics | `GET base-info/` |

The offer list uses page-number pagination with six results per page. See [`docs/api-contracts.md`](docs/api-contracts.md) for the implemented request and permission rules.

## Tests and migrations

```powershell
python manage.py test
python -m coverage run manage.py test
python -m coverage report
python -m pycodestyle .
python manage.py makemigrations --check --dry-run
python manage.py check
```

The coverage configuration omits Django-generated migrations and framework
bootstrap/admin boilerplate; the API and project logic are covered by the test
suite.

The SQLite database, uploaded media, virtual environment and local environment files are excluded from Git. Configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` and `DJANGO_ALLOWED_HOSTS` through environment variables outside local development.

## Licensing and attribution

**Developed as part of the Developer Akademie training programme.**

The supplied frontend and its assets retain the Developer Akademie non-commercial learning licence in the frontend repository's `LICENSE.md`; the licence text is also preserved here as `LICENSE-ACADEMY.md`. Required attribution is included in both project READMEs. The MIT `LICENSE` in this backend repository covers the author's original backend contributions only and does not relicense Developer Akademie material. The source repositories' MIT notices are retained separately for original author-owned contributions.
