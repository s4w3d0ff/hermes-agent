---
name: twitch-api
description: Twitch API reference covering OAuth authentication flows and EventSub WebSocket integration
version: 0.0.1
author: [s4w3d0ff, hermes]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [api, twitch, eventsub, oauth, chatbot, websocket, docs]
---
## REST api
Entire complete REST api docs can be found in `references/api/references.md`

## OAuth Authentication

Twitch uses OAuth 2.0 with two token types: **user access tokens** (for user-specific data) and **app access tokens** (for non-sensitive data).

### Flows

| Flow | Token Type | Use Case |
|------|------------|----------|
| **Authorization Code Grant** | User | Server-side apps with secure client secret storage |
| **Implicit Grant** | User | Client-side apps (JS, mobile) without server |
| **Client Credentials Grant** | App | Server-to-server, no user context needed |
| **Device Code Grant** | User | Limited-input devices (TVs, consoles) |
| **OIDC Authorization Code Grant** | User + ID Token | Server-side apps needing OpenID Connect identity |
| **OIDC Implicit Grant** | User + ID Token | Client-side apps needing OpenID Connect identity |

### Key Endpoints

```
Authorization:  https://id.twitch.tv/oauth2/authorize
Token Exchange: https://id.twitch.tv/oauth2/token
Device Auth:    https://id.twitch.tv/oauth2/device
Validate:       https://id.twitch.tv/oauth2/validate
Revoke:         https://id.twitch.tv/oauth2/revoke
OIDC Discovery: https://id.twitch.tv/oauth2/.well-known/openid-configuration
JWKS:           https://id.twitch.tv/oauth2/keys
UserInfo:       https://id.twitch.tv/oauth2/userinfo
```

### Authorization Code Flow (Recommended for Servers)

1. Redirect user to: `https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={id}&redirect_uri={uri}&scope={scopes}&state={random}`
2. User authorizes → redirect back with `?code={auth_code}&scope={scopes}&state={state}`
3. Exchange code: `POST https://id.twitch.tv/oauth2/token` with `client_id`, `client_secret`, `code`, `grant_type=authorization_code`, `redirect_uri`
4. Response: `{ access_token, refresh_token, expires_in, scope[], token_type }`

### Client Credentials Flow (App Tokens)

```
POST https://id.twitch.tv/oauth2/token
Content-Type: application/x-www-form-urlencoded
client_id={id}&client_secret={secret}&grant_type=client_credentials
```

### Device Code Flow

1. `POST https://id.twitch.tv/oauth2/device` with `client_id`, `scopes`
2. Receive: `device_code`, `user_code`, `verification_uri`, `expires_in`, `interval`
3. User visits `verification_uri` and enters `user_code`
4. Poll: `POST https://id.twitch.tv/oauth2/token` with `grant_type=urn:ietf:params:oauth:grant-type:device_code`, `device_code`, `client_id`, `scopes`
5. Response: `{ access_token, refresh_token, expires_in, scope[], token_type }`

**Note:** Public client type refresh tokens expire after 30 days and are one-time use.

### OIDC Flows

Add `openid` scope and optionally `claims` parameter. Response includes `id_token` (JWT) alongside access/refresh tokens.

- **Implicit:** `response_type=token+id_token` (or `id_token` only)
- **Auth Code:** `response_type=code` → exchange for `access_token`, `refresh_token`, `id_token`

**ID Token Validation:** Use JWKS from discovery endpoint, verify RS256 signature, check `iss`, `aud`, `exp`.

### Token Refresh

```
POST https://id.twitch.tv/oauth2/token
grant_type=refresh_token&refresh_token={refresh_token}&client_id={id}&client_secret={secret}
```

- Only user access tokens from Authorization Code flow can be refreshed
- App access tokens cannot be refreshed
- Public client refresh tokens: one-time use, expire after 30 days
- Confidential client refresh tokens: no expiration, but max 50 active access tokens per refresh token

### Using Tokens

```
Authorization: Bearer <access_token>
Client-Id: {client_id}
```

### Token Validation

```
GET https://id.twitch.tv/oauth2/validate
Authorization: OAuth <token>  (or Bearer)
```

Returns: `{ client_id, scopes[], expires_in, login, user_id }` or 401 if invalid.

**Required:** Third-party apps maintaining OAuth sessions must validate hourly.

### Token Revocation

```
POST https://id.twitch.tv/oauth2/revoke
client_id={id}&token={access_token}
```

### Scopes Reference

See `references/authentication/scopes.md` for full list. Common scopes:

