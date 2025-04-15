import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { TypographyH4 } from "../typography/typography";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ModeToggle } from "./ThemeToggle";
import { useLocation } from "react-router";

export function Navbar() {
  let location = useLocation();
  let pathname = location.pathname;

  const pathnameMap: { [key: string]: string } = {
    "/": "Project Manager",
    "/label": "Video Labeling",
  };

  const title = pathnameMap[pathname] || "Dashboard";

  return (
    <nav className="flex items-center justify-between p-4 h-16 border-b">
      <div className="flex items-center space-x-4">
        <SidebarTrigger />
        <TypographyH4>{title}</TypographyH4>
      </div>
      <div className="flex items-center space-x-4">
        <ModeToggle />
        <Avatar>
          <AvatarImage src="https://github.com/nicobrch.png" alt="@nicobrch" />
          <AvatarFallback>NC</AvatarFallback>
        </Avatar>
      </div>
    </nav>
  );
}
