import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { updateProject } from "@/services/api";
import { useQueryClient } from "@tanstack/react-query";
import {
  DialogTitle,
  DialogContent,
  DialogClose,
  DialogFooter,
  DialogHeader,
  DialogDescription,
} from "@/components/ui/dialog";
import { ErrorMessage } from "@/components/ui/errormsg";

interface EditProjectFormProps {
  projectId: number;
  projectName: string;
  projectDescription: string;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export function EditProjectForm({
  projectId,
  projectName,
  projectDescription,
  setIsOpen,
}: EditProjectFormProps) {
  const [name, setName] = useState(projectName);
  const [description, setDescription] = useState(projectDescription || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await updateProject(projectId, {
        name,
        description,
      });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setIsOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <DialogContent className="max-w-md w-full">
      <DialogHeader>
        <DialogTitle>Edit Project</DialogTitle>
        <DialogDescription>Modify the project details</DialogDescription>
      </DialogHeader>

      {error && <ErrorMessage error={error} />}

      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="project-name">Project Name</Label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter project name"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-description">Description</Label>
            <Textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter project description (optional)"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter className="flex justify-end space-x-2 pt-2">
          <DialogClose asChild>
            <Button type="button" variant="outline" disabled={isSubmitting}>
              Cancel
            </Button>
          </DialogClose>
          <Button type="submit" disabled={isSubmitting || !name.trim()}>
            {isSubmitting ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
