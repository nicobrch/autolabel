import { formatDate } from "@/lib/utils";
import { TypographySmall } from "../typography/typography";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { NavLink } from "react-router";
import { Calendar, FileVideo } from "lucide-react";

interface ProjectCardProps {
  id: number;
  name: string;
  description: string;
  dateCreated: string; // ISO date string
  videoCount: number;
}

export function ProjectCard({ id, name, description, dateCreated, videoCount = 0 }: ProjectCardProps) {
  return (
    <NavLink to={`/projects/${id}`} className="no-underline">
      <Card>
        <CardHeader>
          <CardTitle>{name}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col space-y-2 -mt-2">
        <div className="flex justify-between">
          <div className="flex items-center">
            <FileVideo className="mr-1.5 h-4 w-4" />
            <TypographySmall>{videoCount}</TypographySmall>
          </div>
          <div className="flex items-center">
            <Calendar className="mr-1.5 h-4 w-4" />
            <TypographySmall>{formatDate(dateCreated)}</TypographySmall>
          </div>
        </div>
      </CardContent>
      </Card>
    </NavLink>
  );
}
