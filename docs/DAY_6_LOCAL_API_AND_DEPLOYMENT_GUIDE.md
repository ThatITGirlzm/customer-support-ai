# AVERSE Day 6 — Local API, Deployment, and Frontend Integration Guide

**Prepared:** 2026-11-16  
**Scope:** Local prototype guidance only. No hosting account, provider, notification service, or deployment was configured.

## What is implemented

The application is a local prototype with a FastAPI transport adapter and Pydantic schemas. The service runs the safety preflight before ordinary classification and retrieval, uses the frozen Naive Bayes artifact only for intent candidates, and uses one prototype-configured retriever. The production TF-IDF versus BM25 decision remains deferred.

No answerability catalogue entries are enabled. A candidate retrieval result or score never authorizes a factual answer; ordinary requests therefore abstain until answer rules are separately approved.

The demonstration complaint endpoint is opt-in, loopback-only, and requires an explicit synthetic-demo declaration. It can record a local demonstration complaint and queue a local SQLite notification payload addressed to the runtime-configured demonstration recipient. The notification is not sent by SMS or another channel. The response never exposes the recipient and states that no bank or BoZ submission occurred.

## 1. Local development configuration

Use the project virtual environment. The default 2,000-code-point question cap is configurable and remains provisional under PA-08. It is not an approved policy limit.

From PowerShell, set local process environment values when intentionally running the demonstration:

    $env:AVESE_DEMO_MODE = "true"
    $env:AVESE_DEMO_RECIPIENT_PHONE = Read-Host "Enter the owner-authorized demonstration recipient"
    $env:AVESE_DEMO_OUTBOX_PATH = Join-Path $env:LOCALAPPDATA "Averse\demo-outbox.sqlite3"
    $env:AVESE_EXPERIMENTAL_RETRIEVER = "tfidf"
    $env:AVESE_MAX_QUESTION_CODEPOINTS = "2000"

The value for AVESE_DEMO_RECIPIENT_PHONE is not stored in source code or this guide. Keep it in a local process/session environment; do not place it in a committed file, frontend configuration, logs, or deployment environment. The prototype’s default outbox is under the current user’s local application-data directory, outside the repository. The outbox stores the configured recipient and submitted demonstration text, so use synthetic details only.

AVESE_EXPERIMENTAL_RETRIEVER chooses one local experimental ranker. Setting it to tfidf does not approve TF-IDF as the production winner. The default input cap remains provisional even when supplied via the environment variable. AVESE_CORS_ORIGINS is optional and accepts explicit comma-separated origins; wildcard origins are rejected. CORS is disabled when the variable is empty.

Other settings:

| Variable | Purpose | Default and boundary |
|---|---|---|
| AVESE_DEMO_MODE | Enables the demonstration route | false; route is unavailable unless explicitly enabled |
| AVESE_DEMO_RECIPIENT_PHONE | Local outbox recipient | unset; required for demonstration queueing |
| AVESE_DEMO_OUTBOX_PATH | SQLite outbox location | local application-data directory |
| AVESE_EXPERIMENTAL_RETRIEVER | Selects one local ranker | tfidf prototype default; production selection deferred |
| AVESE_MAX_QUESTION_CODEPOINTS | Request-length cap | 2,000 provisional code points |
| AVESE_CORS_ORIGINS | Explicit browser origins | empty; no cross-origin browser access |

The backend reads environment variables directly; no dotenv package or local environment-file loader has been added.

## 2. Starting the FastAPI backend locally

The API object is app.main:app. The local development dependency set includes the pinned Uvicorn ASGI server. It is used only to run the existing application on the development computer's loopback interface.

Start the local API with:

    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Binding to 127.0.0.1 is required for the local demonstration route. Do not expose the demonstration route through a public host or proxy.

The FastAPI application itself was imported successfully from the project environment. Route tests invoked the ASGI application directly; they did not open a network port.

## 3. API endpoints and local checks

Implemented endpoints:

