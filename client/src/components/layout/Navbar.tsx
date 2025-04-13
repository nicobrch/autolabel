import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { TypographyH4 } from "../typography/typography";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ModeToggle } from "./ThemeToggle";

export function Navbar() {
    return (
        <nav className="flex items-center justify-between p-4 h-16 border-b">
            <div className="flex items-center space-x-4">
                <SidebarTrigger />
                <TypographyH4>
                    Projects
                </TypographyH4>
            </div>
            <div className="flex items-center space-x-4">
                <ModeToggle />
                <Avatar>
                    <AvatarImage src="https://github.com/nicobrch.png" alt="@nicobrch" />
                    <AvatarFallback>NC</AvatarFallback>
                </Avatar>
            </div>
        </nav>
    )
}