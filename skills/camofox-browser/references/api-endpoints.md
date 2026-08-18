# Camofox Browser REST API Endpoints

Base URL: `http://localhost:9377`

All endpoints require `userId=demo` (or your chosen session ID) as a query parameter unless noted.

## Session Management

### Create Tab
```
POST /tabs?userId={userId}
Content-Type: application/json

{
  "userId": "demo",
  "sessionKey": "unique-session-key",
  "url": "https://example.com"  // optional, navigate on creation
}

Response: {"tabId":"<uuid>","url":"about:blank"}
```

### Navigate Tab
```
POST /tabs/{tabId}/navigate?userId={userId}
Content-Type: application/json

{
  "url": "https://example.com",
  "userId": "demo"
}

Response: {"ok":true,"tabId":"<uuid>","url":"https://example.com/","refsAvailable":true}
```

### Get Snapshot
```
GET /tabs/{tabId}/snapshot?userId={userId}&full=true&maxChars=50000

Response: {
  "url": "https://example.com/",
  "snapshot": "- heading \"Example Domain\" [level=1]\n- paragraph:\n    - link \"Learn more\" [e1]:\n      - /url: https://iana.org/domains/example",
  "refsCount": 5,
  "truncated": false,
  "totalChars": 237
}
```

### Take Screenshot
```
GET /tabs/{tabId}/screenshot?userId={userId}&fullPage=true&format=png

Response: binary PNG data (Content-Type: image/png)
```

## Interaction

### Click Element
```
POST /tabs/{tabId}/click?userId={userId}
Content-Type: application/json

{
  "ref": "@e3",
  "userId": "demo"
}
```

### Type Text
```
POST /abs/{tabId}/type?userId={userId}
Content-Type: application/json

{
  "ref": "@e2",
  "text": "search query",
  "userId": "demo"
}
```

### Press Key
```
POST /tabs/{tabId}/press?userId={userId}
Content-Type: application/json

{
  "key": "Enter",
  "userId": "demo"
}
```

## Information Endpoints

### List Images
```
GET /tabs/{tabId}/images?userId={userId}

Response: {
  "url": "https://example.com/",
  "images": [
    {"src": "https://example.com/img.png", "alt": "description"}
  ]
}
```

### Close Tab
```
DELETE /tabs/{tabId}?userId={userId}
Response: {"ok":true,"tabId":"<uuid>"}
```

## Health & Monitoring

### Health Check
```
GET /health

Response: {
  "ok": true,
  "engine": "camoufox",
  "browserConnected": false,
  "activeTabs": 0,
  "activeSessions": 1,
  "consecutiveFailures": 0,
  "memory": {"rssMb": 129, "heapUsedMb": 75}
}
```

### Metrics (Prometheus)
```
GET /metrics
```
