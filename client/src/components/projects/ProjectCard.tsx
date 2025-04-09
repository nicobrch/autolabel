interface ProjectCardProps {
  name: string;
  description: string;
}

export function ProjectCard({ name, description }: ProjectCardProps) {
  return (
    <div className="group relative overflow-hidden rounded-lg border bg-white">
      <div className="p-4">
        <h3 className="font-medium text-gray-900">{name}</h3>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </div>
  );
}
