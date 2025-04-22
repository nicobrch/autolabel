import { Button } from "@/components/ui/button";
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
    <div className="flex flex-1 items-center gap-2">
      <Button className="flex-1" onClick={onLabelVideo}>
        <Brain className="h-4 w-4 mr-2" />
        Label Video
      </Button>
      <Button
        variant="outline"
        className="flex-1"
        disabled={isDownloadDisabled}
        onClick={onDownloadLabels}
      >
        <Download className="h-4 w-4 mr-2" />
        Download Labels
      </Button>
    </div>
  );
}
