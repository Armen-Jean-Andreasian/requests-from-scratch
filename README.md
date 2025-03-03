# HTTP Client

A lightweight Python HTTP client for making requests with built-in support for redirects, JSON handling, and compressed response decoding.

## Features

- Supports `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, and `OPTIONS` requests.
- Handles redirects (configurable).
- Supports gzip and deflate compression.
- Automatic JSON serialization and deserialization.
- Custom headers support.
- Connection persistence with `keep-alive`.

## Installation

No additional dependencies required. The client is built on Python's standard `http.client` and `urllib` modules.

## Usage

### Initialization (optional)
```python
from client import Client

# Optional: Set default headers and redirect behavior
Client.init(custom_headers={"Authorization": "Bearer YOUR_TOKEN"}, allow_redirects=True)
```

### Sending Requests
#### GET Request
```python
response = Client.get("https://jsonplaceholder.typicode.com/posts/1")
print(response.status_code)
print(response.json)
```

#### POST Request with JSON Data
```python
data = {"title": "foo", "body": "bar", "userId": 1}
response = Client.post("https://jsonplaceholder.typicode.com/posts", json_data=data)
print(response.status_code)
print(response.json)
```

#### PUT Request
```python
data = {"title": "updated title"}
response = Client.put("https://jsonplaceholder.typicode.com/posts/1", json_data=data)
print(response.status_code)
print(response.json)
```

#### DELETE Request
```python
response = Client.delete("https://jsonplaceholder.typicode.com/posts/1")
print(response.status_code)
```

### Handling Responses
```python
print(response.status_code)  # HTTP status code
print(response.headers)      # Response headers
print(response.content)      # Raw response body
print(response.json)         # Parsed JSON response (if applicable)
```

## Error Handling
- Automatically raises an error for unsupported schemes.
- Returns `None` if JSON decoding fails.
- Raises an error if redirection is attempted without a `Location` header.

## License

Armen-Jean Andreasian 2025


---

## Reminder

- The purpose is to showcase how requests operate "under the hood."
- The product is provided "as is", it's not fully tested. If you considering to use it - you may need to test by yourself.
- The lib doesn't provide sessions, each request is independent (for now).
