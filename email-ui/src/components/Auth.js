import { useState } from "react";
import Login from "./Login";
import Register from "./Register";

export default function Auth() {
  const [page, setPage] = useState("login");

  return page === "login" ? (
    <Login onSwitchToRegister={() => setPage("register")} />
  ) : (
    <Register onSwitchToLogin={() => setPage("login")} />
  );
}