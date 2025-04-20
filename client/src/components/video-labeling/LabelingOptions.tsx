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
import { Plus } from "lucide-react";

interface LabelingOptionsProps {
  selectedObject: string;
  onSelectedObjectChange: (value: string) => void;
  pointType: string;
  onPointTypeChange: (value: string) => void;
  onCreateObject: () => void; // Assuming a function prop for the button click
}

export function LabelingOptions({
  selectedObject,
  onSelectedObjectChange,
  pointType,
  onPointTypeChange,
  onCreateObject,
}: LabelingOptionsProps) {
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
          <Button className="w-full" onClick={onCreateObject}>
            <Plus className="h-4 w-4 mr-2" />
            Create New Object
          </Button>
        </div>

        <div className="space-y-2">
          <Label htmlFor="object-type">Current Selected Object</Label>
          <Select value={selectedObject} onValueChange={onSelectedObjectChange}>
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
          <RadioGroup value={pointType} onValueChange={onPointTypeChange}>
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
      </CardContent>
    </Card>
  );
}
