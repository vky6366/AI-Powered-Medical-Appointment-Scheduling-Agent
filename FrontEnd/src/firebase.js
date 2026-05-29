import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCWbRRbOxNbomaxiZIwNciv9jVyq1YsPj8",
  authDomain: "medical-appointment-85be7.firebaseapp.com",
  projectId: "medical-appointment-85be7",
  storageBucket: "medical-appointment-85be7.firebasestorage.app",
  messagingSenderId: "1040073547725",
  appId: "1:1040073547725:web:68c674ce74632dfa17ae84",
  measurementId: "G-45NMD1KTFH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Services
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
