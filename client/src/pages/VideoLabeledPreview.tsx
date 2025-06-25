import { AspectRatio } from "@/components/ui/aspect-ratio";
import {
  TypographyH4,
  TypographySmall,
} from "@/components/typography/typography";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Nut,
  Box,
  Brain,
  Gauge,
  TableOfContents,
  Clock2,
  SquareDashedMousePointer,
} from "lucide-react";
import { useParams, useNavigate } from "react-router";
import { ContentHeader } from "@/components/layout/ContentHeader";
import {
  fetchVideoById,
  getVideoInferenceUrl,
  getInferenceThumbnailUrl,
  downloadYoloDataset,
  downloadCocoDataset,
  downloadYoloSegDataset,
  fetchInferenceResults,
} from "@/services/api";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { formatDateTime } from "@/lib/utils";
import { useEffect } from "react";

export default function VideoLabeledPreview() {
  let { videoId } = useParams();
  const navigate = useNavigate();

  const {
    data: video,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["video", videoId],
    queryFn: () => fetchVideoById(videoId!),
    enabled: !!videoId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Check if the inference video exists as soon as the base video data is loaded
  useEffect(() => {
    if (!isLoading && video) {
      // Get the inference video URL
      const inferenceVideoUrl = getVideoInferenceUrl(video.file_name);

      // Use fetch to check if the inference video exists
      fetch(inferenceVideoUrl, { method: "HEAD" })
        .then((response) => {
          if (!response.ok) {
            // If response is not OK (e.g., 404), redirect to not found
            navigate("/not-found");
          }
        })
        .catch(() => {
          // If fetch fails (network error, etc.), redirect to not found
          navigate("/not-found");
        });

      // Set a short timeout as a fallback for the API query
      const timeout = setTimeout(() => {
        if (!inferenceResults && !isLoadingInference) {
          navigate("/not-found");
        }
      }, 1000);

      return () => clearTimeout(timeout);
    }
  }, [isLoading, video, navigate]);

  const {
    data: inferenceResults,
    isLoading: isLoadingInference,
    error: inferenceError,
  } = useQuery({
    queryKey: ["inferenceResults", videoId],
    queryFn: () => fetchInferenceResults(videoId!),
    enabled: !!videoId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Redirect to 404 page if inference results are not found
  useEffect(() => {
    if (!isLoadingInference && (inferenceError || !inferenceResults)) {
      navigate("/not-found");
    }
  }, [isLoadingInference, inferenceError, inferenceResults, navigate]);

  // Create a mutation for downloading YOLO dataset
  const downloadYoloMutation = useMutation({
    mutationFn: async () => {
      if (!videoId) throw new Error("Video ID is required");
      return await downloadYoloDataset(videoId);
    },
    onError: (error) => {
      toast.error("Download error", {
        description: `YOLO download failed ${error} Please try again.`,
      });
    },
  });

  // Create a mutation for downloading COCO dataset
  const downloadCocoMutation = useMutation({
    mutationFn: async () => {
      if (!videoId) throw new Error("Video ID is required");
      return await downloadCocoDataset(videoId);
    },
    onError: (error) => {
      toast.error("Download error", {
        description: `COCO download failed ${error} Please try again.`,
      });
    },
  });

  // Create a mutation for downloading YOLO segmentation dataset
  const downloadYoloSegMutation = useMutation({
    mutationFn: async () => {
      if (!videoId) throw new Error("Video ID is required");
      return await downloadYoloSegDataset(videoId);
    },
    onError: (error) => {
      toast.error("Download error", {
        description: `YOLO segmentation download failed ${error} Please try again.`,
      });
    },
  });

  const handleDownloadYolo = () => {
    if (!videoId) {
      toast.error("Video ID missing", {
        description: "Video ID is missing. Please try again.",
      });
      return;
    }
    downloadYoloMutation.mutate();
  };

  const handleDownloadCoco = () => {
    if (!videoId) {
      toast.error("Video ID missing", {
        description: "Video ID is missing. Please try again.",
      });
      return;
    }
    downloadCocoMutation.mutate();
  };

  const handleDownloadYoloSeg = () => {
    if (!videoId) {
      toast.error("Video ID missing", {
        description: "Video ID is missing. Please try again.",
      });
      return;
    }
    downloadYoloSegMutation.mutate();
  };

  return (
    <div className="flex flex-col w-full p-4">
      <ContentHeader />
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1">
          <AspectRatio ratio={16 / 9}>
            {isLoading ? (
              <div className="w-full h-full rounded-md bg-muted flex items-center justify-center">
                Loading video...
              </div>
            ) : error ? (
              <div className="w-full h-full rounded-md bg-destructive/10 flex items-center justify-center text-destructive">
                {error instanceof Error ? error.message : "An error occurred"}
              </div>
            ) : (
              <video
                src={
                  video
                    ? getVideoInferenceUrl(video.file_name)
                    : "/placeholder.svg?height=720&width=1280"
                }
                poster={
                  video
                    ? getInferenceThumbnailUrl(video.file_name)
                    : "/placeholder.svg"
                }
                width={1280}
                height={720}
                className="w-full h-full rounded-md object-cover shadow-sm border-1"
                controls
              />
            )}
          </AspectRatio>
        </div>

        <div className="w-full lg:w-80 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>
                <TypographyH4>Inference Metadata</TypographyH4>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoadingInference ? (
                <div className="text-center py-2">Loading metadata...</div>
              ) : inferenceError ? (
                <div className="text-center py-2 text-destructive">
                  {inferenceError instanceof Error
                    ? inferenceError.message
                    : "Failed to load inference metadata"}
                </div>
              ) : inferenceResults ? (
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <div className="flex items-center">
                      <Brain className="h-4 w-4 mr-2" />
                      <TypographySmall>Model:</TypographySmall>
                    </div>
                    <TypographySmall>
                      SAM2 {inferenceResults.model_checkpoint}
                    </TypographySmall>
                  </div>
                  <div className="flex justify-between">
                    <div className="flex items-center">
                      <Gauge className="h-4 w-4 mr-2" />
                      <TypographySmall>FPS:</TypographySmall>
                    </div>
                    <TypographySmall>{inferenceResults.fps}</TypographySmall>
                  </div>
                  <div className="flex justify-between">
                    <div className="flex items-center">
                      <TableOfContents className="h-4 w-4 mr-2" />
                      <TypographySmall>Frames:</TypographySmall>
                    </div>
                    <TypographySmall>
                      {inferenceResults.frame_count}
                    </TypographySmall>
                  </div>
                  <div className="flex justify-between">
                    <div className="flex items-center">
                      <Clock2 className="h-4 w-4 mr-2" />
                      <TypographySmall>Last Updated:</TypographySmall>
                    </div>
                    <TypographySmall>
                      {formatDateTime(inferenceResults.updated_at)}
                    </TypographySmall>
                  </div>
                </div>
              ) : (
                <div className="text-center py-2 text-muted-foreground">
                  No inference data available
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                <TypographyH4>Download Dataset</TypographyH4>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={handleDownloadCoco}
                  disabled={downloadCocoMutation.isPending || !videoId}
                >
                  <Nut className="h-4 w-4 mr-2" />
                  {downloadCocoMutation.isPending
                    ? "Downloading..."
                    : "COCO 1.0 Bounding Box"}
                </Button>
                <Button
                  className="w-full"
                  onClick={handleDownloadYolo}
                  disabled={downloadYoloMutation.isPending || !videoId}
                >
                  <Box className="h-4 w-4 mr-2" />
                  {downloadYoloMutation.isPending
                    ? "Downloading..."
                    : "Ultralytics YOLO 1.0 Detection"}
                </Button>
                <Button
                  className="w-full"
                  onClick={handleDownloadYoloSeg}
                  disabled={downloadYoloSegMutation.isPending || !videoId}
                >
                  <SquareDashedMousePointer className="h-4 w-4 mr-2" />
                  {downloadYoloSegMutation.isPending
                    ? "Downloading..."
                    : "Ultralytics YOLO 1.0 Segmentation"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
