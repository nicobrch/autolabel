import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";

interface ProjectCardProps {
  name: string;
  description: string;
}

export function ProjectCard({ name, description }: ProjectCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
    </Card>
  );
}
