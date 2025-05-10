import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { TypographyH4 } from "../typography/typography";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ModeToggle } from "./ThemeToggle";
import { useLocation } from "react-router";

export function Navbar() {
  let location = useLocation();
  let pathname = location.pathname;

  const pathnameMap: { [key: string]: string } = {
    "/project": "Project Manager",
    "/label": "Video Labeling",
    "/results": "Label Results",
    "/": "Dashboard", // Keep "/" last as a fallback or handle it explicitly
  };

  let title = "Dashboard"; // Default title

  // Find the matching title based on pathname containment
  for (const key in pathnameMap) {
    // Ensure the key is not just "/" or handle it specifically if needed
    // Check if pathname starts with the key (and handle the root path case)
    if (pathname.startsWith(key) && (key !== "/" || pathname === "/")) {
      title = pathnameMap[key];
      break; // Found the most specific match (or the first one depending on order)
    }
  }

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
