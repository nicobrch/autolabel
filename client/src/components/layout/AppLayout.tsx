import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Outlet } from "react-router";
import { Navbar } from "./Navbar";

export default function AppLayout() {
  return (
    <SidebarProvider className="font-display h-screen">
      <AppSidebar />
      <div className="flex-1 overflow-hidden h-full">
        <Navbar />
        <div className="h-full overflow-y-auto">
          <Outlet />
        </div>
      </div>
    </SidebarProvider>
  );
}
