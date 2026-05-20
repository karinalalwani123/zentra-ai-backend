export default function ChatHistory({ chats }) {
  return (
    <div className="chat-list">
      {chats.length === 0 ? (
        <p className="no-chats">No chats yet</p>
      ) : (
        chats.map((c, i) => (
          <div key={i} className="chat-item">
            {c.title || "New Chat"}
          </div>
        ))
      )}
    </div>
  );
}