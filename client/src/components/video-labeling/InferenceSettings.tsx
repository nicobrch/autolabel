import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TypographyH4 } from "@/components/typography/typography";
import { Button } from "@/components/ui/button";
import { Brain } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { propagateVideo } from "@/services/api";
import { toast } from "sonner";
import { useModelStore } from "@/stores/modelStore";

interface InferenceSettingsProps {
  onLabelVideo: () => void;
  videoId: string;
  projectId: string;
}

export function InferenceSettings({
  onLabelVideo,
  videoId,
  projectId,
}: InferenceSettingsProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();
  const { modelCheckpoint, setModelCheckpoint } = useModelStore();

  const handleLabelVideo = async () => {
    if (!videoId) {
      toast.error("Video ID is missing");
      return;
    }

    setIsProcessing(true);

    try {
      toast.info("Processing video", {
        description:
          "Propagating object masks through the video. This may take a while...",
        duration: 5000,
      });

      const result = await propagateVideo({
        videoId,
        checkpoint: modelCheckpoint,
      });

      // Call parent callback
      onLabelVideo();

      toast.success("Video processed successfully", {
        description: "Object masks have been propagated through the video.",
      });

      // Redirect to the labeled preview page
      navigate(`/projects/${projectId}/download/${result.video_id}`);
    } catch (error) {
      console.error("Failed to propagate video:", error);

      // Improved error display
      let errorMessage = "An unexpected error occurred";
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      toast.error("Failed to propagate video", {
        description: errorMessage,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <TypographyH4>Inference Settings</TypographyH4>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="model-checkpoint">Model Checkpoint</Label>
          <Select
            value={modelCheckpoint}
            onValueChange={setModelCheckpoint}
            disabled={isProcessing}
          >
            <SelectTrigger id="model-checkpoint" className="w-full">
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="tiny">SAM2-Tiny</SelectItem>
              <SelectItem value="small">SAM2-Small</SelectItem>
              <SelectItem value="base-plus">SAM2-BasePlus</SelectItem>
              <SelectItem value="large">SAM2-Large</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button
          className="w-full"
          onClick={handleLabelVideo}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
              Processing Video...
            </>
          ) : (
            <>
              <Brain className="h-4 w-4 mr-2" />
              Label Video
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
