import { AspectRatio } from "@/components/ui/aspect-ratio";
import { TypographyH4 } from "@/components/typography/typography";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Download, Nut, Box, Drama } from "lucide-react";
import { useParams } from "react-router";
import { ContentHeader } from "@/components/layout/ContentHeader";

export default function VideoLabeledPreview() {
  let { videoId } = useParams();
  console.log("Video ID:", videoId);

  const handleDownload = (url: string) => {
    // Create a temporary link element
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", ""); // lets browser treat it as a download
    // Append link to the body, click it, and remove it
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getApiUrl = (downloadType: string) => {
    // Replace with your actual API base URL structure if different
    return `/api/videos/${videoId}/download/${downloadType}`;
  };

  return (
    <div className="flex flex-col w-full p-4">
      <ContentHeader />
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1">
          <AspectRatio ratio={16 / 9}>
            <video
              src={"/placeholder.svg?height=720&width=1280"}
              width={1280}
              height={720}
              className="w-full h-full rounded-md object-cover shadow-sm border-1"
            />
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
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => handleDownload(getApiUrl("coco"))}
                >
                  <Nut className="h-4 w-4 mr-2" />
                  Download COCO labels
                </Button>
                <Button
                  className="w-full"
                  onClick={() => handleDownload(getApiUrl("yolo"))}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download YOLO labels
                </Button>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model-checkpoint">Segmentation</Label>
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => handleDownload(getApiUrl("preview"))}
                >
                  <Box className="h-4 w-4 mr-2" />
                  Download Video Preview
                </Button>
                <Button
                  className="w-full"
                  variant="secondary"
                  onClick={() => handleDownload(getApiUrl("masks"))}
                >
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
