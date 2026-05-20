import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDR8BRFRz587lhNLA2NBH8kdJrJI5v5GII",
  authDomain: "emailassistant-d737b.firebaseapp.com",
  projectId: "emailassistant-d737b",
  storageBucket: "emailassistant-d737b.firebasestorage.app",
  messagingSenderId: "332757522958",
  appId: "1:332757522958:web:f7cb9ad371dee5508d7a5f",
  measurementId: "G-0KQ864MY6Q"
};

// Initialize Firebase
// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Export services
export const auth = getAuth(app);
export const db = getFirestore(app);