| Scope | Purpose |
|-------|---------|
| `channel:read:subscriptions` | Subscriber events |
| `channel:moderate` | Moderation actions |
| `chat:read` / `chat:edit` | Chat messages (IRC) |
| `bits:read` | Cheer events |
| `channel:bot` | Chatbot identity/badge |
| `user:read:chat` / `user:write:chat` | Chat messages (EventSub) |
| `moderator:read:followers` | Follow events |
| `openid` | OIDC identity token |

### App Registration

1. Enable 2FA on Twitch account
2. Developer Console → Applications → Register
3. Set OAuth Redirect URLs
4. Note Client ID, generate Client Secret

---

## EventSub WebSocket

EventSub WebSocket provides real-time event notifications over a persistent connection.

### Connection Flow

1. Connect to: `wss://eventsub.wss.twitch.tv/ws` (optionally `?keepalive_timeout_seconds=10-600`)
2. Receive **Welcome** message with `session.id` and `keepalive_timeout_seconds`
3. Subscribe to events using the session ID within 10 seconds (code 4003)
4. Handle messages: Notification, Keepalive, Reconnect, Revocation
5. Respond to Ping with Pong (code 4002)

### WebSocket Message Types

| Type | Description |
|------|-------------|
| `session_welcome` | First message after connect - contains session ID |
| `session_keepalive` | Periodic heartbeat - empty payload |
| `notification` | Event occurrence - contains `subscription`, `event` |
| `session_reconnect` | Server dropping connection - contains `reconnect_url` |
| `revocation` | Subscription revoked (auth revoked, user removed, version removed) |

### Subscribing via WebSocket

After receiving Welcome message, create subscription via REST API:

```
POST https://api.twitch.tv/helix/eventsub/subscriptions
Authorization: Bearer {user_access_token}
Client-Id: {client_id}
Content-Type: application/json

{
  "type": "channel.follow",
  "version": "2",
  "condition": { "broadcaster_user_id": "12345" },
  "transport": { "method": "websocket", "session_id": "{welcome.session.id}" }
}
```

### Key Subscription Fields

- `type` - Event type (e.g., `channel.follow`, `stream.online`)
- `version` - Subscription definition version
- `condition` - Filter parameters (broadcaster_id, etc.)
- `transport.method` - `websocket` or `webhook` or `conduit`
- `transport.session_id` - From Welcome message (WebSocket only)
- `transport.callback` - Your HTTPS endpoint (webhook only)
- `transport.secret` - HMAC secret for verification (webhook only)

### Authorization Rules

| Transport | Token Type |
|-----------|------------|
| WebSocket | **User access token only** (app tokens fail) |
| Webhook | **App access token only** (user tokens fail) |
| Conduit | **App access token only** |

### Connection Limits (per user token)

- Max 3 WebSocket connections with enabled subscriptions
- Max 300 enabled subscriptions per connection
- Max total cost: 10 across all subscriptions
- Must subscribe within 10 seconds of connect (code 4003)
- Must respond to Ping with Pong (code 4002)
- Must not send inbound traffic except Pong (code 4001)

### Reconnection

On `session_reconnect`:
1. Connect to `reconnect_url` from message
2. Old subscriptions transfer automatically
3. Close old connection within 30 seconds (code 4004)

### Duplicate Handling

Twitch delivers **at-least-once**. Track `message_id` to deduplicate. Also verify `message_timestamp` is within 10 minutes for replay protection.

---

## EventSub Webhooks

For server-hosted apps (Cloud Chatbots) - receives events via HTTPS callbacks.

### Setup

1. Create HTTPS endpoint on port 443
2. Subscribe with `transport.method=webhook`, `callback`, `secret`
3. Handle `webhook_callback_verification` challenge (return raw challenge)
4. Verify HMAC-SHA256 signature on all messages
5. Respond 2xx within seconds (or queue for async processing)

### Message Types

- `notification` - Event data
- `webhook_callback_verification` - Challenge verification
- `revocation` - Subscription revoked

### Verification

```
message = message_id + message_timestamp + raw_body
hmac = HMAC-SHA256(secret, message)
Compare with Twitch-Eventsub-Message-Signature (sha256= prefix)
```

---

## EventSub Conduits

For high-scale apps - load balances across multiple shards (WebSocket or Webhook).

### Setup

1. `POST /helix/eventsub/conduits` with `shard_count`
2. `PATCH /helix/eventsub/conduits/shards` to assign transports to shards
3. Webhook shards: handle challenge verification
4. WebSocket shards: assign within 10 seconds of Welcome
5. `POST /helix/eventsub/subscriptions` with `transport.method=conduit`, `conduit_id`

