interface ProjectData {
  id: number;
  name: string;
  description: string;
}

export async function fetchProjects(): Promise<ProjectData[]> {
  const response = await fetch("http://localhost:8000/api/v1/projects");

  if (!response.ok) {
    throw new Error("Failed to fetch projects");
  }

  return response.json();
}
