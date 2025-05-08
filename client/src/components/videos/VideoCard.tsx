import { Card, CardContent, CardFooter, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar, Tag, Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatDuration } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { TypographyH4 } from "../typography/typography";
import { NavLink } from "react-router";
import { getFileNameWithoutExtension } from "@/lib/utils";

interface VideoCardProps {
  id: string | number;
  name: string;
  duration: number;
  dateCreated: string;
  imageUrl: string;
}

export function VideoCard({
  id,
  name,
  duration,
  dateCreated,
  imageUrl,
}: VideoCardProps) {
  return (
    <Card className="group overflow-hidden p-0 transition-all duration-300 hover:shadow-md min-w-xs max-w-xs">
      <div className="relative overflow-hidden">
        <img
          src={imageUrl || "/placeholder.svg"}
          width={1280}
          height={720}
          alt={`Thumbnail for ${name}`}
          className="aspect-video w-full object-cover transition-transform duration-500 group-hover:scale-105"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.onerror = null;
            target.src = "/placeholder.svg?height=1280&width=720";
          }}
        />
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <Badge
            variant="secondary"
            className="bg-background/50 hover:bg-background/60"
          >
            {typeof duration === "number" ? formatDuration(duration) : duration}
          </Badge>
        </div>
      </div>

      <CardTitle className="px-4">
        <TypographyH4>{getFileNameWithoutExtension(name)}</TypographyH4>
      </CardTitle>

      <CardContent className="flex items-center text-sm text-muted-foreground -mt-2">
        <Calendar className="mr-1.5 h-4 w-4" />
        {formatDate(dateCreated)}
      </CardContent>

      <CardFooter className="flex justify-between gap-2 pb-3 px-4">
        <Button variant="default" size="sm" className="flex-1" asChild>
          <NavLink to={`/label/${id}`}>
            <Tag className="mr-1.5 h-4 w-4" />
            Label
          </NavLink>
        </Button>

        <Button variant="outline" size="sm" className="flex-1" asChild>
          <NavLink to={`/results/${id}`}>
            <Download className="mr-1.5 h-4 w-4" />
            Download
          </NavLink>
        </Button>
      </CardFooter>
    </Card>
  );
}
