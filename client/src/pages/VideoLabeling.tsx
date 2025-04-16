import { useState, MouseEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { TypographyH4 } from "@/components/typography/typography";
import { Plus, Brain, Download } from "lucide-react";
import { AspectRatio } from "@/components/ui/aspect-ratio";

export default function VideoLabeling() {
  const [modelCheckpoint, setModelCheckpoint] = useState("SAM2-T");
  const [selectedObject, setSelectedObject] = useState("Person");
  const [pointType, setPointType] = useState("positive");

  const handleImageClick = (event: MouseEvent<HTMLImageElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    // Calculate click coordinates relative to the image element
    // NOTE: If the image is scaled/resized within the element,
    // further calculations might be needed based on naturalWidth/Height vs clientWidth/Height.
    // For now, offsetX/Y provides coordinates relative to the element's padding box.
    const x = event.nativeEvent.offsetX;
    const y = event.nativeEvent.offsetY;
    console.log(`Clicked at (relative): x=${x}, y=${y}`);
    // TODO: Store or send these coordinates as needed
  };

  return (
    <div className="flex flex-col w-full p-6">
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1">
          <AspectRatio ratio={16 / 9}>
            <img
              src="/placeholder.svg?height=720&width=1280"
              alt="Video first frame"
              width={1280}
              height={720}
              className="w-full h-full rounded-md object-cover shadow-sm border-1 cursor-crosshair"
              onClick={handleImageClick}
            />
            <div className="absolute bottom-4 left-4 bg-accent px-3 py-1 rounded-md text-sm">
              Frame: 1/240
            </div>
          </AspectRatio>
        </div>

        <div className="w-full lg:w-80 space-y-6">
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
                >
                  <SelectTrigger id="model-checkpoint" className="w-full">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SAM2-T">SAM2-Tiny</SelectItem>
                    <SelectItem value="SAM2-S">SAM2-Small</SelectItem>
                    <SelectItem value="SAM2-BP">SAM2-BasePlus</SelectItem>
                    <SelectItem value="SAM2-L">SAM2-Large</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                <TypographyH4>Labeling Options</TypographyH4>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="object-type">Create Object</Label>
                <Button className="w-full">
                  <Plus className="h-4 w-4" />
                  Create New Object
                </Button>
              </div>

              <div className="space-y-2">
                <Label htmlFor="object-type">Current Selected Object</Label>
                <Select
                  value={selectedObject}
                  onValueChange={setSelectedObject}
                >
                  <SelectTrigger id="object-type" className="w-full">
                    <SelectValue placeholder="Select object" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Person">Person</SelectItem>
                    <SelectItem value="Vehicle">Vehicle</SelectItem>
                    <SelectItem value="Animal">Animal</SelectItem>
                    <SelectItem value="Building">Building</SelectItem>
                    <SelectItem value="Custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-4">
                <Label>Point Type</Label>
                <div className="space-y-2">
                  <RadioGroup value={pointType} onValueChange={setPointType}>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="positive" id="positive" />
                      <Label htmlFor="positive">Positive</Label>
                      <RadioGroupItem value="negative" id="negative" />
                      <Label htmlFor="negative">Negative</Label>
                    </div>
                  </RadioGroup>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                <TypographyH4>Actions</TypographyH4>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="label-video">Propagate Segmentation</Label>
                <Button className="w-full">
                  <Brain className="h-4 w-4" />
                  Label Video
                </Button>
              </div>
              <div className="space-y-2">
                <Label htmlFor="download-labels">
                  Download Inference Results
                </Label>
                <Button variant="secondary" className="w-full" disabled>
                  <Download className="h-4 w-4" />
                  Download Labels
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
