# Maison — Luxury Women's Fashion E-commerce

A production-oriented Django e-commerce platform for women's clothing, with a branded admin dashboard, Razorpay payments, and WhatsApp order confirmation.

---

## Mac Setup

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- Git

### 1. Clone and enter the project
```bash
cd /path/to/clothingbrand
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Node dependencies (for Tailwind CSS)
```bash
npm install
```

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your values
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Create admin account
```bash
python manage.py createsuperuser
```

### 8. Load sample data (optional)
```bash
python manage.py loaddata fixtures/sample_data.json
```

### 9. Build CSS
```bash
npm run build:css
# Or watch during development:
npm run watch:css
```

### 10. Start development server
```bash
python manage.py runserver
```

Visit:
- Storefront: http://127.0.0.1:8000/
- Branded dashboard: http://127.0.0.1:8000/dashboard/
- Django admin: http://127.0.0.1:8000/admin/

---

## Razorpay Test Setup

1. Create a free account at https://razorpay.com
2. Go to Settings → API Keys → Generate Test Key
3. Add to `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=your_actual_secret
   RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
   ```
4. For webhooks in development, use [ngrok](https://ngrok.com):
   ```bash
   ngrok http 8000
   ```
   Then add `https://your-ngrok-url.ngrok.io/orders/payment/webhook/` in Razorpay Dashboard → Webhooks.
   Select the `payment.captured` event.

**Test card:** 4111 1111 1111 1111, any future expiry, any CVV.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for dev, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `DATABASE_URL` | PostgreSQL URL (leave blank for SQLite) |
| `RAZORPAY_KEY_ID` | Razorpay API key ID |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret |
| `RAZORPAY_WEBHOOK_SECRET` | Razorpay webhook signing secret |
| `WHATSAPP_NUMBER` | WhatsApp number with country code (e.g. `919876543210`) |

---

## Running Tests

```bash
source venv/bin/activate
python manage.py test store.tests orders.tests
```

---

## Project Structure

```
clothingbrand/
├── config/          # Django project settings and root URLs
├── core/            # Store settings, banners, dashboard views
├── store/           # Products, categories, cart, offers, coupons
├── orders/          # Orders, payments, Razorpay integration
├── templates/
│   ├── base.html
│   ├── store/       # Storefront templates
│   ├── orders/      # Checkout and order templates
│   └── dashboard/   # Admin dashboard templates
├── static/
│   └── css/
│       ├── input.css   # Tailwind source
│       └── main.css    # Compiled output
├── fixtures/
│   └── sample_data.json
├── .env.example
├── .gitignore
├── requirements.txt
├── package.json
└── tailwind.config.js
```

---

## Deployment Checklist

### Environment
- [ ] Set `DEBUG=False`
- [ ] Set a strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Set `DATABASE_URL` to your PostgreSQL connection string
- [ ] Set real Razorpay live credentials (`rzp_live_...`)
- [ ] Set `WHATSAPP_NUMBER`

### Static files
```bash
npm run build:css
python manage.py collectstatic --noinput
```

### Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Web server (Gunicorn + Nginx recommended)
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Security
- [ ] HTTPS enabled (Let's Encrypt / Cloudflare)
- [ ] Nginx configured to serve `/static/` and `/media/` directly
- [ ] `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` are auto-enabled when `DEBUG=False`
- [ ] Razorpay webhook URL registered in Razorpay dashboard
- [ ] Media files backed up (S3 or equivalent recommended for production)

### Razorpay go-live
- [ ] Switch from test keys to live keys
- [ ] Complete Razorpay KYC
- [ ] Update webhook URL to production domain
- [ ] Test a real ₹1 transaction end-to-end

---

## Incomplete / Pending

- **Razorpay live credentials** — you must obtain these from your Razorpay account
- **WhatsApp number** — update in Store Settings via the dashboard
- **Product images** — upload via Dashboard → Products → Images
- **Homepage banners** — add via Dashboard → Banners
- **Brand name** — change from "Maison" via Dashboard → Settings
- **Policy pages** — fill in via Dashboard → Settings
- **Email notifications** — not yet implemented (order confirmation emails)
- **Shipping cost calculation** — currently shows "calculated at checkout" but no shipping fee is added
- **Pagination on product list** — not yet added (all products load at once)
- **Password reset** — not implemented for dashboard users
- **Rate limiting** — `django-ratelimit` is installed but not yet applied to checkout/payment endpoints
- **S3 media storage** — media files are stored locally; configure `django-storages` + S3 for production
