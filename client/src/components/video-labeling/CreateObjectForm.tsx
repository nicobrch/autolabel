import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createVideoObject } from "@/services/api";
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
import { ColorPicker, colorPresets } from "@/components/ui/color-picker";
import { Checkbox } from "@/components/ui/checkbox";

// Helper function to get a random color from the presets
const getRandomColor = () => {
  const randomIndex = Math.floor(Math.random() * colorPresets.length);
  return colorPresets[randomIndex];
};

interface CreateObjectFormProps {
  videoId: string;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export function CreateObjectForm({
  videoId,
  setIsOpen,
}: CreateObjectFormProps) {
  const [name, setName] = useState("");
  const [color, setColor] = useState(getRandomColor()); // Random color from presets
  const [isProjectWide, setIsProjectWide] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await createVideoObject(videoId, {
        name,
        color,
        project_wide: isProjectWide,
      });
      queryClient.invalidateQueries({ queryKey: ["videoObjects", videoId] });
      setIsOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setName("");
      setColor(getRandomColor()); // Reset to a new random color
      setIsSubmitting(false);
    }
  };

  return (
    <DialogContent className="max-w-md w-full">
      <DialogHeader>
        <DialogTitle>Create Object</DialogTitle>
        <DialogDescription>
          Create a new object to label in the video
        </DialogDescription>
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
              placeholder="Enter object name (e.g., Person, Car)"
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

          <div className="flex items-center space-x-2">
            <Checkbox
              id="project-wide"
              checked={isProjectWide}
              onCheckedChange={(checked) => setIsProjectWide(Boolean(checked))}
            />
            <label
              htmlFor="project-wide"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Create for all videos in this project
            </label>
          </div>

          <DialogFooter className="flex justify-end space-x-2 pt-2">
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isSubmitting || !name.trim()}>
              {isSubmitting ? "Creating..." : "Create Object"}
            </Button>
          </DialogFooter>
        </div>
      </form>
    </DialogContent>
  );
}
