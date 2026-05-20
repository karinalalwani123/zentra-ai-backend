import { useState, useEffect } from "react";
import axios from "axios";
import { onAuthStateChanged } from "firebase/auth";
import { addDoc, collection, serverTimestamp, doc, getDoc } from "firebase/firestore";
import { auth, db } from "./firebase";
import { useChat } from "./hooks/useChat";

import LeftSidebar from "./components/LeftSidebar";
import RightSidebar from "./components/RightSidebar";
import ChatWindow from "./components/ChatWindow";
import Auth from "./components/Auth";
import AdminPanel from "./pages/AdminPanel";
import ScheduleEmail from "./pages/ScheduleEmail";

import "./App.css";

export default function App() {
  const [input, setInput] = useState("");
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [showScheduler, setShowScheduler] = useState(false);

  const {
    chats,
    activeChatId,
    setActiveChatId,
    messages,
    setMessages,
    newChat,
    saveMessage,
    updateChatTitle,
    setMessageFlagsById,
  } = useChat();

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        const snap = await getDoc(doc(db, "users", firebaseUser.uid));
        setRole(snap.exists() ? snap.data().role : "user");
      } else {
        setRole(null);
      }
      setAuthLoading(false);
    });
    return () => unsub();
  }, []);

  const getChatId = async (text) => {
    if (activeChatId) return activeChatId;
    const ref = await addDoc(collection(db, "users", user.uid, "chats"), {
      title: text.slice(0, 30),
      createdAt: serverTimestamp(),
    });
    setActiveChatId(ref.id);
    return ref.id;
  };

  const sendMessage = async () => {
    if (!input.trim() || !user) return;

    const text = input;
    setInput("");

    const chatId = await getChatId(text);
    await saveMessage(chatId, "user", text);

    if (messages.length === 0) {
      await updateChatTitle(chatId, text.slice(0, 30));
    }

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: text,
      });

      console.log("API response:", res.data);

      const msgId = await saveMessage(chatId, "bot", res.data.response);

      if (msgId) {
        setMessageFlagsById(msgId, {
          isDraft: res.data.is_draft || false,
          draft: res.data.draft || null,
          isEmailList: res.data.is_email_list || false,
          emails: res.data.emails || [],
        });
      }

    } catch (err) {
      console.error("Error:", err);
      await saveMessage(chatId, "bot", "Error connecting to backend");
    }
  };

  const onSendDraft = async (draft) => {
    if (!draft) return;
    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: "send",
      });

      setMessages((prev) =>
        prev.map((m) =>
          m.isDraft ? { ...m, isDraft: false, draft: null } : m
        )
      );

      if (activeChatId) {
        await saveMessage(activeChatId, "bot", res.data.response);
      }
    } catch (err) {
      if (activeChatId) {
        await saveMessage(activeChatId, "bot", "❌ Failed to send email.");
      }
    }
  };

  const onCancelDraft = async (msgIndex) => {
    try {
      await axios.post("http://127.0.0.1:8000/chat", {
        message: "cancel",
      });

      setMessages((prev) =>
        prev.map((m, i) =>
          i === msgIndex ? { ...m, isDraft: false, draft: null } : m
        )
      );
    } catch (err) {
      console.error("Cancel failed:", err);
    }
  };

  const onAutoReply = async (emailIndex) => {
    if (!user) return;

    const chatId = await getChatId(`auto reply to email ${emailIndex}`);

    // Show locally without saving to Firebase
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text: `✍️ Auto replying to email ${emailIndex}...`,
        id: `local-${Date.now()}`,
      },
    ]);

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        message: `auto reply to email ${emailIndex}`,
      });

      const msgId = await saveMessage(chatId, "bot", res.data.response);

      if (msgId && res.data.is_draft) {
        setMessageFlagsById(msgId, {
          isDraft: res.data.is_draft || false,
          draft: res.data.draft || null,
        });
      }

    } catch (err) {
      await saveMessage(chatId, "bot", "❌ Failed to generate reply.");
    }
  };

  if (authLoading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!user) {
    return <Auth />;
  }

  if (role === "admin") {
    return <AdminPanel />;
  }

  if (showScheduler) {
    return <ScheduleEmail onBack={() => setShowScheduler(false)} />;
  }

  return (
    <div className="app-shell">
      <LeftSidebar
        chats={chats}
        activeChatId={activeChatId}
        setActiveChatId={setActiveChatId}
        newChat={newChat}
      />
      <ChatWindow
        messages={messages}
        input={input}
        setInput={setInput}
        sendMessage={sendMessage}
        onSendDraft={onSendDraft}
        onCancelDraft={onCancelDraft}
        onAutoReply={onAutoReply}
      />
      <RightSidebar onSchedule={() => setShowScheduler(true)} />
    </div>
  );
}