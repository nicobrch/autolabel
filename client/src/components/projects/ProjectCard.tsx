import { formatDate } from "@/lib/utils";
import { TypographySmall } from "../typography/typography";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { NavLink } from "react-router";
import {
  Calendar,
  FileVideo,
  Video,
  EllipsisVertical,
  Pencil,
  Trash2,
} from "lucide-react";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { useState } from "react";
import { DeleteProjectDialog } from "./DeleteProjectDialog";
import { EditProjectForm } from "./EditProjectForm";
import { Dialog } from "../ui/dialog";

interface ProjectCardProps {
  id: number;
  name: string;
  description: string;
  dateCreated: string; // ISO date string
  videoCount: number;
}

export function ProjectCard({
  id,
  name,
  description,
  dateCreated,
  videoCount = 0,
}: ProjectCardProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  return (
    <Card>
      <CardHeader className="flex flex-col space-y-2 overflow-hidden">
        <div className="flex justify-between items-start w-full gap-2">
          <div className="flex-grow overflow-hidden min-w-0">
            <CardTitle className="truncate">
              <NavLink
                to={`/projects/${id}`}
                className="block overflow-hidden text-ellipsis"
              >
                {name}
              </NavLink>
            </CardTitle>
            <CardDescription className="truncate">
              {description}
            </CardDescription>
          </div>
          <div className="flex-shrink-0">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="text-primary transform hover:scale-105 transition-all duration-300">
                  <EllipsisVertical className="h-5 w-5" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setIsEditDialogOpen(true)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  variant="destructive"
                  onClick={() => setIsDeleteDialogOpen(true)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      {/* Edit Project Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <EditProjectForm
          projectId={id}
          projectName={name}
          projectDescription={description}
          setIsOpen={setIsEditDialogOpen}
        />
      </Dialog>

      {/* Delete Project Dialog */}
      <DeleteProjectDialog
        projectId={id}
        projectName={name}
        isOpen={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      />

      <CardContent className="flex flex-col space-y-2">
        <div className="flex justify-between">
          <div className="flex items-center">
            <FileVideo className="mr-1.5 h-4 w-4" />
            <TypographySmall>{videoCount}</TypographySmall>
          </div>
          <div className="flex items-center">
            <Calendar className="mr-1.5 h-4 w-4" />
            <TypographySmall>{formatDate(dateCreated)}</TypographySmall>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between gap-2 px-4">
        <Button variant="default" size="sm" className="flex-1" asChild>
          <NavLink to={`/projects/${id}`}>
            <Video className="mr-1.5 h-4 w-4" />
            Project Videos
          </NavLink>
        </Button>
      </CardFooter>
    </Card>
  );
}
