# 🚀 FastAPI Webhook Subscription Service

This FastAPI project enables users to create, read, update, and delete webhook subscriptions. When events are triggered, the system sends POST requests (webhooks) to subscribed external URLs.

---

## 📦 Environment Variables

The following environment variables can be configured to customize the service:

| Variable         | Default Value              | Description                                    |
|------------------|----------------------------|------------------------------------------------|
| `DB_NAME`        | `webhook_service`          | Name of the MongoDB database                   |
| `MONGO_URI`      | `mongodb://localhost:27017`| MongoDB connection URI                         |
| `REDIS_URL`      | `redis://localhost`        | Redis connection URL                           |
| `WORKER_COUNT`   | `10`                       | Number of concurrent webhook workers           |
| `REQUEST_TIMEOUT`| `10`                       | HTTP request timeout for webhook delivery (s)  |

Set these in your `.env` file or export them in your shell environment before running the service.

---

## ⚙️ Architecture

This version of the webhook service uses **`asyncio.Queue`** to handle webhook delivery jobs efficiently. Incoming events are enqueued and processed concurrently by a pool of asynchronous workers.

> 🧠 **Note:** There is an earlier implementation of this project that uses **FastAPI’s built-in `BackgroundTasks`** for webhook dispatching instead of `asyncio.Queue`. You can find this version in a separate branch named `background-task-version`.

---

## 📚 Features

* ✅ Create, Read, Update, Delete subscriptions
* 📩 Trigger webhooks based on event types
* 🌐 Subscriptions to all events by passing an empty `event_types` list
* 🔒 Subscription secrets: Add a secret key to your subscription to verify incoming requests before sending the webhook POST request to the target URL.
* ⚡ Asynchronous and high-performance (FastAPI + HTTPX)
* 🔁 Queue-based webhook processing via `asyncio.Queue`
* 🧪 Comprehensive test suite using `pytest`, `httpx`, and `respx`
* 🐳 Fully Dockerized setup

---

## 🐳 Local Setup Using Docker

### 1. Clone the Repository

```bash
git clone https://github.com/Ns-AnoNymouS/webhook-service.git
cd webhook-service
````

### 2. Build and Start the Server

```bash
docker-compose up --build
```

### 3. Access the API Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔌 API Documentation

### ➕ Create Subscription

**POST** `/subscriptions`

```json
{
  "target_url": "https://webhook.site/your-endpoint",
  "event_types": ["order.update"]
}
```

✅ If `"event_types": []` is provided, the subscription will receive **all events**.

---

### 📖 Read All Subscriptions

**GET** `/subscriptions`

Returns a list of all active subscriptions.

---

### 📖 Read One Subscription

**GET** `/subscriptions/{id}`

Returns a specific subscription by its ID.

---

### 🔁 Update Subscription

**PUT** `/subscriptions/{id}`

```json
{
  "target_url": "https://new-url.com",
  "event_types": []
}
```

Updates the subscription. Empty `event_types` will now capture **all** future events.

---

### ❌ Delete Subscription

**DELETE** `/subscriptions/{id}`

Deletes a subscription by ID.

---

### 🚀 Trigger Webhook

**POST** `/ingest/{subscription_id}?event_type=order.update`

```json
{
  "order_id": "1234",
  "status": "shipped"
}
```

In this updated version, the event_type is now a query parameter in the URL (e.g., ?event_type=order.update), while the payload is provided directly in the body of the request.

If the `event_type` matches what the subscription expects, a webhook POST request is sent to the `target_url`.

> 🛡️ Verification: If a secret was provided in the subscription, the system will check for the presence of the X-Hub-Signature-256 header in the request. If it’s missing or doesn’t match, the webhook request is rejected. Check the `signature.py` to get the `X-Hub-Signature-256` header for your body.

---

## 🧪 Running Tests

Run tests using the following command:

```bash
PYTHONPATH=./src pytest tests/
```

This ensures correct imports when tests rely on `src/` as the module root.

---

## 🛠 Tech Stack

* **FastAPI** – Modern Python web framework
* **Uvicorn** – ASGI web server
* **HTTPX** – Async HTTP client
* **Respx** – Mocking HTTP requests
* **Pytest** – Test framework
* **Docker** – Containerization

---


