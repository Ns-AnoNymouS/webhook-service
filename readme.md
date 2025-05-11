# 🚀 FastAPI Webhook Subscription Service

This FastAPI project enables users to create, read, update, and delete webhook subscriptions. When events are triggered, the system sends POST requests (webhooks) to subscribed external URLs. It supports event type filtering, signature verification, and robust retry strategies to ensure delivery reliability.

---

## 📆 Features

* ✅ Create, Read, Update, Delete webhook subscriptions
* 📩 Trigger webhooks for specific event types
* 🌐 Subscribe to all events with empty `event_types`
* 🔒 Secure subscriptions using secret-based signature verification
* ⚡ Asynchronous processing via `asyncio.Queue`
* 🛡️ Configurable retry strategy for webhook delivery
* 🧰 Dockerized setup for easy deployment
* 🔮 NoSQL-first approach with MongoDB
* 🤖 Redis used for coordination (future extensibility)

---

## 🌟 Architecture Overview

* **FastAPI** for serving HTTP API endpoints
* **MongoDB** (NoSQL) to store:

  * Subscription documents
  * Webhook delivery logs
* **Redis** for shared state and coordination
* **AsyncIO Queue** to handle high-throughput delivery
* **HTTPX** for async HTTP requests
* **Retry logic** using static intervals

---

## 🔧 Why NoSQL (MongoDB)?

* Subscription documents can vary and grow in schema over time.
* Delivery logs may be numerous and not require strong relational consistency.
* Indexes can be applied on `subscription_id`, `event_type`, and `status` for efficient retrieval.
* MongoDB provides great performance for high write throughput, which suits webhook logging.

---

## 📢 Backoff and Retry Strategy

The current backoff strategy uses a **static retry interval list** defined in [`src/app/constants.py`](src/app/constants.py):

```python
RETRY_INTERVALS = [10, 30, 60, 120, 300]  # in seconds
```

* Retries are limited to **5 attempts**.
* Static backoff is simple and predictable.
* This avoids wasting resources on excessive retries.
* For more flexibility, an **exponential backoff** mechanism can be implemented if needed with a formula like base * (2 ** attempt).

---

## 🔒 Security Features
### ✅ Signature Verification
If a secret is added to a subscription, outgoing webhooks will include a header:
X-Hub-Signature-256: sha256=...

Receivers can verify this to ensure authenticity. Incoming secrets are hashed using HMAC-SHA256 over the request body.

## 🎯 Event Type Filtering
Subscriptions can specify event_types like:

```json
["user.signup", "order.placed"]
```
Only matching events trigger webhook delivery.
If event_types is empty, the subscription will receive all events.

## 🛠️ Environment Variables

| Variable          | Default                     | Description                                 |
| ----------------- | --------------------------- | ------------------------------------------- |
| `DB_NAME`         | `webhook_service`           | MongoDB database name                       |
| `MONGO_URI`       | `mongodb://localhost:27017` | MongoDB connection URI                      |
| `REDIS_URL`       | `redis://localhost`         | Redis connection URL                        |
| `WORKER_COUNT`    | `10`                        | Number of async workers for webhook queue   |
| `REQUEST_TIMEOUT` | `10`                        | Timeout (in seconds) for webhook HTTP calls |

---

## 🚧 Running Locally with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/Ns-AnoNymouS/webhook-service.git
cd webhook-service
```

### 2. Start with Docker

```bash
docker-compose up --build
```

If you're on Linux and face permission issues, use:

```bash
sudo docker-compose up --build
```

### 3. Access API Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔎 API Reference

### ➕ Create Subscription

```bash
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://webhook.site/your-endpoint", "event_types": ["order.update"]}'
```

### 📖 Read All Subscriptions

```bash
curl http://localhost:8000/subscriptions
```

### 📖 Read Subscription by ID

```bash
curl http://localhost:8000/subscriptions/<subscription_id>
```

### ↺ Update Subscription

```bash
curl -X PUT http://localhost:8000/subscriptions/<subscription_id> \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://new-url.com", "event_types": []}'
```

### ❌ Delete Subscription

```bash
curl -X DELETE http://localhost:8000/subscriptions/<subscription_id>
```

### 🚀 Ingest Event (Trigger Webhook)

```bash
curl -X POST "http://localhost:8000/ingest/<subscription_id>?event_type=order.update" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "1234", "status": "shipped"}'
```

---

## 🚪 Testing Webhooks

To inspect webhook deliveries, use [https://webhook.site/](https://webhook.site/) to generate a temporary URL and view requests in real-time.

---

## 💸 Cost Estimation

| Item                  | Free Tier Provider  | Estimated Usage         | Monthly Cost (Free Tier)    |
| --------------------- | ------------------- | ----------------------- | --------------------------- |
| **MongoDB Atlas**     | MongoDB             | 5000 docs/day + queries | \$0 (under shared cluster)  |
| **Redis**             | Upstash/Redis Stack | Light coordination only | \$0 (minimal usage)         |
| **FastAPI + Uvicorn** | Render/Fly.io       | Always-on instance      | \$0 (free web service tier) |

Assumptions:

* 5000 events/day, \~1.2 retries/event
* 1 container handles all workloads
* Minimal logging requirements

---

## 📓 Database Schema and Indexing

### `subscriptions`

```json
{
  "_id": "ObjectId",
  "target_url": "https://example.com/hook",
  "event_types": ["order.update", "order.cancel"],
  "secret": "...",
  "created_at": "ISODate"
}
```

**Indexes:**

* `event_types`
* `created_at`

### `delivery_logs`

```json
{
  "subscription_id": "ObjectId",
  "event_type": "order.update",
  "payload": { ... },
  "attempts": 3,
  "status": "success" | "failed",
  "last_attempt_at": "ISODate"
}
```

**Indexes:**

* `subscription_id`
* `status`
* `last_attempt_at`

---

## 📄 Tests

Run unit tests with:

```bash
PYTHONPATH=./src pytest tests/
```

---

## 🙏 Credits

* [FastAPI](https://fastapi.tiangolo.com/)
* [MongoDB](https://www.mongodb.com/)
* [Redis](https://redis.io/)
* [HTTPX](https://www.python-httpx.org/)
* [Respx](https://lundberg.github.io/respx/)
* [Webhook.site](https://webhook.site/) for live webhook testing
* [OpenAI ChatGPT](https://chat.openai.com)
* [webhook.site](https://webhook.site) for testing
