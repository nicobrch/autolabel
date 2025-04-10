import { cn } from "@/lib/utils";
import { NavLink } from "react-router";

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

export function NavItem({ to, icon, children }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={cn("flex items-center gap-2 px-3 py-2 text-sm rounded-lg")}
    >
      {icon}
      <span>{children}</span>
    </NavLink>
  );
}
