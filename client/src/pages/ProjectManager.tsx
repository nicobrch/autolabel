import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { fetchVideos } from "@/services/api";
import { VideoCard } from "@/components/videos/VideoCard";
import { ErrorMessage } from "@/components/ui/errormsg";
import { useParams, NavLink } from "react-router";
import { ArrowLeft } from "lucide-react";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { UploadVideoForm } from "@/components/videos/UploadVideoForm";
import { Upload } from "lucide-react";

export default function ProjectManager() {
  const [isOpen, setIsOpen] = useState(false);

  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return <ErrorMessage error="Project ID is missing from the URL." />;
  }

  const {
    isPending,
    error,
    data: videos,
  } = useQuery({
    // Include projectId in the query key to refetch when it changes
    queryKey: ["videos", projectId],
    queryFn: () => fetchVideos(projectId),
    enabled: !!projectId, // Only run the query if projectId is available
  });

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-4">
        <Button variant="outline" className="gap-2" asChild>
          <NavLink to="/">
            <ArrowLeft className="h-4 w-4" />
            Back to Projects
          </NavLink>
        </Button>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Upload className="h-4 w-4" />
              Upload Video
            </Button>
          </DialogTrigger>
          <UploadVideoForm setIsOpen={setIsOpen} />
        </Dialog>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {isPending ? (
          <div className="col-span-full flex justify-center">
            <p>Loading videos...</p>
          </div>
        ) : error ? (
          <div className="col-span-full flex flex-col items-center">
            <ErrorMessage error={error.message} />
          </div>
        ) : videos && videos.length > 0 ? (
          videos.map((video) => (
            <VideoCard
              key={video.id}
              id={video.id}
              name={video.file_name}
              duration={video.duration}
              dateCreated={video.created_at}
              imageUrl={video.file_path || "/placeholder.svg"}
            />
          ))
        ) : (
          <div className="col-span-full flex justify-center">
            <p>No videos found for this project.</p>
          </div>
        )}
      </div>
    </div>
  );
}
