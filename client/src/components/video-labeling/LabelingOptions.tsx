import { useState } from "react";
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
import { Plus, Undo2, Eraser, Pen } from "lucide-react";
import { VideoObject } from "@/services/api";
import { Dialog, DialogTrigger } from "@/components/ui/dialog";
import { CreateObjectForm } from "@/components/video-labeling/CreateObjectForm";
import { EditObjectForm } from "@/components/video-labeling/EditObjectForm";

interface LabelingOptionsProps {
  selectedObject: string;
  onSelectedObjectChange: (value: string) => void;
  pointType: string;
  onPointTypeChange: (value: string) => void;
  onCreateObject?: () => void; // Make optional since we'll handle it internally
  videoObjects: VideoObject[];
  isLoading?: boolean;
  videoId: string; // Add videoId prop to pass to CreateObjectForm
}

export function LabelingOptions({
  selectedObject,
  onSelectedObjectChange,
  pointType,
  onPointTypeChange,
  videoObjects,
  isLoading = false,
  videoId,
}: LabelingOptionsProps) {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  const selectedObjectData = selectedObject
    ? videoObjects.find((obj) => obj.id.toString() === selectedObject)
    : undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <TypographyH4>Labeling Options</TypographyH4>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="object-type">Create Object</Label>
          <div className="flex gap-2">
            <Dialog
              open={isCreateDialogOpen}
              onOpenChange={setIsCreateDialogOpen}
            >
              <DialogTrigger asChild>
                <Button className="flex-1">
                  <Plus className="h-4 w-4 mr-2" />
                  Create New Object
                </Button>
              </DialogTrigger>
              <CreateObjectForm
                videoId={videoId}
                setIsOpen={setIsCreateDialogOpen}
              />
            </Dialog>

            <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  size="icon"
                  disabled={!selectedObjectData}
                  title="Edit Selected Object"
                >
                  <Pen className="h-4 w-4" />
                </Button>
              </DialogTrigger>
              {selectedObjectData && (
                <EditObjectForm
                  videoId={videoId}
                  objectData={selectedObjectData}
                  setIsOpen={setIsEditDialogOpen}
                />
              )}
            </Dialog>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="object-type">Current Selected Object</Label>
          <div className="flex items-center space-x-2">
            <Select
              value={selectedObject}
              onValueChange={onSelectedObjectChange}
              disabled={isLoading || videoObjects.length === 0}
            >
              <SelectTrigger id="object-type" className="w-full">
                <SelectValue
                  placeholder={isLoading ? "Loading..." : "Select object"}
                />
              </SelectTrigger>
              <SelectContent>
                {videoObjects.length === 0 ? (
                  <SelectItem value="no-objects" disabled>
                    No objects available
                  </SelectItem>
                ) : (
                  videoObjects.map((obj) => (
                    <SelectItem
                      key={obj.id}
                      value={obj.id.toString()}
                      style={{ color: obj.color }}
                    >
                      {obj.name}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>

            {/* Color square - always displayed */}
            <div
              className="w-8 h-8 rounded-sm border flex-shrink-0"
              style={{
                backgroundColor: selectedObject
                  ? videoObjects.find(
                      (obj) => obj.id.toString() === selectedObject,
                    )?.color || "transparent"
                  : "transparent",
              }}
            />
          </div>
        </div>

        <div className="space-y-4">
          <Label>Point Type</Label>
          <RadioGroup
            value={pointType}
            onValueChange={onPointTypeChange}
            className="flex space-x-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="positive" id="positive" />
              <Label htmlFor="positive">Positive</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="negative" id="negative" />
              <Label htmlFor="negative">Negative</Label>
            </div>
          </RadioGroup>
        </div>

        <div className="space-y-4">
          <Label>Modify Segmentation Points</Label>
          <div className="flex flex-1 items-center space-x-2">
            <Button variant="default">
              <Undo2 className="h-4 w-4 mr-2" />
              Undo Last
            </Button>
            <Button variant="destructive">
              <Eraser className="h-4 w-4 mr-2" />
              Clear Points
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
