import { signOut } from "firebase/auth";
import { auth } from "../firebase";

export default function RightSidebar({ onSchedule }) {
  return (
    <div className="right-sidebar">

      <button onClick={onSchedule} className="schedule-open-btn">
        Schedule Email
      </button>
      <button onClick={() => signOut(auth)} className="logout-btn">
        Logout
      </button>
    </div>
  );
}