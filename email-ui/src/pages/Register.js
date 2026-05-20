import { useState } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "../firebase";
import { doc, setDoc } from "firebase/firestore";

export default function Register({ onSwitch }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const register = async () => {
    const userCred = await createUserWithEmailAndPassword(auth, email, password);

    await setDoc(doc(db, "users", userCred.user.uid), {
      email,
      role: "user"
    });
  };

  return (
    <div style={styles.container}>
      <h2>Register</h2>

      <input onChange={(e) => setEmail(e.target.value)} placeholder="email" />
      <input type="password" onChange={(e) => setPassword(e.target.value)} placeholder="password" />

      <button onClick={register}>Register</button>

      <p onClick={onSwitch} style={{ cursor: "pointer" }}>
        Already have account?
      </p>
    </div>
  );
}

const styles = {
  container: { width: 300, margin: "auto", marginTop: 100 }
};