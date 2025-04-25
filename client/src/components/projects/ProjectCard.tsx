import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { NavLink } from "react-router";

interface ProjectCardProps {
  id: number;
  name: string;
  description: string;
}

export function ProjectCard({ id, name, description }: ProjectCardProps) {
  return (
    <NavLink to={`/projects/${id}`} className="no-underline">
      <Card>
        <CardHeader>
          <CardTitle>{name}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
      </Card>
    </NavLink>
  );
}
