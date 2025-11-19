#!/bin/bash

# Start Firebase Emulators
echo "🔥 Starting Firebase Emulators..."
echo ""
echo "Emulator UI: http://localhost:4000"
echo "Auth Emulator: http://localhost:9099"
echo "Firestore Emulator: http://localhost:8080"
echo "Storage Emulator: http://localhost:9199"
echo ""

firebase emulators:start
