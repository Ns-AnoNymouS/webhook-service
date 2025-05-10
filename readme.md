# 🚀 FastAPI Webhook Subscription Service

This FastAPI project enables users to create, read, update, and delete webhook subscriptions. When events are triggered, the system sends POST requests (webhooks) to subscribed external URLs.

---

## 📚 Features

* ✅ Create, Read, Update, Delete subscriptions
* 📩 Trigger webhooks based on event types
* 🌐 Subscriptions to all events by passing an empty `event_types` list
* ⚡ Asynchronous and high-performance (FastAPI + HTTPX)
* 🧪 Comprehensive test suite using `pytest`, `httpx`, and `respx`
* 🐳 Fully Dockerized setup

---

## 🐳 Local Setup Using Docker

### 1. Clone the Repository

```bash
git clone https://github.com/Ns-AnoNymouS/webhook-service.git
cd webhook-service
```

### 2. Add Your Requirements

Ensure your `requirements.txt` contains:

```txt
fastapi
uvicorn
httpx
respx
pytest
pytest-asyncio
```

### 3. Build and Start the Server

```bash
docker-compose up --build
```

### 4. Access the API Docs

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

**POST** `/ingest/{subscription_id}`

```json
{
  "event_type": ["order.update"],
  "payload": {
    "order_id": "1234",
    "status": "shipped"
  }
}
```

If the `event_type` matches what the subscription expects, a webhook POST request is sent to the `target_url`.

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

## 📫 Contact

Feel free to open issues or contribute to the repo!
