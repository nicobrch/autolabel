import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchProjects } from "@/services/api";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { CreateProjectForm } from "@/components/projects/CreateProjectForm";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { ErrorMessage } from "@/components/ui/errormsg";
import { useState } from "react";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { ContentHeader } from "@/components/layout/ContentHeader";

export default function Dashboard() {
  const {
    isPending,
    error,
    data: projects,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="p-4">
      <ContentHeader>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Create Project
            </Button>
          </DialogTrigger>
          <CreateProjectForm setIsOpen={setIsOpen} />
        </Dialog>
      </ContentHeader>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6">
        {isPending ? (
          <div className="col-span-full flex justify-center">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="col-span-full flex flex-col items-center">
            <ErrorMessage error={error.message} />
            <Button variant="outline" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        ) : (
          // Success state - render projects
          projects?.map((project) => (
            <ProjectCard
              key={project.id}
              id={project.id}
              name={project.name}
              description={project.description}
              dateCreated={project.created_at}
              videoCount={project.video_count}
            />
          ))
        )}
      </div>
    </div>
  );
}
