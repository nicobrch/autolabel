import { LayoutGrid } from "lucide-react";
import { NavItem } from "../navigation/NavItem";
import { FolderItem } from "../navigation/FolderItem";
import { useQuery } from "@tanstack/react-query";
import { fetchProjects } from "@/services/api";
import { ErrorMessage } from "../ui/errormsg";

export function Sidebar() {
  const {
    isPending,
    error,
    data: projects,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  return (
    <div className="w-64 border-r bg-white">
      <div className="p-4">
        <h1 className="text-xl font-bold">AutoLabel</h1>
      </div>
      <nav className="space-y-1 px-2">
        <NavItem to="#" icon={<LayoutGrid className="h-4 w-4" />} active>
          All content
        </NavItem>
        <div className="py-3">
          <div className="px-3 text-xs font-medium uppercase text-gray-500">
            Projects
          </div>
          <div className="mt-2">
            {isPending ? (
              <div className="px-3 py-2 text-sm text-gray-500">
                Loading projects...
              </div>
            ) : error ? (
              <ErrorMessage error={error.message} />
            ) : projects && projects.length > 0 ? (
              projects.map((project, index) => (
                <FolderItem key={index} to={`/projects/${project.id}`}>
                  {project.name}
                </FolderItem>
              ))
            ) : (
              <div className="px-3 py-2 text-sm text-gray-500">
                No projects found
              </div>
            )}
          </div>
        </div>
      </nav>
    </div>
  );
}
