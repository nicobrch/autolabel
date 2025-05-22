import { AspectRatio } from "@/components/ui/aspect-ratio";
import { TypographyH4 } from "@/components/typography/typography";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Download, Nut, Box, Drama } from "lucide-react";
import { useParams } from "react-router";
import { ContentHeader } from "@/components/layout/ContentHeader";
import {
  fetchVideoById,
  getVideoInferenceUrl,
  getInferenceThumbnailUrl,
} from "@/services/api";
import { useQuery } from "@tanstack/react-query";

export default function VideoLabeledPreview() {
  let { videoId } = useParams();

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
                <TypographyH4>Download Results</TypographyH4>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="model-checkpoint">Labels</Label>
                <Button className="w-full" variant="outline">
                  <Nut className="h-4 w-4 mr-2" />
                  Download COCO labels
                </Button>
                <Button className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Download YOLO labels
                </Button>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model-checkpoint">Segmentation</Label>
                <Button className="w-full" variant="outline">
                  <Box className="h-4 w-4 mr-2" />
                  Download Video Preview
                </Button>
                <Button className="w-full" variant="secondary">
                  <Drama className="h-4 w-4 mr-2" />
                  Download Object Masks
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
