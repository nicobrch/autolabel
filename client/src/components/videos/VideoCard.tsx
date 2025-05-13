import { Card, CardContent, CardFooter, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  Tag,
  Download,
  Clock,
  Save,
  Proportions,
} from "lucide-react";
import { formatDuration, formatFileSize } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { TypographyH4 } from "../typography/typography";
import { NavLink } from "react-router";
import { getFileNameWithoutExtension } from "@/lib/utils";
import { useParams } from "react-router";

interface VideoCardProps {
  id: string | number;
  name: string;
  duration: number;
  size: number;
  resolution: string;
  dateCreated: string;
  videoPath: string;
}

export function VideoCard({
  id,
  name,
  duration,
  size,
  resolution,
  dateCreated,
  videoPath,
}: VideoCardProps) {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <Card className="group overflow-hidden p-0 transition-all duration-300 hover:shadow-md">
      <div className="relative overflow-hidden">
        <video
          src={videoPath || "/placeholder.svg"}
          width={1280}
          height={720}
          poster="/placeholder.svg"
          className="aspect-video w-full object-cover"
          controls
          muted
          preload="metadata"
        />
      </div>

      <CardTitle className="px-4">
        <TypographyH4>{getFileNameWithoutExtension(name)}</TypographyH4>
      </CardTitle>

      <CardContent className="flex flex-col space-y-2 text-sm text-muted-foreground -mt-2">
        <div className="flex justify-between">
          <div className="flex items-center">
            <Calendar className="mr-1.5 h-4 w-4" />
            {formatDate(dateCreated)}
          </div>
          <div className="flex items-center">
            <Clock className="mr-1.5 h-4 w-4" />
            {formatDuration(duration)}
          </div>
        </div>
        <div className="flex justify-between">
          <div className="flex items-center">
            <Save className="mr-1.5 h-4 w-4" />
            {formatFileSize(size)}
          </div>
          <div className="flex items-center">
            <Proportions className="mr-1.5 h-4 w-4" />
            {resolution}
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
