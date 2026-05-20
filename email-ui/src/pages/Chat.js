import SidebarLeft from "../components/SidebarLeft";
import SidebarRight from "../components/SidebarRight";
import ChatWindow from "../components/ChatWindow";

export default function Chat() {
  return (
    <div className="flex h-screen w-screen bg-gray-100">

      {/* LEFT SIDEBAR */}
      <SidebarLeft />

      {/* CENTER CHAT */}
      <div className="flex-1 flex flex-col">
        <ChatWindow />
      </div>

      {/* RIGHT SIDEBAR */}
      <SidebarRight />

    </div>
  );
}