### Scaling

- `PATCH /helix/eventsub/conduits` to change `shard_count`
- Subscribe to `conduit.shard.disabled` for failure detection
- Disabled shards: reassign or swap with last shard and reduce count
- Conduit deleted after 72 hours if all shards disabled

---

## EventSub Subscription Management

### Create Subscription

```
POST https://api.twitch.tv/helix/eventsub/subscriptions
```

### List Subscriptions

```
GET https://api.twitch.tv/helix/eventsub/subscriptions
```

Filter by `type` or `status` (enabled, webhook_callback_verification_pending, authorization_revoked, etc.)

### Delete Subscription

```
DELETE https://api.twitch.tv/helix/eventsub/subscriptions?id={id}
```

### Subscription Costs

- Cost-based limits per client ID + user ID tuple
- No cost for user-authorized subscriptions (e.g., `channel.subscribe`)
- Cost for non-authorized subscriptions (e.g., `stream.online`) unless user authorized app
- Max 3 subscriptions with same type+condition
- WebSocket: max 10 total cost, 300 per connection, 3 connections

---

## Common Event Types Quick Reference

| Event | Version | Condition | Scopes Required |
|-------|---------|-----------|-----------------|
| `channel.follow` | 2 | `broadcaster_user_id`, `moderator_user_id` | `moderator:read:followers` |
| `channel.subscribe` | 1 | `broadcaster_user_id` | `channel:read:subscriptions` |
| `channel.cheer` | 1 | `broadcaster_user_id` | `bits:read` |
| `channel.channel_points_custom_reward_redemption.add` | 1 | `broadcaster_user_id` | `channel:read:redemptions` |
| `stream.online` | 1 | `broadcaster_user_id` | None |
| `stream.offline` | 1 | `broadcaster_user_id` | None |
| `channel.chat.message` | 1 | `broadcaster_user_id`, `user_id` | `user:read:chat` or `channel:bot` |
| `channel.chat.notification` | 1 | `broadcaster_user_id`, `user_id` | `user:read:chat` or `channel:bot` |
| `channel.ban` | 1 | `broadcaster_user_id` | `moderator:manage:banned_users` |
| `channel.unban` | 1 | `broadcaster_user_id` | `moderator:manage:banned_users` |
| `channel.moderate` | 1/2 | `broadcaster_user_id`, `moderator_user_id` | `moderation:read` |
| `channel.hype_train.begin` | 2 | `broadcaster_user_id` | None |
| `channel.goal.begin` | 1 | `broadcaster_user_id` | `channel:read:goals` |
| `channel.poll.begin` | 1 | `broadcaster_user_id` | `channel:read:polls` |
| `channel.prediction.begin` | 1 | `broadcaster_user_id` | `channel:read:predictions` |
| `user.authorization.grant` | 1 | `client_id` | App token |
| `user.authorization.revoke` | 1 | `client_id` | App token |
| `user.update` | 1 | (none) | App token |

Full list: `references/eventsub/eventsub-subscription-types.md`

---

## Files in references/

```
references/
├── authentication/
│   ├── index.md                       # Overview, token types, flows table
│   ├── getting-tokens-oauth.md        # All 4 OAuth flows with examples
│   ├── getting-tokens-oidc.md         # OpenID Connect flows
│   ├── register-app.md                # App registration
│   ├── scopes.md                      # Complete scope reference
│   ├── validate-tokens.md             # Token validation endpoint
│   ├── refresh-tokens.md              # Refresh token flow
│   └── revoke-tokens.md               # Token revocation
├── eventsub/
│   ├── index.md                       # EventSub overview, transports
│   ├── websocket-reference.md         # WebSocket message formats
│   ├── handling-websocket-events.md   # WebSocket client implementation
│   ├── handling-webhook-events.md     # Webhook callback implementation
│   ├── handling-conduit-events.md     # Conduit (sharded) transport
│   ├── manage-subscriptions.md        # CRUD subscriptions, limits, auth rules
│   ├── eventsub-reference.md          # All eventsub conditions, events, field details
│   └── eventsub-subscription-types.md # All event types with payloads
├── api/
│   └── reference.md                   # Helix API reference
└── chat/
    ├── index.md                       # Chatbot overview, types, rate limits
    ├── authenticating.md              # Chatbot auth (user/app tokens, channel:bot)
    ├── send-receive-messages.md       # EventSub chat + Send Chat Message API
    ├── moderation.md                  # Mod actions via API
    ├── whispers.md                    # Whisper API
    └── chatbot-guide.md               # Example chatbot implementation
```