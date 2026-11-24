# Running Averse — Backend + Expo Go Frontend

## Project layout

```
Customer Support AI/
├── app/                    Python backend (FastAPI)
├── frontend/               React Native / Expo frontend
│   └── src/
│       ├── api/            HTTP client + endpoint functions
│       ├── constants/      Colours, typography, spacing, strings
│       ├── components/     Header, MessageBubble, ResponseCard, …
│       ├── screens/        HomeScreen, ChatScreen, AboutScreen
│       ├── styles/         All StyleSheet files (one per concern)
│       └── navigation/     AppNavigator (React Navigation stack)
├── data/                   Knowledge base, model artifacts
├── .env.example            Backend environment variable template
└── RUNNING.md              ← this file
```

---

## 1 — Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Python | 3.12 | python.org |
| Node.js | 18 LTS | nodejs.org |
| npm | 9+ | bundled with Node |
| Expo Go app | latest | iOS App Store / Google Play |

---

## 2 — Set up the backend

### 2a. Create and activate the virtual environment (first time only)

```powershell
# From the project root
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2b. Configure environment variables

```powershell
# Copy the template
Copy-Item .env.example .env
```

Open `.env` and set `AVESE_CORS_ORIGINS` to include the Expo Metro bundler
origin.  The default value (`http://localhost:8081,http://127.0.0.1:8081`)
works for simulators and the web browser.

**Physical device (Expo Go on Android/iOS):**
Find your machine's LAN IP address:

```powershell
ipconfig | Select-String "IPv4"
```

Then add it to `AVESE_CORS_ORIGINS` in `.env`, e.g.:

```
AVESE_CORS_ORIGINS=http://localhost:8081,http://192.168.1.42:8081
```

### 2c. Start the backend

```powershell
# With the virtual environment active, from the project root:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
Verify it is running: open `http://localhost:8000/health` in your browser —
you should see `{"status":"ok","mode":"local-prototype"}`.

---

## 3 — Set up the frontend

### 3a. Install dependencies (first time only)

```powershell
cd frontend
npm install
```

This installs Expo, React Native, React Navigation, and all peer dependencies.

### 3b. Configure the backend URL

Open `frontend/src/api/client.js` and check `BASE_URL`:

```js
export const BASE_URL = 'http://localhost:8000';
```

- **Android emulator:** change to `http://10.0.2.2:8000`
- **Physical device:** change to your machine's LAN IP, e.g. `http://192.168.1.42:8000`
- **iOS Simulator / web:** `http://localhost:8000` works as-is

### 3c. Start the Expo development server

```powershell
# From the frontend/ directory:
npx expo start
```

Expo will print a QR code in the terminal.

---

## 4 — Open the app in Expo Go

1. Install the **Expo Go** app on your phone (iOS App Store or Google Play).
2. Make sure your phone is on the **same Wi-Fi network** as your computer.
3. Scan the QR code from the terminal with:
   - **iOS:** the standard Camera app
   - **Android:** the Expo Go app's QR scanner
4. The Averse app will load in Expo Go.

For an Android emulator or iOS Simulator running on the same machine, press
`a` or `i` in the Expo terminal to open automatically.

---

## 5 — CORS at a glance

The backend reads `AVESE_CORS_ORIGINS` from the environment at startup and
passes those origins to FastAPI's `CORSMiddleware`.  The middleware only
activates when at least one origin is listed — if the variable is empty, no
CORS headers are added (which is fine for server-to-server or same-origin use).

Expo Go makes requests from the Metro bundler origin (`http://<your-ip>:8081`
in the `Origin` header).  As long as that origin is in `AVESE_CORS_ORIGINS`,
all three API routes (`/health`, `/api/v1/requests`, `/api/v1/demo/complaints`)
will respond correctly.

**No code changes to the backend are required** — only the `.env` value.

---

## 6 — Common issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "Could not reach the Averse service" | Backend not running | Start `uvicorn` (step 2c) |
| "Could not reach the Averse service" on device | Wrong `BASE_URL` | Set LAN IP in `client.js` |
| CORS error in browser console | Origin not listed | Add origin to `AVESE_CORS_ORIGINS` in `.env`, restart uvicorn |
| Health check shows ✗ in About screen | Same as above | Same fix |
| `npm install` hangs | Slow network | Wait; it will complete |
| `Module not found: @react-navigation/…` | `npm install` incomplete | Run `npm install` again in `frontend/` |
| Android emulator can't reach backend | Wrong emulator IP | Use `http://10.0.2.2:8000` in `BASE_URL` |

---

## 7 — Running both servers side-by-side (Windows)

Open two PowerShell terminals:

**Terminal 1 — backend**
```powershell
cd "Customer Support AI"
.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — frontend**
```powershell
cd "Customer Support AI\frontend"
npx expo start
```
