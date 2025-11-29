// lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getStorage, connectStorageEmulator } from 'firebase/storage';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "demo-api-key",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "localhost",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "demo-project",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "demo-bucket",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const storage = getStorage(app);

// Connect to Firebase Auth emulator in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  const authEmulatorHost = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST || 'localhost:9099';
  try {
    // connectAuthEmulator expects format: "localhost:9099" (no http://)
    const emulatorUrl = authEmulatorHost.replace(/^https?:\/\//, '');
    connectAuthEmulator(auth, `http://${emulatorUrl}`, { disableWarnings: true });
    console.log('✅ Connected to Firebase Auth Emulator:', emulatorUrl);
  } catch {
    // Already connected, ignore
  }

  // Connect to Firebase Storage emulator
  const storageEmulatorHost = process.env.NEXT_PUBLIC_FIREBASE_STORAGE_EMULATOR_HOST || 'localhost:9199';
  try {
    const [host, port] = storageEmulatorHost.replace(/^https?:\/\//, '').split(':');
    connectStorageEmulator(storage, host, parseInt(port));
    console.log('✅ Connected to Firebase Storage Emulator:', storageEmulatorHost);
  } catch {
    // Already connected, ignore
  }
}

// Helper to get auth token
export async function getAuthToken(): Promise<string> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated");
  }
  try {
    // Force refresh to get a fresh token (helps with emulator issues)
    return await user.getIdToken(true);
  } catch (error) {
    console.error("Error getting auth token:", error);
    // Fallback: try without forcing refresh
    return await user.getIdToken(false);
  }
}
