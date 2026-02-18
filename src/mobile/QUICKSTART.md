# 🚀 Quick Start - Mobile Development in Codespace

## ⚡ Fastest Way to Test

### Step 1: Install Expo Go
- iOS: [App Store](https://apps.apple.com/app/expo-go/id982107779)
- Android: [Play Store](https://play.google.com/store/apps/details?id=host.exp.exponent)

### Step 2: Start Development Server
```bash
cd /workspaces/WAOOAW/src/mobile
npm run start:codespace
```

### Step 3: Connect Your Phone
1. QR code appears in terminal
2. Open Expo Go app
3. Scan QR code
4. App loads on your phone ✨

### Step 4: Make Changes
- Edit files in `src/`
- Save
- App reloads automatically

---

## 📝 Available Commands

```bash
# Start with tunnel (for Codespace)
npm run start:codespace

# Run type checking
npm run typecheck

# Run tests
npm test

# Run type check + tests
npm run validate

# Clear cache and restart
npx expo start --clear
```

---

## 🎯 What Works

✅ **All Features Work via Expo Go:**
- Agent browsing & search
- OAuth login (Google)
- Voice commands
- Firebase Analytics
- Offline caching
- Error boundaries
- Accessibility features

✅ **Hot Reload**: Edit code → Save → See changes instantly

---

## ⚠️ Known Limitations

❌ **Cannot run `expo start` directly in Codespace** (Node 18 vs Expo 54 requires Node 20)

✅ **Workaround**: Use Expo Go with tunnel mode (works perfectly)

---

## 🐛 If Something Goes Wrong

### App won't connect
```bash
# Restart with tunnel
npm run start:codespace
```

### Cache issues
```bash
# Clear Expo cache
npx expo start --clear

# Or full reset
rm -rf .expo node_modules
npm install
npm run start:codespace
```

### Type errors
```bash
# Check for TypeScript errors
npm run typecheck
```

---

## 📱 Current Status

- **Progress**: 49/55 stories (89%)
- **Files**: 93 TypeScript files
- **Dependencies**: All installed
- **Firebase**: Configured with demo environment
- **GCP**: Demo environment ready

---

## 🔗 Useful Links

- [Expo Docs](https://docs.expo.dev)
- [Expo Go Download](https://expo.dev/client)
- [Full Instructions](./CODESPACE_DEV.md)
- [Project Board](../../docs/mobile/implementation_plan.md)

---

**Ready to code? Run `npm run start:codespace` now! 🎉**
