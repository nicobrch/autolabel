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

export function UploadVideoForm({
  setIsOpen,
}: {
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [resolution, setResolution] = useState<string>("Original");
  const [fps, setFps] = useState<number>(5);
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
                    <SelectItem value="854x480">854x480 (FWVGA)</SelectItem>
                    <SelectItem value="960x540">960x540 (qHD)</SelectItem>
                    <SelectItem value="1280x720">1280x720 (HD)</SelectItem>
                    <SelectItem value="1920x1080">
                      1920x1080 (Full HD)
                    </SelectItem>
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
                onChange={(e) => setFps(parseInt(e.target.value))}
                placeholder="e.g., 5"
                required
              />
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
              disabled={isSubmitting || !name.trim() || files.length === 0}
            >
              {isSubmitting ? "Uploading..." : "Upload Video"}
            </Button>
          </DialogFooter>
        </div>
      </form>
    </DialogContent>
  );
}
