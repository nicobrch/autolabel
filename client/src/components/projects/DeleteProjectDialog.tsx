import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { deleteProject } from "@/services/api";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import * as z from "zod";
import { TypographySmall } from "../typography/typography";

interface DeleteProjectDialogProps {
  projectId: number;
  projectName: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteProjectDialog({
  projectId,
  projectName,
  isOpen,
  onOpenChange,
}: DeleteProjectDialogProps) {
  const [confirmName, setConfirmName] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const queryClient = useQueryClient();

  // Create schema for validation
  const confirmSchema = z.object({
    name: z.literal(projectName),
  });

  const isValid = confirmSchema.safeParse({ name: confirmName }).success;

  const handleDelete = async () => {
    if (!isValid) return;

    setIsDeleting(true);
    try {
      await deleteProject(projectId.toString());
      toast.success("Project deleted successfully");

      // Refetch the projects list
      queryClient.invalidateQueries({ queryKey: ["projects"] });

      onOpenChange(false);
    } catch (error) {
      console.error("Error deleting project:", error);
      toast.error("Failed to delete project", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-destructive">
            Delete Project
          </AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. The project and all its associated
            videos will be permanently deleted from the server.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="py-2">
          <div className="mb-2">
            <TypographySmall>
              To confirm, type the project name:{" "}
              <span className="font-bold">{projectName}</span>
            </TypographySmall>
          </div>

          <div className="space-y-2">
            <Label htmlFor="projectName" className="sr-only">
              Project Name
            </Label>
            <Input
              id="projectName"
              value={confirmName}
              onChange={(e) => setConfirmName(e.target.value)}
              placeholder="Type project name to confirm"
              className={!isValid && confirmName ? "border-destructive" : ""}
            />
            {!isValid && confirmName && (
              <div className="text-destructive">
                <TypographySmall>
                  The name doesn't match. Please type the exact name.
                </TypographySmall>
              </div>
            )}
          </div>
        </div>

        <AlertDialogFooter className="flex justify-between sm:justify-between">
          <AlertDialogCancel
            onClick={() => setConfirmName("")}
            disabled={isDeleting}
          >
            Cancel
          </AlertDialogCancel>
          <Button
            type="button"
            variant="destructive"
            disabled={!isValid || isDeleting}
            onClick={handleDelete}
          >
            {isDeleting ? "Deleting..." : "Delete Project"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
