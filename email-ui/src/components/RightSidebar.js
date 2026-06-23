import { signOut } from "firebase/auth";
import { auth } from "../firebase";

export default function RightSidebar() {
  return (
    <div className="right-sidebar">
      <button onClick={() => signOut(auth)} className="logout-btn">
        Logout
      </button>
    </div>
  );
}