import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ContentArea } from "@/components/layout/ContentArea";

export default function ProjectManager() {
  return (
    <div className="flex h-screen bg-white">
      <Sidebar />
      <div className="flex-1">
        <Header />
        <ContentArea />
      </div>
    </div>
  );
}
