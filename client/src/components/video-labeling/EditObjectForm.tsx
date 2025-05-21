import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { updateVideoObject, VideoObject } from "@/services/api";
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
import { ColorPicker } from "@/components/ui/color-picker";

interface EditObjectFormProps {
  videoId: string;
  objectData: VideoObject;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export function EditObjectForm({
  videoId,
  objectData,
  setIsOpen,
}: EditObjectFormProps) {
  const [name, setName] = useState(objectData.name);
  const [color, setColor] = useState(objectData.color);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await updateVideoObject(videoId, objectData.id.toString(), {
        name,
        color,
      });
      queryClient.invalidateQueries({ queryKey: ["videoObjects", videoId] });
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
        <DialogTitle>Edit Object</DialogTitle>
        <DialogDescription>Modify the object properties</DialogDescription>
      </DialogHeader>

      {error && <ErrorMessage error={error} />}

      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="object-name">Object Name</Label>
            <Input
              id="object-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter object name"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="object-color">Object Color</Label>
            <ColorPicker
              defaultValue={color}
              onChange={setColor}
              className="w-full"
            />
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
        </div>
      </form>
    </DialogContent>
  );
}
