import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getFileNameWithoutExtension } from "@/lib/utils";
import { deleteVideo } from "@/services/api";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import * as z from "zod";
import { TypographySmall } from "../typography/typography";

interface DeleteVideoDialogProps {
  videoId: string | number;
  videoName: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  projectId?: string;
}

export function DeleteVideoDialog({
  videoId,
  videoName,
  isOpen,
  onOpenChange,
  projectId,
}: DeleteVideoDialogProps) {
  const [confirmName, setConfirmName] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const queryClient = useQueryClient();

  const displayName = getFileNameWithoutExtension(videoName);

  // Create schema for validation
  const confirmSchema = z.object({
    name: z.literal(displayName),
  });

  const isValid = confirmSchema.safeParse({ name: confirmName }).success;

  const handleDelete = async () => {
    if (!isValid) return;

    setIsDeleting(true);
    try {
      await deleteVideo(videoId.toString());
      toast.success("Video deleted successfully");

      // If we have a projectId, refetch the video list
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: ["videos", projectId] });
      }

      onOpenChange(false);
    } catch (error) {
      console.error("Error deleting video:", error);
      toast.error("Failed to delete video", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-destructive">Delete Video</DialogTitle>
          <DialogDescription>
            This action cannot be undone. The video and all its associated data
            will be permanently deleted from the server.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          <div className="mb-2">
            <TypographySmall>
              To confirm, type the video name:{" "}
              <span className="font-bold">{displayName}</span>
            </TypographySmall>
          </div>

          <div className="space-y-2">
            <Label htmlFor="videoName" className="sr-only">
              Video Name
            </Label>
            <Input
              id="videoName"
              value={confirmName}
              onChange={(e) => setConfirmName(e.target.value)}
              placeholder="Type video name to confirm"
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

        <DialogFooter className="flex justify-between sm:justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={!isValid || isDeleting}
            onClick={handleDelete}
          >
            {isDeleting ? "Deleting..." : "Delete Video"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
