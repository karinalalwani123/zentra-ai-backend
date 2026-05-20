import { useState, useEffect, useRef } from "react";
import {
  collection,
  addDoc,
  query,
  orderBy,
  onSnapshot,
  serverTimestamp,
  doc,
  setDoc,
} from "firebase/firestore";
import { db, auth } from "../firebase";
import { onAuthStateChanged } from "firebase/auth";

export function useChat() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [user, setUser] = useState(null);
  const [messageFlags, setMessageFlags] = useState({});

  // ✅ FIX: Keep a ref that always has the latest messageFlags
  // so onSnapshot closure never reads stale values
  const messageFlagsRef = useRef({});

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      if (!firebaseUser) {
        setChats([]);
        setActiveChatId(null);
        setMessages([]);
        setMessageFlags({});
        messageFlagsRef.current = {};
      }
    });
    return () => unsub();
  }, []);

  // Load all chats
  useEffect(() => {
    if (!user) return;

    const q = query(
      collection(db, "users", user.uid, "chats"),
      orderBy("createdAt", "desc")
    );

    const unsub = onSnapshot(q, (snap) => {
      setChats(snap.docs.map((d) => ({ id: d.id, ...d.data() })));
    });

    return () => unsub();
  }, [user]);

  // Load messages and merge with UI flags
  useEffect(() => {
    if (!activeChatId || !user) {
      setMessages([]);
      setMessageFlags({});
      messageFlagsRef.current = {};
      return;
    }

    const q = query(
      collection(db, "users", user.uid, "chats", activeChatId, "messages"),
      orderBy("createdAt", "asc")
    );

    const unsub = onSnapshot(q, (snap) => {
      const msgs = snap.docs.map((d) => ({ id: d.id, ...d.data() }));

      setMessages((prev) => {
        // Collect flags from previous messages as fallback
        const prevFlags = {};
        prev.forEach((m) => {
          if (m.id) {
            prevFlags[m.id] = {
              isDraft: m.isDraft,
              draft: m.draft,
              isEmailList: m.isEmailList,
              emails: m.emails,
            };
          }
        });

        return msgs.map((msg) => {
          // ✅ FIX: Read from ref (always fresh) instead of stale closure value
          const flags =
            messageFlagsRef.current[msg.id] || prevFlags[msg.id] || {};
          return { ...msg, ...flags };
        });
      });
    });

    return () => unsub();
  }, [activeChatId, user]);

  // Set UI-only flags for a message by ID
  const setMessageFlagsById = (msgId, flags) => {
    // ✅ FIX: Update both state AND ref together so the ref is always in sync
    setMessageFlags((prev) => {
      const updated = {
        ...prev,
        [msgId]: { ...(prev[msgId] || {}), ...flags },
      };
      messageFlagsRef.current = updated; // keep ref in sync
      return updated;
    });

    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, ...flags } : m))
    );
  };

  const newChat = async () => {
    if (!user) return;
    const ref = await addDoc(collection(db, "users", user.uid, "chats"), {
      title: "New Chat",
      createdAt: serverTimestamp(),
    });
    setActiveChatId(ref.id);
    setMessages([]);
    setMessageFlags({});
    messageFlagsRef.current = {};
  };

  const saveMessage = async (chatId, role, text) => {
    if (!user) return null;
    const ref = await addDoc(
      collection(db, "users", user.uid, "chats", chatId, "messages"),
      { role, text, createdAt: serverTimestamp() }
    );
    return ref.id;
  };

  const updateChatTitle = async (chatId, title) => {
    if (!user) return;
    await setDoc(
      doc(db, "users", user.uid, "chats", chatId),
      { title },
      { merge: true }
    );
  };

  return {
    chats,
    activeChatId,
    setActiveChatId,
    messages,
    setMessages,
    newChat,
    saveMessage,
    updateChatTitle,
    setMessageFlagsById,
  };
}