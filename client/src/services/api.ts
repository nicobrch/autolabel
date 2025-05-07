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

interface CreateProjectData {
  name: string;
  description: string;
}

export async function createProject(
  data: CreateProjectData
): Promise<ProjectData> {
  const response = await fetch("http://localhost:8000/api/v1/projects", {
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

// Add the Video type definition
export interface Video {
    id: string | number;
    name: string;
    description?: string;
    thumbnailUrl?: string; // Optional thumbnail URL
    // Add other relevant video properties if needed
}

// Add the function to fetch videos for a specific project
export async function fetchVideos(projectId: string): Promise<Video[]> {
    const response = await fetch(`/api/project/${projectId}/videos`); // Adjust API endpoint as needed
    if (!response.ok) {
        // Provide more specific error messages if possible
        const errorData = await response.text(); // Try to get error details
        console.error("Fetch videos error:", errorData);
        throw new Error(`HTTP error! status: ${response.status} - Failed to fetch videos for project ${projectId}`);
    }
    try {
        return await response.json();
    } catch (e) {
        console.error("Failed to parse videos JSON:", e);
        throw new Error("Received invalid data format from server.");
    }
}
