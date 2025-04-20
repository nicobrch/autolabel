import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { TypographyH4 } from "@/components/typography/typography";
import { Brain, Download } from "lucide-react";

interface ActionButtonsProps {
  onLabelVideo: () => void; // Placeholder for future functionality
  onDownloadLabels: () => void; // Placeholder for future functionality
  isDownloadDisabled: boolean; // Example prop to control download button state
}

export function ActionButtons({
  onLabelVideo,
  onDownloadLabels,
  isDownloadDisabled,
}: ActionButtonsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <TypographyH4>Actions</TypographyH4>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="label-video">Propagate Segmentation</Label>
          <Button className="w-full" onClick={onLabelVideo}>
            <Brain className="h-4 w-4 mr-2" />
            Label Video
          </Button>
        </div>
        <div className="space-y-2">
          <Label htmlFor="download-labels">Download Inference Results</Label>
          <Button
            variant="secondary"
            className="w-full"
            disabled={isDownloadDisabled}
            onClick={onDownloadLabels}
          >
            <Download className="h-4 w-4 mr-2" />
            Download Labels
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
