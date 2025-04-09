import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchProjects } from "@/services/api";
import { ProjectCard } from "@/components/projects/ProjectCard";

export function ContentArea() {
  const {
    isPending,
    error,
    data: projects,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-4">
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Create Project
        </Button>
        <Button variant="outline" className="gap-2">
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Import Project
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {isPending ? (
          <div className="col-span-full flex justify-center">
            <p className="text-gray-500">Loading projects...</p>
          </div>
        ) : error ? (
          <div className="col-span-full flex flex-col items-center">
            <p className="text-red-500">
              Error loading projects: {error.message}
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        ) : (
          // Success state - render projects
          projects?.map((project, index) => (
            <ProjectCard
              key={index}
              name={project.name}
              description={project.description}
            />
          ))
        )}
      </div>
    </div>
  );
}
