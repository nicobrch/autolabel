const apiUrl = "http://localhost:8000/api/v1";

interface ProjectData {
  id: number;
  name: string;
  description: string;
}

export async function fetchProjects(): Promise<ProjectData[]> {
  const response = await fetch(`${apiUrl}/projects`);

  if (!response.ok) {
    throw new Error("Failed to fetch projects");
  }

  return response.json();
}

interface CreateProjectData {
  name: string;
  description: string;
}

export async function createProject(
  data: CreateProjectData
): Promise<ProjectData> {
  const response = await fetch(`${apiUrl}/projects`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error("Failed to create project");
  }

  return response.json();
}

export interface Video {
  id: number;
  project_id: number;
  file_path: string;
  file_name: string;
  file_size: number;
  width: number;
  height: number;
  fps: number;
  duration: number;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

export async function fetchVideos(projectId: string): Promise<Video[]> {
  const response = await fetch(`${apiUrl}/projects/${projectId}/videos`);
  if (!response.ok) {
    const errorData = await response.text();
    console.error("Fetch videos error:", errorData);
    throw new Error(
      `HTTP error! status: ${response.status} - Failed to fetch videos for project ${projectId}`
    );
  }
  try {
    return await response.json();
  } catch (e) {
    console.error("Failed to parse videos JSON:", e);
    throw new Error("Received invalid data format from server.");
  }
}
