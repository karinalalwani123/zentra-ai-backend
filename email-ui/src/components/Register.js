import { useState } from "react";
import { auth, db } from "../firebase";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc } from "firebase/firestore";

export default function Register({ onSwitchToLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const register = async () => {
    try {
      setError("");
      setSuccess("");

      if (!email || !password) {
        setError("Please fill in all fields.");
        return;
      }

      if (password !== confirm) {
        setError("Passwords do not match.");
        return;
      }

      if (password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }

      if (email === "admin@gmail.com") {
        setError("This account already exists. Please login.");
        return;
      }

      const userCred = await createUserWithEmailAndPassword(auth, email, password);
      await setDoc(doc(db, "users", userCred.user.uid), {
        email,
        role: "user",
      });

      setSuccess("Account created! Redirecting to login...");
      setTimeout(() => onSwitchToLogin(), 1500);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h2>AI Assistant</h2>
        <p className="auth-subtitle">Create a new account</p>

        {error && <p className="auth-error">{error}</p>}
        {success && <p className="auth-success">{success}</p>}

        <input
          className="auth-input"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="auth-input"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <input
          className="auth-input"
          type="password"
          placeholder="Confirm Password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && register()}
        />

        <div className="auth-buttons">
          <button className="auth-btn-register" onClick={register}>Register</button>
        </div>

        <p className="auth-switch">
          Already have an account?{" "}
          <span className="auth-link" onClick={onSwitchToLogin}>
            Login
          </span>
        </p>
      </div>
    </div>
  );
}