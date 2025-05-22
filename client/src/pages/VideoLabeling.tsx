import { useState, MouseEvent, useEffect } from "react";
import { VideoDisplay } from "@/components/video-labeling/VideoDisplay";
import { InferenceSettings } from "@/components/video-labeling/InferenceSettings";
import { LabelingOptions } from "@/components/video-labeling/LabelingOptions";
import { ContentHeader } from "@/components/layout/ContentHeader";
import { useParams } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchVideoFrameCount,
  fetchVideoById,
  getInferenceThumbnailUrl,
  fetchVideoObjects,
  labelVideoFrame,
} from "@/services/api";
import { ErrorMessage } from "@/components/ui/errormsg";
import LoadingSpinner from "@/components/ui/loading-spinner";
import { toast } from "sonner";

export default function VideoLabeling() {
  const { videoId } = useParams<{ videoId: string }>();
  const queryClient = useQueryClient();

  const [modelCheckpoint, setModelCheckpoint] = useState("small");
  const [selectedObject, setSelectedObject] = useState<string>("");
  const [pointType, setPointType] = useState("positive");
  const [isProcessing, setIsProcessing] = useState(false);
  const currentFrame = 1;

  // Use React Query to fetch video data
  const {
    isPending: isVideoPending,
    error: videoError,
    data: videoData,
  } = useQuery({
    queryKey: ["video", videoId],
    queryFn: () => {
      if (!videoId) throw new Error("Video ID is missing");
      return fetchVideoById(videoId);
    },
    enabled: !!videoId,
  });

  // Use React Query to fetch frame count
  const {
    isPending: isFrameCountPending,
    error: frameCountError,
    data: frameData,
  } = useQuery({
    queryKey: ["frameCount", videoId],
    queryFn: () => {
      if (!videoId) throw new Error("Video ID is missing");
      return fetchVideoFrameCount(videoId);
    },
    enabled: !!videoId,
  });

  // Use React Query to fetch video objects
  const {
    isPending: isObjectsPending,
    error: objectsError,
    data: objectsData,
  } = useQuery({
    queryKey: ["videoObjects", videoId],
    queryFn: () => {
      if (!videoId) throw new Error("Video ID is missing");
      return fetchVideoObjects(videoId);
    },
    enabled: !!videoId,
  });

  // NEW QUERY: Use React Query to fetch the inference frame
  const {
    isPending: isFrameLoading,
    error: frameError,
    data: inferenceFrameUrl,
    refetch: refetchFrame,
  } = useQuery({
    queryKey: ["inferenceFrame", videoId],
    queryFn: () => {
      if (!videoId || !videoData) return null;
      // Return the URL directly rather than fetching it - we just need the URL for the image
      return getInferenceThumbnailUrl(videoData.file_name);
    },
    enabled: !!videoId && !!videoData,
    staleTime: 0, // Consider data as stale immediately so it will refetch after revalidation
  });

  // Get the total frames from the query result
  const totalFrames = frameData?.frame_count || 0;

  // Use the inference frame URL from the query, or fallback to a placeholder
  const displayImageUrl =
    inferenceFrameUrl ||
    (videoData
      ? getInferenceThumbnailUrl(videoData.file_name)
      : "/placeholder.svg?height=720&width=1280");

  // Create a unique key that changes when the frame should be refreshed
  const displayKey = `frame-${videoId}-${isProcessing ? "processing" : inferenceFrameUrl}`;

  const isPending =
    isVideoPending || isFrameCountPending || isObjectsPending || isFrameLoading;
  const error = videoError || frameCountError || objectsError || frameError;

  // Helper function to show missing object error
  const showMissingObjectError = () => {
    toast.error("No object selected", {
      description: "Please create and select an object before labeling",
    });
  };

  // Reset query caches when videoId changes
  useEffect(() => {
    if (videoId) {
      queryClient.invalidateQueries({ queryKey: ["inferenceFrame", videoId] });
    }
  }, [videoId, queryClient]);

  const handleImageClick = async (event: MouseEvent<HTMLImageElement>) => {
    // If no objects exist or no object is selected, show error and return
    if (!objectsData?.length) {
      toast.error("No objects available", {
        description: "Please create an object before trying to add points",
      });
      return;
    }

    if (!selectedObject) {
      showMissingObjectError();
      return;
    }

    if (!videoId) {
      toast.error("Video ID is missing");
      return;
    }

    const imgElement = event.currentTarget;
    const rect = imgElement.getBoundingClientRect();

    // Define the original/natural dimensions
    const naturalWidth = videoData?.width || 1280;
    const naturalHeight = videoData?.height || 720;

    // Get the displayed dimensions
    const displayWidth = rect.width;
    const displayHeight = rect.height;

    // Calculate scaling factors
    const scaleX = naturalWidth / displayWidth;
    const scaleY = naturalHeight / displayHeight;

    // Calculate click coordinates relative to the image element
    const clickX = event.nativeEvent.offsetX;
    const clickY = event.nativeEvent.offsetY;

    // Scale coordinates to match the original image dimensions
    const x = Math.round(clickX * scaleX);
    const y = Math.round(clickY * scaleY);

    console.log(`Clicked at (relative): x=${clickX}, y=${clickY}`);
    console.log(`Scaled to ${naturalWidth}x${naturalHeight}: x=${x}, y=${y}`);

    // Determine label based on pointType state
    const label = pointType === "positive" ? 1 : 0;
    const objectId = parseInt(selectedObject, 10);

    // Set processing state to show loading spinner
    setIsProcessing(true);

    try {
      // Use the API function instead of direct fetch
      const result = await labelVideoFrame({
        videoId,
        objectId,
        x,
        y,
        label,
        checkpoint: modelCheckpoint,
      });

      console.log("Frame labeled successfully:", result);

      // Display success message
      toast.success("Frame labeled successfully", {
        description: `Object ${selectedObject} has been segmented`,
      });

      // Invalidate and refetch relevant queries to update the UI
      queryClient.invalidateQueries({ queryKey: ["inferenceFrame", videoId] });
      queryClient.invalidateQueries({ queryKey: ["videoObjects", videoId] });

      // Force a refetch of the frame
      await refetchFrame();
    } catch (error) {
      console.error("Failed to process frame:", error);
      toast.error("Failed to label frame", {
        description: (error as Error).message || "An unexpected error occurred",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLabelVideo = () => {
    // If no objects exist or no object is selected, show error and return
    if (!objectsData?.length) {
      toast.error("No objects available", {
        description: "Please create an object before trying to label the video",
      });
      return;
    }

    if (!selectedObject) {
      showMissingObjectError();
      return;
    }

    console.log("Label video clicked");
    // Add logic to start video labeling/propagation
  };

  return (
    <div className="flex flex-col w-full p-4">
      <ContentHeader />
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1">
          {isPending && !isProcessing ? (
            <div className="flex items-center justify-center h-[720px] bg-muted">
              <LoadingSpinner />
              <span className="ml-2">Loading video frames...</span>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-[720px] bg-muted">
              <ErrorMessage error={(error as Error).message} />
            </div>
          ) : isProcessing ? (
            <div className="flex items-center justify-center h-[720px] bg-muted relative">
              <img
                src={displayImageUrl}
                alt="Video frame"
                className="max-w-full max-h-full opacity-50"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <LoadingSpinner />
                <span className="ml-2 font-semibold text-lg">
                  Processing frame...
                </span>
              </div>
            </div>
          ) : (
            <VideoDisplay
              key={displayKey} // Add key prop to force re-render
              imageUrl={displayImageUrl}
              onImageClick={handleImageClick}
              currentFrame={currentFrame}
              totalFrames={totalFrames}
              hasSelectedObject={!!selectedObject}
            />
          )}
        </div>

        <div className="w-full lg:w-80 space-y-6">
          <InferenceSettings
            modelCheckpoint={modelCheckpoint}
            onModelCheckpointChange={setModelCheckpoint}
            onLabelVideo={handleLabelVideo}
            videoId={videoId || ""}
          />

          <LabelingOptions
            selectedObject={selectedObject}
            onSelectedObjectChange={setSelectedObject}
            pointType={pointType}
            onPointTypeChange={setPointType}
            videoObjects={objectsData || []}
            isLoading={isObjectsPending}
            videoId={videoId || ""}
          />
        </div>
      </div>
    </div>
  );
}
