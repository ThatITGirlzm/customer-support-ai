# Averse Support Mobile

A native React Native app built with Expo. It connects only to `POST /api/v1/requests` and keeps no question history or credentials on the device. The local demo complaint route is not included in the app.

## Setup

Requirements: Node.js 22.13 or newer and npm. This project uses Expo SDK 58, React 19.3, React Native 0.88, and `react-native-safe-area-context`.

From this folder:

```powershell
Copy-Item .env.example .env.local
npm install
npm run start
```

The API URL is configured through `EXPO_PUBLIC_AVERSE_API_BASE_URL`. It is not a secret; do not put credentials or tokens in an `EXPO_PUBLIC_` variable. The default `http://127.0.0.1:8000` is for a local simulator only.

For an Android emulator, with the Python service already listening on `127.0.0.1:8000` on the development computer, use Android Debug Bridge port reversal:

```powershell
adb reverse tcp:8000 tcp:8000
```

For an iOS simulator on the same Mac as the local service, `127.0.0.1` can address the development host. A physical phone cannot reach a host loopback address. This project does not configure a public server or an exposed LAN backend; do not bind the service publicly to make a device connect.

The existing Python environment previously had no ASGI server installed. Start the backend only in an environment where its already-approved local ASGI server is available, bound to loopback. No live backend connection is claimed by this guide.

## Interface behavior

- Home offers editable topic question starters; choosing one does not send it.
- Support posts only `{ "question": "..." }` to the configured ordinary-request endpoint.
- The app displays the server’s response text as native text for the five approved non-answer actions: `ABSTAIN_NOT_IN_SOURCES`, `BLOCK_INJECTION`, `REFER_HUMAN`, `INVALID_REQUEST`, and `SERVICE_UNAVAILABLE`.
- Unknown actions, including factual-answer actions, are not displayed. The app does not create facts, citations, referral claims, or official reference numbers.
- Questions are cleared when sent and are not written to device storage. The app has no chat-history, analytics, or logging package.
- Do not enter passwords, PINs, one-time codes, full account numbers, or other credentials.

## Accessibility checklist

- Meaningful labels, hints, button roles, selected states, headings, and a polite response announcement are provided.
- Text uses React Native font scaling; no fixed text heights or maximum font scale are set.
- Buttons and navigation controls have at least 54 dp height, generous padding, visible pressed/focused styling, and keyboard focus support.
- Screen content follows a logical reading order and scrolls when enlarged text needs more space.
- Text/background pairs use dark foregrounds on off-white, mint, and sand surfaces. Static contrast calculations give at least 4.82:1 for the text pairs and 3.49:1 for the neutral outline against off-white; labels accompany every status so colour is never the only signal.
- The client sends no credentials and renders backend strings in native `Text` components, never as HTML or executable markup.

## Current limits

The current backend normally abstains because no answer rules are approved. The app does not enable factual answer generation, external referral, SMS, demo complaints, or public deployment. The backend’s demo endpoint remains absent from the mobile interface.
