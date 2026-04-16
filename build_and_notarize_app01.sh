#!/bin/bash
set -e

# ── Load credentials from .env ───────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "Error: .env file not found. Copy .env.example to .env and fill in your credentials."
  exit 1
fi
set -a; source .env; set +a
# ────────────────────────────────────────────────────────────────────────────
# openssl x509 -inform DER -in developerID_application.cer -noout -subject

APP_NAME="app01"
VERSION="1.0.1"
PKG_NAME="$APP_NAME-$VERSION"

echo "==> Rebuilding app..."
rm -rf build dist
python3.12 setup_app01.py py2app

echo "==> Signing binaries..."
find dist/$APP_NAME.app -type f \( -name "*.so" -o -name "*.dylib" -o -name "Python" -o -name "Python3" -o -name "python" -o -name "python3" \) | xargs -I {} \
  codesign --force \
  --sign "$APP_CERT" \
  --keychain "$KEYCHAIN" \
  --options runtime --timestamp {}

echo "==> Signing Python framework..."
find dist/$APP_NAME.app -name "Python.framework" -type d | while read fw; do
  codesign --force --sign "$APP_CERT" --keychain "$KEYCHAIN" --options runtime --timestamp "$fw/Versions/Current/Python"
  codesign --force --sign "$APP_CERT" --keychain "$KEYCHAIN" --options runtime --timestamp "$fw/Versions/Current"
  codesign --force --sign "$APP_CERT" --keychain "$KEYCHAIN" --options runtime --timestamp "$fw"
done

echo "==> Signing app bundle..."
codesign --force --verify --verbose \
  --sign "$APP_CERT" \
  --keychain "$KEYCHAIN" \
  --options runtime --timestamp \
  dist/$APP_NAME.app

echo "==> Notarizing app..."
ditto -c -k --keepParent dist/$APP_NAME.app dist/$APP_NAME.zip
xcrun notarytool submit dist/$APP_NAME.zip \
  --apple-id "$APPLE_ID" \
  --team-id "$TEAM_ID" \
  --password "$APP_PASSWORD" \
  --wait

echo "==> Stapling app..."
xcrun stapler staple dist/$APP_NAME.app
spctl --assess --verbose dist/$APP_NAME.app

echo "==> Building PKG..."
pkgbuild --component dist/$APP_NAME.app \
  --install-location /Applications \
  $PKG_NAME.pkg

productsign --sign "$PKG_CERT" \
  --keychain "$KEYCHAIN" \
  $PKG_NAME.pkg $PKG_NAME-signed.pkg
rm $PKG_NAME.pkg

echo "==> Notarizing PKG..."
xcrun notarytool submit $PKG_NAME-signed.pkg \
  --apple-id "$APPLE_ID" \
  --team-id "$TEAM_ID" \
  --password "$APP_PASSWORD" \
  --wait

echo "==> Stapling PKG..."
xcrun stapler staple $PKG_NAME-signed.pkg

echo ""
echo "Done! Send $PKG_NAME-signed.pkg to the other user."