| Method and path | Purpose | Boundary |
|---|---|---|
| GET /health | Returns basic local-prototype status | Does not expose paths, recipient, or configuration secrets |
| POST /api/v1/requests | Validates and processes a general question | Sensitive preflight cases stop before classifier/retrieval; ordinary questions abstain because no answer rules are approved |
| POST /api/v1/demo/complaints | Records an eligible synthetic demo request and queues a local notification payload | Disabled by default; local client only; requires demo_declaration = SYNTHETIC_DEMO_ONLY |

When the API server is available, FastAPI’s schema page is at /docs and its OpenAPI document is at /openapi.json. These browser/network paths were not exercised because the current environment lacks an ASGI server and HTTP test client.

A synthetic demo request has this shape:

    {
      "question": "Synthetic test: I was scammed and need human help.",
      "demo_declaration": "SYNTHETIC_DEMO_ONLY"
    }

A successful demo response reports RECORDED_LOCAL_ONLY and QUEUED_LOCAL_ONLY, with notification_delivered false, referral_state NOT_SENT, and external_referral_submitted false. It includes a local DEMO complaint ID, not a bank or BoZ complaint reference. No phone number is returned. A local outbox failure reports NOT_RECORDED and NOT_QUEUED rather than a delivery success.

Request-validation errors return stable field/type information without echoing submitted values. The service does not log question text, complaint details, or the configured recipient.

The focused synthetic verification command used for this prototype is:

    .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_app_config.py tests\test_app_safety.py tests\test_inference.py tests\test_app_service.py tests\test_demo_outbox.py tests\test_app_api.py tests\test_retrieval.py tests\test_intent_classifier.py tests\test_text_processing.py

The focused synthetic test set was rerun after installing the local ASGI server dependency and completed with **131 passed in 1.43 seconds**. It did not run the complete project suite, validators, model evaluation, training, or any held-out dataset.

The command deliberately excludes tests that inspect or hash protected datasets. It does not run model evaluation, training, knowledge-base validators, or any held-out dataset.

## 4. Frontend-to-backend connection

The repository includes a React Native/Expo mobile client under mobile/. It uses one configured API base URL, EXPO_PUBLIC_AVERSE_API_BASE_URL, and calls only POST /api/v1/requests. The mobile app does not expose the demonstration route, factual-answer actions, external referrals, SMS, or local data storage.

For the native mobile client, configure a safe simulator-only local base URL. A physical device must not be made to work by binding this prototype's backend publicly or exposing it on a LAN. Browser-origin CORS settings are not required for the React Native client. If a browser frontend is later added, use an exact development origin, never a wildcard. Keep the demonstration route on localhost even if another frontend is added.

The request and response contract remains provisional under PA-09. The demo-specific status fields and wording are authorized only for the controlled demonstration workflow. Do not treat the prototype schema as the final customer-facing contract.

## 5. Hosting provider selection considerations

No hosting provider has been selected. Evaluate any future provider for:

- Python/runtime compatibility and supported ASGI serving.
- HTTPS support, secret/environment management, access controls, and auditability.
- Data location, retention, deletion, backup, and persistence behavior.
- Ability to keep demonstration endpoints private or disabled.
- Persistent storage behavior if an approved production referral workflow is later implemented.
- Cost, account ownership, operational support, and project scope.

Do not choose or create a provider account or incur cost as part of this prototype. A production referral destination and real customer-data handling are still unapproved.

## 6. Deployment preparation and deployment steps

Nothing is deployed. Before a later deployment is considered:

1. Obtain owner and supervisor decisions for all pending policy, answerability, referral, and source-currentness items.
2. Confirm the customer-facing contract, authentication, rate limiting, privacy, retention, and support operations.
3. Keep the demonstration workflow disabled or remove it from a public build. The demonstration recipient is personal and is not an institutional support destination.
4. Select an ASGI server and hosting provider through an approved dependency/deployment decision.
5. Configure secrets and approved runtime settings on the provider, not in source, build output, or frontend assets.
6. Configure explicit production browser origins and HTTPS.
7. Decide on persistent storage and data lifecycle before accepting any real customer details.
8. Deploy only after the service’s safety and operational controls have been reviewed.
9. Verify health, validation errors, source-only abstention behavior, access restrictions, and logs in a non-production environment first.

The current local SQLite outbox is a single-host demonstration mechanism. It is not designed for concurrent multi-instance deployment, durable institutional case management, encryption-at-rest guarantees, or external delivery.

