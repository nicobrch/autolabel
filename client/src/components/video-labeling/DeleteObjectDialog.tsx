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
import { deleteObject } from "@/services/api";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import * as z from "zod";
import { TypographySmall } from "../typography/typography";

interface DeleteObjectDialogProps {
  videoId: string;
  objectId: string;
  objectName: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onDeleted?: () => void;
}

export function DeleteObjectDialog({
  videoId,
  objectId,
  objectName,
  isOpen,
  onOpenChange,
  onDeleted,
}: DeleteObjectDialogProps) {
  const [confirmName, setConfirmName] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const queryClient = useQueryClient();

  // Create schema for validation
  const confirmSchema = z.object({
    name: z.literal(objectName),
  });

  const isValid = confirmSchema.safeParse({ name: confirmName }).success;

  const handleDelete = async () => {
    if (!isValid) return;

    setIsDeleting(true);
    try {
      await deleteObject(videoId, objectId);
      toast.success("Object deleted successfully");

      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["videoObjects", videoId] });
      queryClient.invalidateQueries({ queryKey: ["inferenceFrame", videoId] });

      if (onDeleted) {
        onDeleted();
      }
      
      onOpenChange(false);
    } catch (error) {
      console.error("Error deleting object:", error);
      toast.error("Failed to delete object", {
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
          <AlertDialogTitle className="text-destructive">Delete Object</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. The object "{objectName}" and all its associated
            segmentation data will be permanently deleted.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="py-2">
          <div className="mb-2">
            <TypographySmall>
              To confirm, type the object name:{" "}
              <span className="font-bold">{objectName}</span>
            </TypographySmall>
          </div>

          <div className="space-y-2">
            <Label htmlFor="objectName" className="sr-only">
              Object Name
            </Label>
            <Input
              id="objectName"
              value={confirmName}
              onChange={(e) => setConfirmName(e.target.value)}
              placeholder="Type object name to confirm"
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
            {isDeleting ? "Deleting..." : "Delete Object"}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
