import { LayoutGrid, Folder } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchProjects } from "@/services/api";
import { ErrorMessage } from "../ui/errormsg";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "../ui/sidebar";
import { TypographyH3 } from "../typography/typography";
import { NavLink } from "react-router";

export function AppSidebar() {
  const {
    isPending,
    error,
    data: projects,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  const appItems = [
    {
      title: "All content",
      url: "/",
      icon: LayoutGrid,
    },
  ];

  return (
    <Sidebar>
      <SidebarHeader className="p-4 h-16 border-b flex">
        <TypographyH3>AutoLabel</TypographyH3>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Application</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {appItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>Projects</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {isPending ? (
                <div className="px-3 py-2 text-sm">Loading projects...</div>
              ) : error ? (
                <ErrorMessage error={error.message} />
              ) : projects && projects.length > 0 ? (
                projects.map((project) => (
                  <SidebarMenuItem key={project.id}>
                    <SidebarMenuButton asChild>
                      <NavLink to={`/projects/${project.id}`}>
                        <Folder />
                        <span>{project.name}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))
              ) : (
                <div className="px-3 py-2 text-sm">No projects found</div>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
