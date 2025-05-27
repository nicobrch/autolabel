import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { uploadVideoFile } from "@/services/api";
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
import { UploadFileDropzone } from "@/components/videos/UploadFileDropzone";
import { useParams } from "react-router";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getFileNameWithoutExtension } from "@/lib/utils";
import { z } from "zod";

// Define validation schema
const uploadVideoSchema = z.object({
  name: z.string().min(1, "Video name is required"),
  fps: z
    .number()
    .int()
    .min(1, "FPS must be at least 1")
    .max(24, "FPS cannot exceed 24"),
  resolution: z.string(),
});

export function UploadVideoForm({
  setIsOpen,
}: {
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [resolution, setResolution] = useState<string>("Original");
  const [fps, setFps] = useState<number>(2);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  let { projectId } = useParams<{ projectId: string }>();

  useEffect(() => {
    if (files.length > 0 && files[0]) {
      const fileName = files[0].name;
      const nameWithoutExtension = getFileNameWithoutExtension(fileName);
      setName(nameWithoutExtension);
    } else {
      setName("");
    }
  }, [files]); // Rerun effect when files array changes

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    if (files.length === 0) {
      setError("Please select a video file to upload.");
      setIsSubmitting(false);
      return;
    }

    try {
      // Validate form data
      const result = uploadVideoSchema.safeParse({
        name,
        fps,
        resolution,
      });

      if (!result.success) {
        // Extract the first validation error message
        const errorMsg =
          result.error.errors[0]?.message || "Validation failed";
        setError(errorMsg);
        setIsSubmitting(false);
        return;
      }

      await uploadVideoFile(parseInt(projectId!), files[0], resolution, fps);
      queryClient.invalidateQueries({ queryKey: ["videos", projectId] }); // Update query key
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
        <DialogTitle>Upload Video</DialogTitle>
        <DialogDescription>
          To start labeling videos, upload a video file.
        </DialogDescription>
      </DialogHeader>

      {error && <ErrorMessage error={error} />}

      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <UploadFileDropzone files={files} setFiles={setFiles} />
          <div className="space-y-2">
            <Label htmlFor="video-name">Video Name</Label>
            <Input
              id="video-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter name for this video"
              required
            />
          </div>
          <div className="flex space-x-4">
            <div className="space-y-2 flex-1">
              <Label htmlFor="video-resolution">Resolution</Label>
              <Select value={resolution} onValueChange={setResolution}>
                <SelectTrigger id="video-resolution" className="w-full">
                  <SelectValue placeholder="Select a resolution" />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="Original">Original</SelectItem>
                    <SelectItem value="1138x640">1138x640</SelectItem>
                    <SelectItem value="1280x720">1280x720 (HD)</SelectItem>
                    <SelectItem value="1600x900">1600x900 (HD+)</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 flex-1">
              <Label htmlFor="video-fps">Frames Per Second</Label>
              <Input
                id="video-fps"
                type="number"
                value={fps}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  if (!isNaN(value)) {
                    setFps(value);
                  }
                }}
                min={1}
                max={24}
                placeholder="e.g., 2"
                required
              />
              <p className="text-xs text-muted-foreground">
                Must be between 1 and 24
              </p>
            </div>
          </div>
          <DialogFooter className="flex justify-end space-x-2 pt-2">
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogClose>
            <Button
              type="submit"
              disabled={
                isSubmitting ||
                !name.trim() ||
                files.length === 0 ||
                fps < 1 ||
                fps > 24
              }
            >
              {isSubmitting ? "Uploading..." : "Upload Video"}
            </Button>
          </DialogFooter>
        </div>
      </form>
    </DialogContent>
  );
}
