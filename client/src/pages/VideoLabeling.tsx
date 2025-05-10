import { useState, MouseEvent } from "react";
import { VideoDisplay } from "@/components/video-labeling/VideoDisplay";
import { InferenceSettings } from "@/components/video-labeling/InferenceSettings";
import { LabelingOptions } from "@/components/video-labeling/LabelingOptions";
import { ActionButtons } from "@/components/video-labeling/ActionButtons";
import { Button } from "@/components/ui/button";
import { NavLink } from "react-router";
import { ArrowLeft } from "lucide-react";

export default function VideoLabeling() {
  const [modelCheckpoint, setModelCheckpoint] = useState("SAM2-T");
  const [selectedObject, setSelectedObject] = useState("Person");
  const [pointType, setPointType] = useState("positive");
  // Add state for frame numbers if dynamic
  const currentFrame = 1;
  const totalFrames = 240;

  const handleImageClick = async (event: MouseEvent<HTMLImageElement>) => {
    const imgElement = event.currentTarget;
    const rect = imgElement.getBoundingClientRect();

    // Get the displayed dimensions
    const displayWidth = rect.width;
    const displayHeight = rect.height;

    // Define the original/natural dimensions
    const naturalWidth = 1280;
    const naturalHeight = 720;

    // Calculate scaling factors
    const scaleX = naturalWidth / displayWidth;
    const scaleY = naturalHeight / displayHeight;

    // Calculate click coordinates relative to the image element
    const clickX = event.nativeEvent.offsetX;
    const clickY = event.nativeEvent.offsetY;

    // Scale coordinates to match the original image dimensions
    const x = Math.round(clickX * scaleX);
    const y = Math.round(clickY * scaleY);

    console.log(`Clicked at (relative): x=${clickX}, y=${clickY}`);
    console.log(`Scaled to ${naturalWidth}x${naturalHeight}: x=${x}, y=${y}`);

    // Determine label based on pointType state
    const label = pointType === "positive" ? 1 : 0;
    const object_id = 0; // Using object_id = 0 for now

    try {
      const response = await fetch(`/api/v1/objects/${object_id}/points`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ x, y, label }),
      });

      if (!response.ok) {
        // Handle non-successful responses (e.g., 4xx, 5xx)
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
          const errorData = await response.json();
          console.error("Error sending point:", response.status, errorData);
        } else {
          console.error(
            "Error sending point: Received non-JSON response",
            response.status,
            response.statusText
          );
        }
        // Optionally, show an error message to the user
      } else {
        // Handle successful response (e.g., 2xx)
        const result = await response.json();
        console.log("Point added successfully:", result);
        // Optionally, update UI or state based on success
      }
    } catch (error) {
      // Handle network errors or issues with the fetch call itself
      console.error("Failed to send point:", error);
      // Optionally, show an error message to the user
    }
  };

  // Placeholder handlers for new component props
  const handleCreateObject = () => {
    console.log("Create new object clicked");
    // Add logic to create a new object
  };

  const handleLabelVideo = () => {
    console.log("Label video clicked");
    // Add logic to start video labeling/propagation
  };

  return (
    <div className="flex flex-col w-full p-4">
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1 space-y-2">
          <Button variant="outline" className="gap-2" asChild>
            <NavLink to="/projects/1">
              <ArrowLeft className="h-4 w-4" />
              Back to Projects
            </NavLink>
          </Button>
          <VideoDisplay
            imageUrl="/placeholder.svg?height=720&width=1280" // Consider making this dynamic
            onImageClick={handleImageClick}
            currentFrame={currentFrame}
            totalFrames={totalFrames}
          />
        </div>

        <div className="w-full lg:w-80 space-y-6">
          <InferenceSettings
            modelCheckpoint={modelCheckpoint}
            onModelCheckpointChange={setModelCheckpoint}
          />

          <LabelingOptions
            selectedObject={selectedObject}
            onSelectedObjectChange={setSelectedObject}
            pointType={pointType}
            onPointTypeChange={setPointType}
            onCreateObject={handleCreateObject}
          />

          <ActionButtons onLabelVideo={handleLabelVideo} />
        </div>
      </div>
    </div>
  );
}
