# app01 — macOS Notarized Flask App

A template for building a notarized macOS `.app` and `.pkg` installer from a Python/Flask web application using py2app. The app runs a local web server and opens a browser UI automatically.

---

## Architecture

The app uses a two-server architecture:

| Server | Port | Purpose |
|--------|------|---------|
| Waitress (Flask API) | 5401 | Handles API requests from the browser |
| Python http.server | 5402 | Serves static HTML/JS/CSS files |

On launch, the app:
1. Checks if the API server is already running on port 5401
2. If yes — opens a new browser tab and exits (no duplicate server)
3. If no — kills any stale processes on ports 5401/5402, starts both servers, opens the browser

---

## Project Files

| File | Purpose |
|------|---------|
| `app01.py` | Main Python app — Flask API + static server + launch logic |
| `app01_index.html` | Frontend UI served by the static server |
| `setup_app01.py` | py2app build configuration |
| `build_and_notarize_app01.sh` | Full build, sign, notarize, and package script |
| `.env` | Apple Developer credentials (never commit this) |
| `.env.example` | Template for `.env` |

---

## Prerequisites

### Apple Developer Account
- Paid Apple Developer Program membership ($99/year)
- Two certificates from [developer.apple.com](https://developer.apple.com) → Certificates → "+":
  - **Developer ID Application** — for signing the `.app`
  - **Developer ID Installer** — for signing the `.pkg`

Import both into your Keychain:
```bash
security import developerID_application.cer -k ~/Library/Keychains/login.keychain-db
security import developerID_installer.cer -k ~/Library/Keychains/login.keychain-db
```

Verify:
```bash
security find-identity -v -p codesigning | grep "Developer ID"
```

### App-Specific Password
1. Go to [appleid.apple.com](https://appleid.apple.com) → Sign-In and Security → App-Specific Passwords
2. Generate a new password and save it

### Python Environment
```bash
uv venv env1 --python 3.12
source env1/bin/activate
pip install flask flask-cors waitress py2app
```

> **Important**: Use Homebrew Python 3.12, not uv's standalone build.
> uv's standalone Python has a built-in `zlib` with no `__file__` attribute,
> which causes py2app to fail. Use `/opt/homebrew/bin/python3.12` instead.

---

## Configuration

### .env file
Create `.env` in the project root:
```
APPLE_ID="your@email.com"
TEAM_ID="YOUR_TEAM_ID"
APP_CERT="Developer ID Application: Your Name (YOUR_TEAM_ID)"
PKG_CERT="Developer ID Installer: Your Name (YOUR_TEAM_ID)"
APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"
KEYCHAIN="$HOME/Library/Keychains/login.keychain-db"
```

### Ports
Defined at the top of `app01.py`:
```python
API_PORT    = 5401   # Flask/Waitress API server
STATIC_PORT = 5402   # Static file server
```

Change these if they conflict with other apps on the machine.

### Version
Defined in both `app01.py` and `setup_app01.py`:
```python
VERSION = '1.0.1'
```

---

## Build & Distribute

```bash
source env1/bin/activate
./build_and_notarize_app01.sh 2>&1 | tee build.log
```

The script does the following steps:
1. Rebuilds the `.app` bundle using py2app
2. Signs all `.so`, `.dylib`, and Python binaries with Developer ID Application cert
3. Signs the Python framework inside the bundle
4. Signs the `.app` bundle
5. Notarizes the `.app` with Apple
6. Staples the notarization ticket to the `.app`
7. Packages into a `.pkg` installer
8. Signs the `.pkg` with Developer ID Installer cert
9. Notarizes and staples the `.pkg`

Output: `app01-1.0.1-signed.pkg`

Send this file to the end user.

---

## Installation (End User)

1. Double-click `app01-1.0.1-signed.pkg`
2. Follow the installer wizard
3. App installs to `/Applications/app01.app`
4. Double-click the app to launch — browser opens automatically

No Python, no terminal, no developer tools required on the end user's machine.

---

## Multiple Launches

The app handles multiple launches correctly:
- First launch: starts both servers and opens browser
- Subsequent launches: detects servers already running, opens a new browser tab only
- After closing the browser: click the app icon again to reopen the browser

---

## Adding New API Endpoints

Add routes to `app01.py`:
```python
@app.route("/api/your-endpoint", methods=["POST"])
def your_endpoint():
    data = request.get_json()
    # your logic here
    return jsonify({"result": "..."})
```

Call from `app01_index.html`:
```javascript
const res = await fetch('http://localhost:5401/api/your-endpoint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({key: value})
});
```

---

## Troubleshooting

### Notarization fails with "agreement expired"
Go to [developer.apple.com](https://developer.apple.com), sign in, and accept the updated Apple Developer Program License Agreement.

### "Ambiguous certificate" error during signing
You have duplicate certificates in Keychain. Delete duplicates:
```bash
security find-identity -v -p codesigning | grep "Developer ID"
security delete-certificate -Z <HASH> ~/Library/Keychains/login.keychain-db
```

### App bounces in Dock but doesn't open (second launch)
Stale processes on ports 5401/5402. The app handles this automatically on startup. If it persists:
```bash
lsof -ti :5401 | xargs kill -9
lsof -ti :5402 | xargs kill -9
```

### py2app fails with "zlib has no attribute __file__"
You're using uv's standalone Python. Switch to Homebrew Python 3.12:
```bash
brew install python@3.12
rm -rf env1
/opt/homebrew/bin/python3.12 -m venv env1
source env1/bin/activate
pip install flask flask-cors waitress py2app
```

### Notarization timeout
Apple's servers occasionally time out. Just retry:
```bash
./build_and_notarize_app01.sh 2>&1 | tee build.log
```
