import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { fetchVideos, getThumbnailFrameUrl, getVideoUrl } from "@/services/api";
import { VideoCard } from "@/components/videos/VideoCard";
import { ErrorMessage } from "@/components/ui/errormsg";
import { useParams } from "react-router";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { UploadVideoForm } from "@/components/videos/UploadVideoForm";
import { Upload, Download } from "lucide-react";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { ContentHeader } from "@/components/layout/ContentHeader";
import { DownloadDatasetDialog } from "@/components/videos/DownloadDatasetDialog";

export default function ProjectManager() {
  const [isOpen, setIsOpen] = useState(false);
  const [isDownloadOpen, setIsDownloadOpen] = useState(false);

  const { projectId } = useParams<{ projectId: string }>();

  if (!projectId) {
    return <ErrorMessage error="Project ID is missing from the URL." />;
  }

  const {
    isPending,
    error,
    data: videos,
  } = useQuery({
    queryKey: ["videos", projectId],
    queryFn: () => fetchVideos(projectId),
    enabled: !!projectId,
  });

  return (
    <div className="p-4">
      <ContentHeader>
        <div className="flex gap-2">
          <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Upload className="h-4 w-4" />
                Upload Video
              </Button>
            </DialogTrigger>
            <UploadVideoForm setIsOpen={setIsOpen} />
          </Dialog>

          <Dialog open={isDownloadOpen} onOpenChange={setIsDownloadOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2" variant="outline">
                <Download className="h-4 w-4" />
                Download Dataset
              </Button>
            </DialogTrigger>
            <DownloadDatasetDialog
              videos={videos?.filter((v) => v.has_inference) || []}
              setIsOpen={setIsDownloadOpen}
              projectId={projectId}
            />
          </Dialog>
        </div>
      </ContentHeader>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 2xl:grid-cols-5">
        {isPending ? (
          <div className="col-span-full flex justify-center">
            <LoadingSpinner />
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
              size={video.file_size}
              resolution={`${video.width}x${video.height}`}
              dateCreated={video.created_at}
              videoPath={getVideoUrl(video.file_name)}
              firstFramePath={getThumbnailFrameUrl(video.file_name)}
              hasInference={video.has_inference}
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
