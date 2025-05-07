import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { NavLink } from "react-router";
import { TypographyH3 } from "../typography/typography";
import { Calendar, Clock } from "lucide-react";

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
    <Card className="flex flex-col">
      <img
        src={imageUrl}
        alt={`Thumbnail for ${name}`}
        className="aspect-video w-full rounded-md object-cover transition-transform hover:scale-105"
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          target.onerror = null;
          target.src = "/placeholder.svg";
        }}
      />
      <CardHeader>
        <CardTitle>
          <TypographyH3>{name}</TypographyH3>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex justify-between gap-2">
        <div className="flex items-center text-sm text-muted-foreground">
          <Calendar className="mr-1 h-4 w-4" />
          {dateCreated}
        </div>
        <div className="flex items-center text-sm text-muted-foreground">
          <Clock className="mr-1 h-4 w-4" />
          {duration}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between gap-2">
        <Button variant="outline" size="sm" asChild>
          <NavLink to={`/label/${id}`}>Label</NavLink>
        </Button>
        <Button variant="secondary" size="sm" asChild>
          <NavLink to={`/results/${id}`}>Download</NavLink>
        </Button>
      </CardFooter>
    </Card>
  );
}
