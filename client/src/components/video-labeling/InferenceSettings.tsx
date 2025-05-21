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

interface InferenceSettingsProps {
  modelCheckpoint: string;
  onModelCheckpointChange: (value: string) => void;
  onLabelVideo: () => void;
}

export function InferenceSettings({
  modelCheckpoint,
  onModelCheckpointChange,
  onLabelVideo,
}: InferenceSettingsProps) {
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
            onValueChange={onModelCheckpointChange}
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
        <Button className="w-full" onClick={onLabelVideo}>
          <Brain className="h-4 w-4 mr-2" />
          Label Video
        </Button>
      </CardContent>
    </Card>
  );
}
