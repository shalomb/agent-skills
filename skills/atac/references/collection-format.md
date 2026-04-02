# ATAC Collection & Request JSON/YAML Schema

Full schema for ATAC collection files. Collections are stored as `.json` or
`.yaml` files in your ATAC directory.

## Top-Level Collection

```json
{
  "name": "My Collection",
  "last_position": 0,
  "requests": [ /* array of Request objects */ ]
}
```

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Display name |
| `last_position` | int \| null | Sort order in TUI |
| `requests` | Request[] | Ordered list |

## Request Object

```json
{
  "name": "Create User",
  "url": "{{BASE_URL}}/users",
  "params": [],
  "headers": [ /* KeyValue[] */ ],
  "auth": "no_auth",
  "scripts": {
    "pre_request_script": null,
    "post_request_script": null
  },
  "settings": {
    "use_config_proxy": true,
    "allow_redirects": true,
    "timeout": 30000,
    "store_received_cookies": true,
    "pretty_print_response_content": true,
    "accept_invalid_certs": false,
    "accept_invalid_hostnames": false
  },
  "protocol": { /* Protocol object */ }
}
```

## KeyValue (headers, params)

```json
{ "enabled": true, "data": ["header-name", "header-value"] }
```

Disabled entries are skipped when sending.

## Auth Variants

```json
// No auth
"auth": "no_auth"

// Basic auth
"auth": { "basic_auth": { "username": "user", "password": "{{PASSWORD}}" } }

// Bearer token
"auth": { "bearer_token": { "token": "{{TOKEN}}" } }

// Digest auth
"auth": { "digest_auth": { "username": "user", "password": "pass" } }

// JWT
"auth": {
  "jwt_auth": {
    "algorithm": "HS256",
    "secret": "{{JWT_SECRET}}",
    "payload": "{\"sub\": \"user123\"}",
    "header": null,
    "prefix": "Bearer"
  }
}
```

## Protocol Variants

### HTTP

```json
{
  "type": "http",
  "method": "GET",
  "body": "no_body"
}
```

**Methods:** `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, `TRACE`, `CONNECT`

**Body variants:**

```json
// No body
"body": "no_body"

// Raw text
"body": { "raw": "plain text here" }

// JSON
"body": { "json": "{\"key\": \"value\"}" }

// XML
"body": { "xml": "<root><item>value</item></root>" }

// HTML
"body": { "html": "<h1>Hello</h1>" }

// JavaScript
"body": { "javascript": "console.log('hi')" }

// Form URL-encoded
"body": { "form": [["field1", "value1"], ["field2", "value2"]] }

// Multipart form
"body": { "multipart": [["field", "value"], ["file", "@/path/to/file"]] }

// File upload
"body": { "file": "/path/to/file.json" }
```

### WebSocket

```json
{
  "type": "websocket",
  "url": "wss://example.com/ws"
}
```

## Full Example: POST with JSON body and Bearer auth

```json
{
  "name": "Create Order",
  "url": "{{BASE_URL}}/orders",
  "params": [],
  "headers": [
    { "enabled": true,  "data": ["content-type", "application/json"] },
    { "enabled": true,  "data": ["accept", "application/json"] }
  ],
  "auth": { "bearer_token": { "token": "{{AUTH_TOKEN}}" } },
  "scripts": {
    "pre_request_script": null,
    "post_request_script": "var b = JSON.parse(response.content);\nif (response.status_code !== '201 Created') throw 'FAIL: ' + response.status_code;\nenv.ORDER_ID = b.id;\nconsole.log('PASS: order ' + b.id + ' created');"
  },
  "settings": {
    "use_config_proxy": true,
    "allow_redirects": true,
    "timeout": 30000,
    "store_received_cookies": false,
    "pretty_print_response_content": true,
    "accept_invalid_certs": false,
    "accept_invalid_hostnames": false
  },
  "protocol": {
    "type": "http",
    "method": "POST",
    "body": { "json": "{\"product_id\": \"{{PRODUCT_ID}}\", \"qty\": 1}" }
  }
}
```

## YAML Equivalent

```yaml
name: My Collection
last_position: 0
requests:
  - name: GET Health
    url: "{{BASE_URL}}/health"
    params: []
    headers:
      - enabled: true
        data: [accept, "*/*"]
    auth: no_auth
    scripts:
      pre_request_script: null
      post_request_script: |
        if (response.status_code !== "200 OK") throw "FAIL: " + response.status_code;
        console.log("PASS");
    settings:
      use_config_proxy: true
      allow_redirects: true
      timeout: 30000
      store_received_cookies: true
      pretty_print_response_content: true
      accept_invalid_certs: false
      accept_invalid_hostnames: false
    protocol:
      type: http
      method: GET
      body: no_body
```
