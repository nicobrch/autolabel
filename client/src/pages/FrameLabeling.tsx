import { useState } from "react";
import { Pen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

export default function FrameLabeling() {
  const [videoName, setVideoName] = useState("Street_Scene_001.mp4");
  const [frameStep, setFrameStep] = useState(5);
  const [resolution, setResolution] = useState("720p");
  const [modelCheckpoint, setModelCheckpoint] = useState("YOLOv8-L");
  const [selectedObject, setSelectedObject] = useState("Person");

  return (
    <div className="flex flex-col w-full p-6 bg-black text-white min-h-screen">
      <div className="flex items-center mb-6">
        <h1 className="text-2xl font-bold">Video Labeling</h1>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Video Preview */}
        <div className="flex-1">
          <div className="relative aspect-video w-full bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800">
            <img
              src="/placeholder.svg?height=720&width=1280"
              alt="Video first frame"
              width={1280}
              height={720}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-4 left-4 bg-black/70 px-3 py-1 rounded-md text-sm">
              Frame: 1/240
            </div>
          </div>
        </div>

        {/* Settings Panels */}
        <div className="w-full lg:w-80 space-y-6">
          {/* Video Settings Panel */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-medium">
                Video Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="video-name">Video Name</Label>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Pen className="h-4 w-4" />
                    <span className="sr-only">Edit video name</span>
                  </Button>
                </div>
                <Input
                  id="video-name"
                  value={videoName}
                  onChange={(e) => setVideoName(e.target.value)}
                  className="bg-zinc-950 border-zinc-800"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="frame-step">Frame Step</Label>
                <Input
                  id="frame-step"
                  type="number"
                  value={frameStep}
                  onChange={(e) =>
                    setFrameStep(Number.parseInt(e.target.value))
                  }
                  min={1}
                  className="bg-zinc-950 border-zinc-800"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="resolution">Resolution</Label>
                <Select value={resolution} onValueChange={setResolution}>
                  <SelectTrigger
                    id="resolution"
                    className="bg-zinc-950 border-zinc-800"
                  >
                    <SelectValue placeholder="Select resolution" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800">
                    <SelectItem value="480p">480p</SelectItem>
                    <SelectItem value="720p">720p</SelectItem>
                    <SelectItem value="1080p">1080p</SelectItem>
                    <SelectItem value="1440p">1440p</SelectItem>
                    <SelectItem value="2160p">2160p (4K)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model-checkpoint">Model Checkpoint</Label>
                <Select
                  value={modelCheckpoint}
                  onValueChange={setModelCheckpoint}
                >
                  <SelectTrigger
                    id="model-checkpoint"
                    className="bg-zinc-950 border-zinc-800"
                  >
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800">
                    <SelectItem value="YOLOv8-S">YOLOv8-S</SelectItem>
                    <SelectItem value="YOLOv8-M">YOLOv8-M</SelectItem>
                    <SelectItem value="YOLOv8-L">YOLOv8-L</SelectItem>
                    <SelectItem value="DETR">DETR</SelectItem>
                    <SelectItem value="Mask-RCNN">Mask-RCNN</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Labeling Options Panel */}
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-medium">
                Labeling Options
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="object-type">Object</Label>
                <Select
                  value={selectedObject}
                  onValueChange={setSelectedObject}
                >
                  <SelectTrigger
                    id="object-type"
                    className="bg-zinc-950 border-zinc-800"
                  >
                    <SelectValue placeholder="Select object" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800">
                    <SelectItem value="Person">Person</SelectItem>
                    <SelectItem value="Vehicle">Vehicle</SelectItem>
                    <SelectItem value="Animal">Animal</SelectItem>
                    <SelectItem value="Building">Building</SelectItem>
                    <SelectItem value="Custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <Label>Point Type</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <RadioGroup>
                      <RadioGroupItem value="positive" id="positive">
                        <Label htmlFor="positive">Positive</Label>
                      </RadioGroupItem>
                      <RadioGroupItem value="negative" id="negative">
                        <Label htmlFor="negative">Negative</Label>
                      </RadioGroupItem>
                    </RadioGroup>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
