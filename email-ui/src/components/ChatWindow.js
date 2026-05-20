import ReactMarkdown from "react-markdown";

const CATEGORY_CONFIG = {
  spam:      { label: "Spam",      emoji: "🚨", className: "badge-spam"      },
  promotion: { label: "Promotion", emoji: "🎯", className: "badge-promotion" },
  replying:  { label: "Reply",     emoji: "💬", className: "badge-replying"  },
  important: { label: "Important", emoji: "📌", className: "badge-important" },
};

export default function ChatWindow({
  messages,
  input,
  setInput,
  sendMessage,
  onSendDraft,
  onCancelDraft,
  onAutoReply,
}) {
  const startMic = async () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Not supported");
      return;
    }

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      alert("Mic permission denied: " + err.message);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => console.log("🎤 Listening...");
    recognition.onresult = (e) => {
      setInput(e.results[0][0].transcript);
    };
    recognition.onerror = (e) => console.error("Error:", e.error);
    recognition.onend = () => console.log("Stopped");

    recognition.start();
  };

  const renderEmailDraft = (text) => {
    const lines = text.split("\n");
    return (
      <div className="email-draft">
        {lines.map((line, i) => {
          if (line.startsWith("To:")) {
            return (
              <div key={i} className="email-field">
                <span className="email-label">To:</span>
                <span className="email-value">{line.replace("To:", "").trim()}</span>
              </div>
            );
          }
          if (line.startsWith("Subject:")) {
            return (
              <div key={i} className="email-field">
                <span className="email-label">Subject:</span>
                <span className="email-value">{line.replace("Subject:", "").trim()}</span>
              </div>
            );
          }
          if (line.startsWith("Body:")) {
            return <div key={i} className="email-body-label">Body:</div>;
          }
          if (line.trim() === "") {
            return <br key={i} />;
          }
          return <p key={i} className="email-body-line">{line}</p>;
        })}
      </div>
    );
  };

  const renderEmailCards = (emails) => {
    return (
      <div className="email-card-list">
        {emails.map((email, i) => {
          const config = CATEGORY_CONFIG[email.category] || CATEGORY_CONFIG.important;
          return (
            <div key={i} className={`email-card email-card-${email.category}`}>
              <div className="email-card-header">
                <div className="email-card-meta">
                  <span className="email-card-from">{email.from}</span>
                  <span className="email-card-date">{email.date}</span>
                </div>
                <span className={`email-category-badge ${config.className}`}>
                  {config.emoji} {config.label}
                </span>
              </div>
              <p className="email-card-subject">{email.subject}</p>
              <p className="email-card-preview">{email.snippet}</p>
              {email.reason && (
                <p className="email-card-reason">💡 {email.reason}</p>
              )}
              {email.should_reply && (
                <button
                  className="email-auto-reply-btn"
                  onClick={() => onAutoReply(i + 1)}
                >
                  ✍️ Auto Reply
                </button>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="chat-window">
      <div className="chat-header">ZENTRA AI</div>

      <div className="chat-body">
        {messages.length === 0 ? (
          <div className="empty-state">Start a conversation</div>
        ) : (
          messages.map((msg, i) => (
            <div key={msg.id || i} className={`message ${msg.role}`}>

              {msg.role === "bot" && msg.isEmailList && msg.emails?.length > 0 ? (
                <div className="bubble">
                  <p className="email-list-title">{msg.text}</p>
                  {renderEmailCards(msg.emails)}
                </div>
              ) : (
                <div className="bubble">
                  {msg.role === "bot" ? (
                    msg.isDraft === true ? (
                      renderEmailDraft(msg.text)
                    ) : (
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    )
                  ) : (
                    msg.text
                  )}
                </div>
              )}

            </div>
          ))
        )}
      </div>

      <div className="input-bar">
        <input
          placeholder="Type or speak..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={startMic} className="mic-btn">🎤</button>
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}