## 7. Provider environment and secrets

Keep AVESE_DEMO_MODE false outside an intentionally controlled local demonstration. Do not set the personal demonstration recipient in a hosted environment. No SMS provider, provider credential, bank integration, or BoZ integration is present.

The demo endpoint checks that the request’s client address is loopback. This is a local prototype guard, not a complete production authentication design. Do not rely on it behind a reverse proxy or expose the route publicly. The demo declaration is an explicit user acknowledgment, not proof that submitted text is synthetic; local-only access and operator discipline remain necessary.

No environment values or provider secrets were added to the repository.

## 8. HTTPS and security

HTTPS is not configured because no server or deployment exists. Any future externally reachable API must use HTTPS and a reviewed authentication/authorization design. Production deployment also needs rate limits, request/body limits at the server or gateway, secure logging, dependency patching, and reviewed CORS origins.

The current API avoids returning classifier probabilities and retrieval scores. It does not provide account access, transactions, or complaint submission to a real institution. Current patterns are deterministic and auditable but cannot guarantee detection of all paraphrased or adversarial safety cases.

## 9. Database and persistence

The demo outbox uses Python’s standard-library SQLite. It stores a local complaint ID, synthetic complaint text, timestamp, notification payload, configured recipient, and QUEUED_LOCAL_ONLY state. It does not store an official reference or delivery acknowledgement. No database file was created by the tests in the repository; tests used temporary directories.

Use only synthetic text with this prototype. The local file inherits the host user’s filesystem permissions and is not encrypted by the application. Retention and deletion policy remain pending. SQLite is not a substitute for a production case-management database or notification provider.

## 10. Verifying a future local run

After an ASGI server is explicitly available:

1. GET /health should return status ok and mode local-prototype.
2. A normal source question should abstain with no factual answer until an answerability rule is approved.
3. A synthetic direct sensitive request to the general route should state that no referral was sent.
4. A synthetic direct sensitive request to the enabled demo route should return a local demo ID, local record/queue states, and explicit no-bank/no-BoZ-submission wording.
5. A non-loopback client should receive 403 on the demo route; with demo mode off, the route should be unavailable.
6. Inspect the local outbox only for synthetic records and confirm notification state is QUEUED_LOCAL_ONLY, never DELIVERED.

Do not send actual complaints or make live SMS tests.

## 11. Troubleshooting

| Symptom | Check |
|---|---|
| Connection refused | Start the pinned local Uvicorn server on 127.0.0.1:8000; FastAPI alone is an ASGI app, not a listening server |
| Uvicorn command is unavailable | Activate the project virtual environment or use .\\.venv\\Scripts\\python.exe -m uvicorn |
| Startup reports model or corpus error | Check the frozen Day 4 model artifact, canonical retrieval corpus, and source-register join; do not substitute validation/test datasets |
| Demo route returns 404 | AVESE_DEMO_MODE is disabled |
| Demo route returns 403 | The request did not come from a loopback client; the demonstration route is local-only |
| Demo route returns service unavailable | Check that the runtime recipient variable and writable local outbox path are configured; do not print the recipient in logs |
| Browser reports CORS failure | Configure the exact frontend origin in AVESE_CORS_ORIGINS and restart the backend |
| No notification arrives on a phone | Expected: the current implementation only queues a local outbox record and has no SMS transport |
| A request abstains despite a retrieval result | Expected until a separately approved answerability rule exists |

## 12. Implemented versus pending

**Implemented and locally tested:** request schemas, safety preflight, Naive Bayes-only artifact adapter, source-register join validation, one prototype retriever, empty answerability gate, FastAPI routes, local SQLite demonstration outbox, loopback/demo-mode controls, focused synthetic tests, and a loopback-only API smoke check. The smoke check confirmed health, ordinary-request abstention, injection blocking, and a sensitive-request response with no referral sent.

**Not configured or not approved:** actual SMS delivery, production referral destination, final response contract, candidate answer rules, production retriever, source-currentness policy, authentication for public deployment, hosting provider, HTTPS, and deployment. The mobile client remains unverified on a device or against a live local API.

No external accounts were created, no costs incurred, and no deployment or live notification was made.
