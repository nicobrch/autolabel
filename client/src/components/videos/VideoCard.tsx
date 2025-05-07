import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { NavLink } from "react-router";

interface VideoCardProps {
  id: string | number;
  name: string;
  description?: string;
  imageUrl: string;
}

export function VideoCard({ id, name, description, imageUrl }: VideoCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="truncate">{name}</CardTitle>
        {description && (
          <CardDescription className="h-10 overflow-hidden text-ellipsis">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-grow">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt={`Thumbnail for ${name}`}
          className="aspect-video w-full rounded-md object-cover"
          // Add error handling for image loading if needed
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.onerror = null; // Prevent infinite loop
            target.src = "/placeholder-image.png"; // Fallback image
          }}
        />
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
