import { Outlet } from "react-router-dom";
import { ConversationSidebar } from "./ConversationSidebar";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden">
      <ConversationSidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
