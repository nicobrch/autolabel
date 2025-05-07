import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { fetchVideos } from "@/services/api";
import { VideoCard } from "@/components/videos/VideoCard";
import { ErrorMessage } from "@/components/ui/errormsg";
import { useParams, NavLink } from "react-router";
import { ArrowLeft } from "lucide-react";

export default function ProjectManager() {
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
            {" "}
            {/* NavLink back to the project list */}
            <ArrowLeft className="h-4 w-4" />
            Back to Projects
          </NavLink>
        </Button>
        {/* Add other controls if needed, e.g., Upload Video */}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {isPending ? (
          <div className="col-span-full flex justify-center">
            <p>Loading videos...</p>
          </div>
        ) : error ? (
          <div className="col-span-full flex flex-col items-center">
            <ErrorMessage error={error.message} />
            <Button variant="outline" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        ) : videos && videos.length > 0 ? (
          // Success state - render videos
          videos.map((video) => (
            <VideoCard
              key={video.id}
              id={video.id}
              name={video.name}
              description={video.description}
              imageUrl={video.thumbnailUrl || "/placeholder-image.png"} // Use a placeholder if no thumbnail
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
