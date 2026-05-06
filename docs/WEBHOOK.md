# Webhook Setup (Meta WhatsApp Cloud API)

This document explains how to register your local instance with Meta so it
receives WhatsApp messages.

## Prerequisites

- A Meta for Developers account: https://developers.facebook.com
- A WhatsApp Business app with Cloud API enabled
- A test phone number provisioned in the Meta dashboard
- ngrok or any other HTTPS tunnel for local development

## Step 1: Configure your environment

Copy `.env.example` to `.env` and fill the Meta values:

```
META_VERIFY_TOKEN=any-string-you-pick   # used in the GET handshake
META_APP_SECRET=...                     # from Meta dashboard, App Settings -> Basic
META_PHONE_NUMBER_ID=...                # from Meta dashboard, WhatsApp -> API Setup
META_ACCESS_TOKEN=...                   # temporary or system user token
```

## Step 2: Run the app locally

```bash
make install
make run
```

The app listens on http://localhost:8000.

Verify health:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## Step 3: Expose via ngrok

In another terminal:

```bash
ngrok http 8000
```

Note the HTTPS URL (e.g. `https://a1b2c3d4.ngrok-free.app`).

## Step 4: Register the webhook in Meta

1. Open https://developers.facebook.com -> your app -> **WhatsApp** -> **Configuration**
2. Under **Webhook**, click **Edit**
3. Set **Callback URL** to `https://YOUR-NGROK-URL/webhook`
4. Set **Verify token** to the same value you used for `META_VERIFY_TOKEN`
5. Click **Verify and save**

If your token matches, Meta will issue a GET to `/webhook` with
`hub.mode=subscribe`, `hub.challenge=...`, `hub.verify_token=...` and expects
the challenge echoed back. Our endpoint does that automatically.

After saving, subscribe to the **messages** field.

## Step 5: Send a test message

Send a WhatsApp message from any phone to your Meta test number. You should see
a structured log line in the app output similar to:

```
[info] webhook_received object=whatsapp_business_account entries=1 total_changes=1
```

## Troubleshooting

### Meta shows "The callback URL or verify token couldn't be validated"

- Double-check `META_VERIFY_TOKEN` matches exactly (no trailing spaces).
- Ensure ngrok is forwarding to port 8000 and the app is running.
- Hit `https://YOUR-NGROK-URL/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=YOUR_TOKEN`
  manually; you should get `test` back as plain text.

### POST returns 401

- The header `X-Hub-Signature-256` must be a valid HMAC-SHA256 of the raw body
  using `META_APP_SECRET`. If you are testing manually with curl, sign first.
- Confirm `META_APP_SECRET` matches the value from your Meta App Settings.

### Webhook receives nothing after subscribing

- Check Meta's webhook **Recent Deliveries** panel for retries and 4xx/5xx
  responses.
- Make sure you subscribed to the **messages** field.
- ngrok free tier expires the URL when ngrok stops. Re-register the new URL.

## What is *not* implemented yet (M02 scope)

- Sending replies (uses Meta Send API; planned for M05+)
- Idempotency / dedupe (planned for v0.2.0+)
- Interactive buttons / list messages (planned for v0.2.0+)
- Template messages outside the 24h window (planned for v0.2.0+)
