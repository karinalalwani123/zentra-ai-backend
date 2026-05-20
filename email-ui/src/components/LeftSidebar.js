import { signOut } from "firebase/auth";
import { auth } from "../firebase";

export default function LeftSidebar({ chats, activeChatId, setActiveChatId, newChat }) {
  return (
    <div className="left-sidebar">

      <div className="sidebar-header">
        <h2>ZENTRA AI</h2>
        <button onClick={newChat} className="new-chat-btn">
          + New Chat
        </button>
      </div>

      <div className="chat-list">
        {chats.length === 0 ? (
          <p className="no-chats">No chats yet</p>
        ) : (
          chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => setActiveChatId(chat.id)}
              className={`chat-item ${chat.id === activeChatId ? "active" : ""}`}
            >
              {chat.title || "New Chat"}
            </div>
          ))
        )}
      </div>


    </div>
  );
}