import { useState } from "react";
import { auth } from "../firebase";
import { signInWithEmailAndPassword } from "firebase/auth";

export default function Login({ onSwitchToRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const login = async () => {
    try {
      setError("");
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h2>ZENTRA AI Assistant</h2>
        <p className="auth-subtitle">Login to your account</p>

        {error && <p className="auth-error">{error}</p>}

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
          onKeyDown={(e) => e.key === "Enter" && login()}
        />

        <div className="auth-buttons">
          <button className="auth-btn-login" onClick={login}>Login</button>
        </div>

        <p className="auth-switch">
          Don't have an account?{" "}
          <span className="auth-link" onClick={onSwitchToRegister}>
            Register
          </span>
        </p>
      </div>
    </div>
  );
}