# 🚀 FastAPI Webhook Subscription Service

This FastAPI project enables users to create, read, update, and delete webhook subscriptions. When events are triggered, the system sends POST requests (webhooks) to subscribed external URLs.

---

## 📦 Environment Variables

The following environment variables can be configured to customize the service:

| Variable          | Default Value               | Description                                   |
| ----------------- | --------------------------- | --------------------------------------------- |
| `DB_NAME`         | `webhook_service`           | Name of the MongoDB database                  |
| `MONGO_URI`       | `mongodb://localhost:27017` | MongoDB connection URI                        |
| `REDIS_URL`       | `redis://localhost`         | Redis connection URL                          |
| `WORKER_COUNT`    | `10`                        | Number of concurrent webhook workers          |
| `REQUEST_TIMEOUT` | `10`                        | HTTP request timeout for webhook delivery (s) |

Set these in your `.env` file or export them in your shell environment before running the service.

---

## ⚙️ Architecture

This version of the webhook service uses **FastAPI** with **asyncio.Queue** for webhook delivery. Events are queued and processed concurrently by asynchronous workers using **HTTPX**. Redis is optionally used for deduplication and retry management.

### ✅ Framework: FastAPI

* High performance, modern async support.
* Native Swagger documentation.

### ✅ Database: MongoDB (NoSQL)

* Chosen for flexibility in storing dynamic webhook subscription schemas.
* No fixed schema required — ideal for various payloads and evolving event types.
* Suitable for large-scale data like delivery logs with flexible indexing.
* Built-in support for TTL indexes, ideal for log expiration.

### ✅ Async Task System: asyncio.Queue

* Efficient in-process background task management.
* Easy to scale with configurable worker count.
* Webhooks are retried on failure using backoff logic.

---

## 🧰 Database Schema & Indexing Strategy

### Subscription Document (MongoDB):

```json
{
  "target_url": "https://example.com",
  "event_types": ["order.update", "user.signup"],
  "secret": "optional-secret",
  "created_at": ISODate()
}
```

* Index on `event_types` for quick subscription matching.
* TTL index on delivery logs (if implemented) for auto-cleanup.

---

## 🐳 Local Setup Using Docker

### 1. Clone the Repository

```bash
git clone https://github.com/Ns-AnoNymouS/webhook-service.git
cd webhook-service
```

### 2. Build and Start the Server

```bash
docker-compose up --build
```

If on Linux and facing permission issues:

```bash
sudo docker-compose up --build
```

### 3. Access the API Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔌 API Usage Guide (with curl Examples)

### ➕ Create Subscription

```bash
curl -X POST http://localhost:8000/subscriptions \
  -H 'Content-Type: application/json' \
  -d '{
        "target_url": "https://webhook.site/your-endpoint",
        "event_types": ["order.update"]
      }'
```

### 📖 Get All Subscriptions

```bash
curl http://localhost:8000/subscriptions
```

### 📖 Get Subscription by ID

```bash
curl http://localhost:8000/subscriptions/<subscription_id>
```

### 🔁 Update Subscription

```bash
curl -X PUT http://localhost:8000/subscriptions/<subscription_id> \
  -H 'Content-Type: application/json' \
  -d '{
        "target_url": "https://new-url.com",
        "event_types": []
      }'
```

### ❌ Delete Subscription

```bash
curl -X DELETE http://localhost:8000/subscriptions/<subscription_id>
```

### 🚀 Ingest Webhook

```bash
curl -X POST 'http://localhost:8000/ingest/<subscription_id>?event_type=order.update' \
  -H 'Content-Type: application/json' \
  -d '{"order_id": "1234", "status": "shipped"}'
```

---

## 💵 Cost Estimation (Free Tier)

Assuming:

* 5000 webhooks/day
* Avg 1.2 delivery attempts (6000 HTTP POST/day)

### Estimated Monthly Cost on Free Tiers:

* **MongoDB Atlas**: Free up to 512MB (fits easily with TTL logs)
* **Redis**: Use local Redis or up to 30MB memory with free Redis providers
* **App Hosting (Render/Heroku/Fly.io)**: Free dynos support 550–750 hours/month (\~23x7)
* **Total**: 💰 \~\$0/month on generous free tiers

---

## 🔎 Assumptions

* External URLs are valid and reachable.
* Delivery logs stored in-memory or in a capped Mongo collection.
* TTL expiry on logs (if stored) cleans up old entries.
* Redis is used only if retry/dedup logic requires persistence.

---

## 🙏 Credits

* **FastAPI** – [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
* **HTTPX** – [https://www.python-httpx.org](https://www.python-httpx.org)
* **Respx** – [https://lundberg.github.io/respx/](https://lundberg.github.io/respx/)
* **Uvicorn** – [https://www.uvicorn.org](https://www.uvicorn.org)
* **Docker** – [https://www.docker.com](https://www.docker.com)
* **MongoDB** – [https://www.mongodb.com](https://www.mongodb.com)
* **Redis** – [https://redis.io](https://redis.io)
* **GitHub Copilot/OpenAI ChatGPT** – for assistance with code and documentation.

---

## 🌐 Live Demo

[🔗 Deployed App Link (Replace with actual URL)](https://your-live-url.com)

---

## 🧪 Run Tests

```bash
PYTHONPATH=./src pytest tests/
```

Use this to run all automated tests against the service logic.

