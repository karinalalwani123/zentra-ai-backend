import { useEffect, useRef, useState } from "react";
import { db, auth } from "../firebase";
import {
  collection,
  getDocs,
  doc,
  updateDoc,
  deleteDoc,
  query,
  orderBy,
} from "firebase/firestore";
import { signOut } from "firebase/auth";

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stats, setStats] = useState({ users: 0, chats: 0, messages: 0 });
  const [loading, setLoading] = useState(true);
  const activeChatId = useRef(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const userSnap = await getDocs(collection(db, "users"));
      const userList = userSnap.docs.map((d) => ({ id: d.id, ...d.data() }));
      setUsers(userList);

      let totalChats = 0;
      let totalMessages = 0;

      for (const user of userList) {
        try {
          const chatSnap = await getDocs(collection(db, "users", user.id, "chats"));
          totalChats += chatSnap.size;
          for (const chat of chatSnap.docs) {
            try {
              const msgSnap = await getDocs(
                collection(db, "users", user.id, "chats", chat.id, "messages")
              );
              totalMessages += msgSnap.size;
            } catch (e) {}
          }
        } catch (e) {}
      }

      setStats({ users: userList.length, chats: totalChats, messages: totalMessages });
    } catch (e) {
      console.error("Fetch error:", e);
    }
    setLoading(false);
  };

  const fetchUserChats = async (user) => {
    setSelectedUser(user);
    setSelectedChat(null);
    setMessages([]);
    activeChatId.current = null;
    setActiveTab("chats");
    try {
      const q = query(
        collection(db, "users", user.id, "chats"),
        orderBy("createdAt", "desc")
      );
      const snap = await getDocs(q);
      setChats(snap.docs.map((d) => ({ id: d.id, ...d.data() })));
    } catch (e) {
      console.error("Chat fetch error:", e);
    }
  };

  const fetchMessages = async (chat, currentUser) => {
    activeChatId.current = chat.id;
    setSelectedChat(chat);
    setMessages([]);
    try {
      const q = query(
        collection(db, "users", currentUser.id, "chats", chat.id, "messages"),
        orderBy("createdAt", "asc")
      );
      const snap = await getDocs(q);
      if (activeChatId.current !== chat.id) return;
      setMessages(snap.docs.map((d) => ({ id: d.id, ...d.data() })));
    } catch (e) {
      console.error("Message fetch error:", e);
    }
  };

  const changeRole = async (id, role) => {
    await updateDoc(doc(db, "users", id), { role });
    fetchAll();
  };

  const deleteUser = async (user) => {
    if (!window.confirm(`Delete ${user.email} and all their data?`)) return;
    try {
      const chatSnap = await getDocs(collection(db, "users", user.id, "chats"));
      for (const chat of chatSnap.docs) {
        const msgSnap = await getDocs(
          collection(db, "users", user.id, "chats", chat.id, "messages")
        );
        for (const msg of msgSnap.docs) {
          await deleteDoc(doc(db, "users", user.id, "chats", chat.id, "messages", msg.id));
        }
        await deleteDoc(doc(db, "users", user.id, "chats", chat.id));
      }
      await deleteDoc(doc(db, "users", user.id));
      if (selectedUser?.id === user.id) {
        setSelectedUser(null);
        setChats([]);
        setMessages([]);
        activeChatId.current = null;
      }
      fetchAll();
    } catch (e) {
      console.error("Delete error:", e);
    }
  };

  const deleteChat = async (chat) => {
    if (!window.confirm("Delete this chat?")) return;
    const user = selectedUser;
    try {
      const msgSnap = await getDocs(
        collection(db, "users", user.id, "chats", chat.id, "messages")
      );
      for (const msg of msgSnap.docs) {
        await deleteDoc(doc(db, "users", user.id, "chats", chat.id, "messages", msg.id));
      }
      await deleteDoc(doc(db, "users", user.id, "chats", chat.id));
      if (selectedChat?.id === chat.id) {
        setSelectedChat(null);
        setMessages([]);
        activeChatId.current = null;
      }
      fetchUserChats(user);
    } catch (e) {
      console.error("Delete chat error:", e);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  if (loading) {
    return <div className="loading-screen">Loading admin data...</div>;
  }

  // Reusable user table rows
  const UserTableRows = () =>
    users.map((u) => (
      <div key={u.id} className="admin-table-row">
        <span className="admin-email">{u.email}</span>
        <span className={`admin-badge ${u.role}`}>{u.role}</span>
        <div className="admin-actions">
          <button className="admin-btn-view" onClick={() => fetchUserChats(u)}>
            View Chats
          </button>
          <button
            className="admin-btn-promote"
            onClick={() => changeRole(u.id, u.role === "admin" ? "user" : "admin")}
          >
            {u.role === "admin" ? "Make User" : "Make Admin"}
          </button>
          <button className="admin-btn-delete" onClick={() => deleteUser(u)}>
            Delete
          </button>
        </div>
      </div>
    ));

  return (
    <div className="admin-shell">

      {/* TOP BAR */}
      <div className="admin-topbar">
        <h1>Admin Dashboard</h1>
        <button onClick={() => signOut(auth)} className="admin-signout">
          Logout
        </button>
      </div>

      {/* TABS */}
      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          Dashboard
        </button>
        <button
          className={`admin-tab ${activeTab === "users" ? "active" : ""}`}
          onClick={() => setActiveTab("users")}
        >
          Users ({users.length})
        </button>
        {selectedUser && (
          <button
            className={`admin-tab ${activeTab === "chats" ? "active" : ""}`}
            onClick={() => setActiveTab("chats")}
          >
            {selectedUser.email}'s Chats ({chats.length})
          </button>
        )}
      </div>

      <div className="admin-content">

        {/* DASHBOARD TAB */}
        {activeTab === "dashboard" && (
          <div>
            <div className="admin-stats">
              <div className="stat-card">
                <p className="stat-label">Total Users</p>
                <p className="stat-value">{stats.users}</p>
              </div>
              <div className="stat-card">
                <p className="stat-label">Total Chats</p>
                <p className="stat-value">{stats.chats}</p>
              </div>
              <div className="stat-card">
                <p className="stat-label">Total Messages</p>
                <p className="stat-value">{stats.messages}</p>
              </div>
            </div>

            <h3 className="admin-section-title">All Users</h3>
            <div className="admin-table">
              <div className="admin-table-header">
                <span>Email</span>
                <span>Role</span>
                <span>Actions</span>
              </div>
              <UserTableRows />
            </div>
          </div>
        )}

        {/* USERS TAB */}
        {activeTab === "users" && (
          <div className="admin-table">
            <div className="admin-table-header">
              <span>Email</span>
              <span>Role</span>
              <span>Actions</span>
            </div>
            <UserTableRows />
          </div>
        )}

        {/* CHATS TAB */}
        {activeTab === "chats" && selectedUser && (
          <div className="admin-chats-layout">
            <div className="admin-chat-list">
              <h3 className="admin-section-title">Chats ({chats.length})</h3>
              {chats.length === 0 ? (
                <p className="admin-empty">No chats found</p>
              ) : (
                chats.map((c) => (
                  <div
                    key={c.id}
                    className={`admin-chat-item ${selectedChat?.id === c.id ? "active" : ""}`}
                    onClick={() => fetchMessages(c, selectedUser)}
                  >
                    <span className="admin-chat-title">{c.title || "New Chat"}</span>
                    <button
                      className="admin-btn-delete-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(c);
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="admin-messages">
              {!selectedChat ? (
                <div className="admin-empty-messages">Select a chat to view messages</div>
              ) : (
                <>
                  <h3 className="admin-section-title">{selectedChat.title || "New Chat"}</h3>
                  <div className="admin-message-list">
                    {messages.length === 0 ? (
                      <p className="admin-empty">No messages</p>
                    ) : (
                      messages.map((m) => (
                        <div key={m.id} className={`admin-message ${m.role}`}>
                          <span className="admin-message-role">{m.role}</span>
                          <p className="admin-message-text">{m.text}</p>
                        </div>
                      ))
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}