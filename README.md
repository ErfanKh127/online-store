# 🛒 Online Store API

A Django REST Framework powered e-commerce backend that provides secure JWT authentication, product management, shopping cart, order processing, and Zarinpal payment integration.

---

## ✨ Features

- 🔐 JWT Authentication
- 👤 User Registration & Login
- 🏪 Store Management
- 📦 Product Management
- 🛒 Shopping Cart
- 📄 Order Management
- 💳 Zarinpal Payment Gateway (Sandbox)
- 🐳 Docker Support
- 🗄 PostgreSQL Database
- ⚡ Redis Integration
- RESTful API Architecture

---

# 🛠 Tech Stack

| Technology | Description |
|------------|-------------|
| Python 3.11 | Programming Language |
| Django 4.2 | Backend Framework |
| Django REST Framework | REST APIs |
| PostgreSQL | Database |
| Redis | Cache |
| Docker & Docker Compose | Containerization |
| JWT | Authentication |
| Zarinpal Sandbox | Payment Gateway |

---

# 📂 Project Structure

```
online-store/
│
├── accounts/
├── cart/
├── common/
├── config/
├── core/
├── orders/
├── payments/
├── products/
├── stores/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── .env.example
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/ErfanKh127/online-store.git
cd online-store
```

---

## Create Environment File

Copy

```bash
.env.example
```

to

```bash
.env
```

and fill in your own values.

Example:

```env
SECRET_KEY=your-secret-key

DEBUG=True

DB_NAME=custom_backend_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0

ZARINPAL_MERCHANT_ID=your-merchant-id
ZARINPAL_SANDBOX=True
```

---

# 🐳 Run with Docker

Build containers

```bash
docker compose build
```

Start services

```bash
docker compose up
```

Run migrations

```bash
docker compose exec app python manage.py migrate
```

Create superuser

```bash
docker compose exec app python manage.py createsuperuser
```

The API will be available at

```
http://127.0.0.1:8000/
```

---

# 🔑 Authentication

Obtain JWT Token

```
POST /api/token/
```

Refresh Token

```
POST /api/token/refresh/
```

---

# 📦 Main API Endpoints

## Authentication

```
POST /api/token/
POST /api/token/refresh/
```

## Products

```
GET /api/products/
GET /api/products/{id}/
POST /api/products/
PUT /api/products/{id}/
DELETE /api/products/{id}/
```

## Cart

```
GET /api/cart/
POST /api/cart/items/
PATCH /api/cart/items/{id}/
DELETE /api/cart/items/{id}/
```

## Orders

```
GET /api/orders/
POST /api/orders/
```

## Payments

```
POST /api/payments/initiate/{order_id}/
GET  /api/payments/verify/
```

---

# 💳 Payment Gateway

This project integrates with **Zarinpal Sandbox** for testing payment workflows.

Payment Flow

```
Create Order
      ↓
Initiate Payment
      ↓
Redirect to Zarinpal
      ↓
Verify Payment
      ↓
Update Order Status
```

---

# 🖼 Screenshots

## API Authentication

_Add your Postman screenshot here._

---

## Django Admin

_Add your Django Admin screenshot here._

---

## Payment Process

_Add your payment initiation screenshot here._

---

# 📚 Future Improvements

- Product Categories
- Product Images
- Search & Filtering
- User Addresses
- Wishlist
- Coupons
- Celery Background Tasks
- Email Notifications
- Swagger Documentation
- Unit Tests
- CI/CD Pipeline

---

# 🤝 Contributing

Contributions, issues, and feature requests are welcome.

Feel free to fork the repository and submit a Pull Request.

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Erfan Khosrobigi**

GitHub:
https://github.com/ErfanKh127
