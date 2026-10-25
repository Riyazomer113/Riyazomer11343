# 🛰️ Signal Hunt — Full-Stack Live Event System

Signal Hunt is a real-time, interactive signal intelligence and cryptanalysis hunt designed for college events and technical fests.

* **Frontend:** Responsive tactical UI with live polling, station progression, and organizer telemetry.
* **Backend:** High-performance **FastAPI** server with SQLite (WAL mode), HMAC authentication, sliding-window rate limiting, and team progression engine.
* **Capacity:** Configured for **12 Teams** (5 participants per team = **60 total participants**).

---

## 🔑 Event Credentials Summary

| Role / Team | Colour | Access Code / Password |
| :--- | :--- | :--- |
| **Organizer (Host)** | — | **`ISLIEEEECELL`** |
| **Emergency Rearm Code** | — | **`RESET_SIGNAL_HUNT`** |
| **Team 1** | Red | **`REDRACERS2026`** |
| **Team 2** | Black | **`BLACKPANTHERS2026`** |
| **Team 3** | Navy Blue | **`NAVYSHIPS2026`** |
| **Team 4** | Yellow | **`YELLOWYELLOW2026`** |
| **Team 5** | Orange | **`ORANGEBLAZE2026`** |
| **Team 6** | Green | **`GREENVIPERS2026`** |
| **Team 7** | Purple | **`PURPLESTORM2026`** |
| **Team 8** | Grey | **`GREYSHADOWS2026`** |
| **Team 9** | Brown | **`BROWNTITANS2026`** |
| **Team 10** | Peach | **`PEACHPULSE2026`** |
| **Team 11** | Cyan | **`CYANBEACON2026`** |
| **Team 12** | White | **`WHITEGHOSTS2026`** |

*(All team access codes are case-insensitive).*

---

## ☁️ 1-Click Free Deployment on Render.com (Keeps Live 30+ Days)

This repository includes a pre-configured `Dockerfile` and `render.yaml` Blueprint for Render.

### Steps to Deploy:
1. Go to [dashboard.render.com](https://dashboard.render.com/) and sign in with your GitHub account.
2. Click **New +** → **Web Service**.
3. Select your repository: **`qadeer0201/Signal-Hunt`** (Branch: `main`).
4. Render will automatically detect the **Docker** runtime.
5. Select the **Free** instance type.
6. Click **Deploy Web Service**!

Render will build and deploy the application within 2-3 minutes. You will receive a permanent HTTPS link (e.g. `https://signal-hunt.onrender.com`):
* **Participant App:** `https://your-app.onrender.com/`
* **Organizer Telemetry:** `https://your-app.onrender.com/host.html`
* **Interactive API Docs:** `https://your-app.onrender.com/docs`

---

## 💻 Local Quick Start

```bash
chmod +x run.sh
./run.sh
```
Or with Docker:
```bash
docker build -t signal-hunt .
docker run -p 8000:8000 signal-hunt
```

---

## 🎯 Game Structure
* **4 Stations:** Morse Code, Binary/ASCII, FSK Signals, and Cryptographic Nexus.
* **16 Riddles:** 4 sequential riddles per station with strict progression.
* **120-minute live countdown timer:** Controllable by the organizer (Start, Pause, Resume, Reset).
