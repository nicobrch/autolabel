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
  data: CreateProjectData,
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
      `HTTP error! status: ${response.status} - Failed to fetch videos for project ${projectId}`,
    );
  }
  try {
    return await response.json();
  } catch (e) {
    console.error("Failed to parse videos JSON:", e);
    throw new Error("Received invalid data format from server.");
  }
}

export async function uploadVideoFile(
  projectId: number,
  file: File,
  resolution?: string,
  frameSkip?: number,
): Promise<Video> {
  const formData = new FormData();
  formData.append("file", file);

  let url = `${apiUrl}/videos/upload?project_id=${projectId}`;
  if (resolution) {
    url += `&resolution=${encodeURIComponent(resolution)}`;
  }
  if (frameSkip !== undefined) {
    url += `&frame_step=${frameSkip}`;
  }

  const response = await fetch(url, {
    method: "POST",
    body: formData,
    // Note: Do not set 'Content-Type' header manually when using FormData with fetch,
    // the browser will set it correctly with the required boundary.
  });

  if (!response.ok) {
    let errorDetail = "Failed to upload video";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorDetail = errorData.detail;
      } else if (typeof errorData === "string") {
        errorDetail = errorData;
      }
    } catch (e) {
      // If response is not JSON or parsing fails, try to get text
      const textError = await response.text().catch(() => "");
      if (textError) {
        errorDetail = textError;
      }
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
