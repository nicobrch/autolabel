import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Outlet } from "react-router";
import { Navbar } from "./Navbar";

export default function AppLayout() {
  return (
    <SidebarProvider className="font-display h-screen">
      <AppSidebar />
      <div className="flex-1 overflow-hidden h-full flex flex-col">
        <Navbar />
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </div>
    </SidebarProvider>
  );
}
