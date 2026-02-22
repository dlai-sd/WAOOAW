# WAOOAW Mobile - Codespace Development Guide

## 🚀 Quick Start

### Option 1: Expo Go on Your Phone (Recommended)

Best for rapid iterations and testing real mobile features.

```bash
cd /workspaces/WAOOAW/src/mobile
npm start -- --tunnel
```

1. Install [Expo Go](https://expo.dev/client) on your phone
2. Scan QR code shown in terminal
3. App loads on your phone
4. Hot reload on file changes

**Pros**: Real device, all features work, fast reload  
**Cons**: Requires phone with Expo Go

---

### Option 2: Code Validation (No Runtime)

Validate code without running the app.

```bash
cd /workspaces/WAOOAW/src/mobile

# Type checking
npm run typecheck

# Linting (needs ESLint config update)
npm run lint

# Run tests
npm test
```

**Pros**: Fast, works in Codespace  
**Cons**: No visual feedback, no runtime testing

---

### Option 3: EAS Build Preview

Build actual APK/IPA for testing.

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build for Android (takes 10-15 min)
eas build --profile development --platform android

# Build for iOS (requires Apple Developer account)
eas build --profile development --platform ios
```

**Pros**: Real builds, test on any device  
**Cons**: Slow (10-15 min per build), requires EAS account

---

## 🔧 Development Workflow

### Recommended: Expo Go + Tunnel

```bash
# Start development server
./start-codespace.sh

# Or manually:
npx expo start --tunnel --port 8081
```

**What happens:**
1. Expo creates secure tunnel to Codespace
2. QR code generated for Expo Go app
3. Phone connects via tunnel
4. Edit code → Save → App reloads

**Hot Reload:**
- JS changes: Instant reload
- Native changes: Need rebuild

---

## 📱 Testing Strategy

### Level 1: Code Validation
```bash
npm run typecheck   # Type errors
npm test           # Unit tests
```

### Level 2: Visual Testing
```bash
npm start -- --tunnel   # Expo Go on phone
```

### Level 3: Build Testing
```bash
eas build --profile preview   # Real APK/IPA
```

---

## 🐛 Troubleshooting

### "Could not connect to development server"
- Check tunnel is active
- Restart Expo Go app
- Try different WiFi network

### "Node version mismatch"
- Codespace has Node 18
- Expo 54 needs Node 20
- Use EAS Build or Expo Go (both work)

### "Metro bundler not starting"
- Clear cache: `npx expo start --clear`
- Delete .expo folder
- Reinstall: `rm -rf node_modules && npm install`

---

## 📦 Current Setup

**Environment**: GitHub Codespace (Node 18)  
**App**: React Native 0.81.5 + Expo 54  
**Status**: 49/55 stories complete (89%)  
**Blockers**: None (Expo Go works, EAS Build works)

**Files**:
- 93 TypeScript files
- Firebase configured
- GCP demo environment ready
- All dependencies installed

---

## 🎯 Next Steps

1. **Install Expo Go** on your phone
2. **Run** `npm start -- --tunnel`
3. **Scan QR** code with Expo Go
4. **Edit** files in `/src/mobile/src/`
5. **Watch** hot reload on phone

**Need help?** Check [Expo Docs](https://docs.expo.dev/get-started/create-a-project/)
