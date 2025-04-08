import { cn } from "@/lib/utils";
import { NavLink } from "react-router";

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  active?: boolean;
}

export function NavItem({ to, icon, children, active }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={cn(
        "flex items-center gap-2 px-3 py-2 text-sm text-gray-700 rounded-lg",
        active && "bg-gray-100"
      )}
    >
      {icon}
      <span>{children}</span>
    </NavLink>
  );
}
