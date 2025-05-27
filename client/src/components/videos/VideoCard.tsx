import { Card, CardContent, CardFooter, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  Tag,
  Download,
  Clock,
  Save,
  Proportions,
  Trash2,
} from "lucide-react";
import { formatDuration, formatFileSize } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { TypographyH4, TypographySmall } from "../typography/typography";
import { NavLink } from "react-router";
import { getFileNameWithoutExtension } from "@/lib/utils";
import { useParams } from "react-router";
import { useState } from "react";
import { DeleteVideoDialog } from "./DeleteVideoDialog";

interface VideoCardProps {
  id: string | number;
  name: string;
  duration: number;
  size: number;
  resolution: string;
  dateCreated: string;
  videoPath: string;
  firstFramePath?: string; // Add this new prop for the first frame
}

export function VideoCard({
  id,
  name,
  duration,
  size,
  resolution,
  dateCreated,
  videoPath,
  firstFramePath,
}: VideoCardProps) {
  const { projectId } = useParams<{ projectId: string }>();
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  return (
    <Card className="group overflow-hidden p-0 transition-all duration-300 hover:shadow-md">
      <div className="relative overflow-hidden">
        <video
          src={videoPath || "/placeholder.svg"}
          width={1280}
          height={720}
          // Use the first frame as the poster if available, otherwise fall back to placeholder
          poster={firstFramePath || "/placeholder.svg"}
          className="aspect-video w-full object-cover"
          controls
          muted
          preload="metadata"
        />
      </div>

      <CardTitle className="flex justify-between px-4">
        {getFileNameWithoutExtension(name)}
        <button
          className="hover:text-destructive/80 text-destructive/50 transform hover:scale-105 transition-all duration-300"
          onClick={() => setIsDeleteDialogOpen(true)}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </CardTitle>

      {/* Delete Video Dialog */}
      <DeleteVideoDialog
        videoId={id}
        videoName={name}
        isOpen={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
        projectId={projectId}
      />

      <CardContent className="flex flex-col space-y-2 -mt-2">
        <div className="flex justify-between">
          <div className="flex items-center">
            <Calendar className="mr-1.5 h-4 w-4" />
            <TypographySmall>{formatDate(dateCreated)}</TypographySmall>
          </div>
          <div className="flex items-center">
            <Clock className="mr-1.5 h-4 w-4" />
            <TypographySmall>{formatDuration(duration)}</TypographySmall>
          </div>
        </div>
        <div className="flex justify-between">
          <div className="flex items-center">
            <Save className="mr-1.5 h-4 w-4" />
            <TypographySmall>{formatFileSize(size)}</TypographySmall>
          </div>
          <div className="flex items-center">
            <Proportions className="mr-1.5 h-4 w-4" />
            <TypographySmall>{resolution}</TypographySmall>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between gap-2 pb-3 px-4">
        <Button variant="default" size="sm" className="flex-1" asChild>
          <NavLink to={`/projects/${projectId}/label/${id}`}>
            <Tag className="mr-1.5 h-4 w-4" />
            Label
          </NavLink>
        </Button>

        <Button variant="outline" size="sm" className="flex-1" asChild>
          <NavLink to={`/projects/${projectId}/download/${id}`}>
            <Download className="mr-1.5 h-4 w-4" />
            Download
          </NavLink>
        </Button>
      </CardFooter>
    </Card>
  );
}
