import { MouseEvent } from "react";
import { AspectRatio } from "@/components/ui/aspect-ratio";

interface VideoDisplayProps {
  imageUrl: string;
  onImageClick: (event: MouseEvent<HTMLImageElement>) => void;
  currentFrame: number;
  totalFrames: number;
}

export function VideoDisplay({
  imageUrl,
  onImageClick,
  currentFrame,
  totalFrames,
}: VideoDisplayProps) {
  return (
    <div className="flex-1">
      <AspectRatio ratio={16 / 9}>
        <img
          src={imageUrl}
          alt="Video frame"
          width={1280}
          height={720}
          className="w-full h-full rounded-md object-cover shadow-sm border-1 cursor-crosshair"
          onClick={onImageClick}
        />
        <div className="absolute bottom-4 left-4 bg-accent px-3 py-1 rounded-md text-sm">
          Frame: {currentFrame}/{totalFrames}
        </div>
      </AspectRatio>
    </div>
  );
}
