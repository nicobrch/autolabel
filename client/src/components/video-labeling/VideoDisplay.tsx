import { MouseEvent, useEffect, useState } from "react";
import { AspectRatio } from "@/components/ui/aspect-ratio";

interface VideoDisplayProps {
  imageUrl: string;
  onImageClick: (event: MouseEvent<HTMLImageElement>) => void;
  currentFrame: number;
  totalFrames: number;
  hasSelectedObject?: boolean;
}

export function VideoDisplay({
  imageUrl,
  onImageClick,
  currentFrame,
  totalFrames,
  hasSelectedObject = false,
}: VideoDisplayProps) {
  // State to store the cache-busting URL
  const [cacheBustedUrl, setCacheBustedUrl] = useState("");

  // Update the cache-busted URL whenever the original URL changes
  useEffect(() => {
    if (!imageUrl) return;

    // Add a timestamp query parameter to bypass browser cache
    const timestamp = new Date().getTime();
    const separator = imageUrl.includes("?") ? "&" : "?";
    setCacheBustedUrl(`${imageUrl}${separator}t=${timestamp}`);
  }, [imageUrl]);

  return (
    <AspectRatio ratio={16 / 9}>
      <img
        src={cacheBustedUrl || imageUrl}
        alt="Video frame"
        width={1280}
        height={720}
        className={`w-full h-full rounded-md object-cover shadow-sm border-1 ${
          hasSelectedObject ? "cursor-crosshair" : "cursor-default"
        }`}
        onClick={onImageClick}
      />
      <div className="absolute bottom-4 left-4 bg-accent px-3 py-1 rounded-md text-sm opacity-100 hover:opacity-0 transition-opacity duration-300">
        Frame: {currentFrame}/{totalFrames}
      </div>
    </AspectRatio>
  );
}
