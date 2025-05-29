import { getFileNameWithoutExtension } from "@/lib/utils";

const apiUrl = "http://localhost:8001/api/v1";
const publicUrl = "http://localhost:8001/public/videos";

export function getVideoUrl(fileName: string): string {
  const videoName = getFileNameWithoutExtension(fileName);
  return `${publicUrl}/${videoName}/base/${fileName}`;
}

export function getVideoInferenceUrl(fileName: string): string {
  const videoName = getFileNameWithoutExtension(fileName);
  return `${publicUrl}/${videoName}/inference/${videoName}_inference.mp4`;
}

export function getThumbnailFrameUrl(fileName: string): string {
  const videoName = getFileNameWithoutExtension(fileName);
  return `${publicUrl}/${videoName}/thumbnail/thumbnail.jpg`;
}

export function getInferenceThumbnailUrl(fileName: string): string {
  const videoName = getFileNameWithoutExtension(fileName);
  const baseUrl = `${publicUrl}/${videoName}/thumbnail/inference.jpg`;
  // Add a timestamp to prevent browser caching
  const timestamp = new Date().getTime();
  return `${baseUrl}?t=${timestamp}`;
}

interface ProjectData {
  id: number;
  name: string;
  description: string;
  created_at: string; // ISO date string
  video_count: number; // Add this new field
}

export async function fetchProjects(): Promise<ProjectData[]> {
  const response = await fetch(`${apiUrl}/projects`);

  if (!response.ok) {
    throw new Error("Failed to fetch projects");
  }

  return response.json();
}

interface FrameCount {
  frame_count: number;
}

export async function fetchVideoFrameCount(
  videoId: string,
): Promise<FrameCount> {
  const response = await fetch(`${apiUrl}/videos/${videoId}/frames/count`);
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
  has_inference: boolean;
}

export async function fetchVideos(videoId: string): Promise<Video[]> {
  const response = await fetch(`${apiUrl}/projects/${videoId}/videos`);
  if (!response.ok) {
    const errorData = await response.text();
    console.error("Fetch videos error:", errorData);
    throw new Error(
      `HTTP error! status: ${response.status} - Failed to fetch videos for project ${videoId}`,
    );
  }
  try {
    return await response.json();
  } catch (e) {
    console.error("Failed to parse videos JSON:", e);
    throw new Error("Received invalid data format from server.");
  }
}

export async function fetchVideoById(videoId: string): Promise<Video> {
  const response = await fetch(`${apiUrl}/videos/${videoId}`);
  if (!response.ok) {
    const errorData = await response.text();
    console.error("Fetch video error:", errorData);
    throw new Error(
      `HTTP error! status: ${response.status} - Failed to fetch video ${videoId}`,
    );
  }
  try {
    return await response.json();
  } catch (e) {
    console.error("Failed to parse video JSON:", e);
    throw new Error("Received invalid data format from server.");
  }
}

export async function uploadVideoFile(
  videoId: number,
  file: File,
  resolution?: string,
  fps?: number,
): Promise<Video> {
  const formData = new FormData();
  formData.append("file", file);

  let url = `${apiUrl}/videos/upload?project_id=${videoId}`;
  if (resolution) {
    url += `&resolution=${encodeURIComponent(resolution)}`;
  }
  if (fps !== undefined) {
    url += `&target_fps=${fps}`;
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

export interface VideoObject {
  id: number;
  name: string;
  video_id: number;
  color: string;
  created_at?: string; // ISO date string
  updated_at?: string; // ISO date string
}

export async function fetchVideoObjects(
  videoId: string,
): Promise<VideoObject[]> {
  const response = await fetch(`${apiUrl}/videos/${videoId}/objects`);

  if (!response.ok) {
    const errorData = await response.text();
    console.error("Fetch video objects error:", errorData);
    throw new Error(
      `HTTP error! status: ${response.status} - Failed to fetch objects for video ${videoId}`,
    );
  }

  try {
    return await response.json();
  } catch (e) {
    console.error("Failed to parse video objects JSON:", e);
    throw new Error("Received invalid data format from server.");
  }
}

export async function createVideoObject(
  videoId: string,
  data: { name: string; color?: string },
): Promise<VideoObject> {
  const response = await fetch(`${apiUrl}/videos/${videoId}/objects`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    let errorDetail = "Failed to create object";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      const textError = await response.text().catch(() => "");
      if (textError) {
        errorDetail = textError;
      }
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function updateVideoObject(
  videoId: string,
  objectId: string,
  data: { name: string; color?: string },
): Promise<VideoObject> {
  const response = await fetch(
    `${apiUrl}/videos/${videoId}/objects/${objectId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    let errorDetail = "Failed to update object";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      const textError = await response.text().catch(() => "");
      if (textError) {
        errorDetail = textError;
      }
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

interface LabelFrameParams {
  videoId: string;
  objectId: number;
  x: number;
  y: number;
  label: number;
  checkpoint: string;
}

interface LabelFrameResponse {
  status: "success" | "partial_success";
  objects: Array<{
    id: number;
    name: string;
    color: string;
    segmented: boolean;
    error?: string;
  }>;
  visualization_url: string;
  error?: string;
}

export async function labelVideoFrame(
  params: LabelFrameParams,
): Promise<LabelFrameResponse> {
  const { videoId, objectId, x, y, label, checkpoint } = params;

  const response = await fetch(`${apiUrl}/videos/${videoId}/label_frame`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      object_id: objectId,
      x,
      y,
      label,
      checkpoint,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || `Failed to label frame (status: ${response.status})`,
    );
  }

  return response.json();
}

interface PropagateVideoParams {
  videoId: string;
  checkpoint: string;
}

interface PropagateVideoResponse {
  status: "success";
  video_path: string;
  video_id: number;
}

export async function propagateVideo(
  params: PropagateVideoParams,
): Promise<PropagateVideoResponse> {
  const { videoId, checkpoint } = params;

  const response = await fetch(`${apiUrl}/videos/${videoId}/propagate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      checkpoint,
    }),
  });

  if (!response.ok) {
    try {
      const errorData = await response.json();
      // Handle structured error response
      if (errorData && typeof errorData === "object") {
        if (errorData.detail) {
          throw new Error(errorData.detail);
        } else {
          throw new Error(JSON.stringify(errorData));
        }
      }
      throw new Error(`Failed to propagate video (status: ${response.status})`);
    } catch (e) {
      // If JSON parsing fails, try to get text
      if (e instanceof Error) {
        throw e;
      }
      const errorText = await response
        .text()
        .catch(() => `Failed to propagate video (status: ${response.status})`);
      throw new Error(
        errorText || `Failed to propagate video (status: ${response.status})`,
      );
    }
  }

  return response.json();
}

/**
 * Requests the server to generate and then download a YOLO dataset ZIP file
 * @returns A promise that resolves when the ZIP file is ready for download
 */
export async function prepareYoloDatasetDownload(
  videoId: string,
): Promise<boolean> {
  try {
    // First make a HEAD request to check if the endpoint is ready
    const checkResponse = await fetch(
      `${apiUrl}/videos/${videoId}/download-yolo-dataset`,
      {
        method: "HEAD",
      },
    );

    if (!checkResponse.ok) {
      throw new Error(`Server not ready: ${checkResponse.status}`);
    }

    // If HEAD request is successful, trigger the download
    downloadYoloDataset(videoId);
    return true;
  } catch (error) {
    console.error("Error preparing YOLO dataset download:", error);
    throw error;
  }
}

/**
 * Initiates a download of the YOLO dataset for the specified video
 */
export function downloadYoloDataset(videoId: string): void {
  // Using window.open to trigger a file download in a new tab
  window.open(`${apiUrl}/videos/${videoId}/download-yolo-dataset`, "_blank");
}

/**
 * Requests the server to generate and then download a COCO dataset ZIP file
 * @returns A promise that resolves when the ZIP file is ready for download
 */
export async function prepareCocoDatasetDownload(
  videoId: string,
): Promise<boolean> {
  try {
    // First make a HEAD request to check if the endpoint is ready
    const checkResponse = await fetch(
      `${apiUrl}/videos/${videoId}/download-coco-dataset`,
      {
        method: "HEAD",
      },
    );

    if (!checkResponse.ok) {
      throw new Error(`Server not ready: ${checkResponse.status}`);
    }

    // If HEAD request is successful, trigger the download
    downloadCocoDataset(videoId);
    return true;
  } catch (error) {
    console.error("Error preparing COCO dataset download:", error);
    throw error;
  }
}

/**
 * Initiates a download of the COCO dataset for the specified video
 */
export function downloadCocoDataset(videoId: string): void {
  // Using window.open to trigger a file download in a new tab
  window.open(`${apiUrl}/videos/${videoId}/download-coco-dataset`, "_blank");
}

/**
 * Deletes the last point added to the specified object
 */
export async function deleteLastPoint(
  videoId: string,
  objectId: string,
  checkpoint: string = "tiny",
): Promise<{ status: string; message: string }> {
  const response = await fetch(
    `${apiUrl}/videos/${videoId}/objects/${objectId}/points`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(checkpoint),
    },
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail ||
        `Failed to delete last point (status: ${response.status})`,
    );
  }

  return response.json();
}

export interface InferenceResults {
  original_video: string;
  inference_video: string;
  model_checkpoint: string;
  fps: number;
  frame_count: number;
  created_at: string;
  updated_at: string;
}

export async function fetchInferenceResults(
  videoId: string,
): Promise<InferenceResults> {
  const response = await fetch(`${apiUrl}/videos/${videoId}/inference_results`);

  if (!response.ok) {
    const errorData = await response.text();
    console.error("Fetch inference results error:", errorData);
    throw new Error(
      `HTTP error! status: ${response.status} - Failed to fetch inference results for video ${videoId}`,
    );
  }

  try {
    return await response.json();
  } catch (e) {
    console.error("Failed to parse inference results JSON:", e);
    throw new Error("Received invalid data format from server.");
  }
}

/**
 * Deletes a video and all its associated data
 */
export async function deleteVideo(videoId: string): Promise<void> {
  const response = await fetch(`${apiUrl}/videos/${videoId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    let errorDetail = "Failed to delete video";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      const textError = await response.text().catch(() => "");
      if (textError) {
        errorDetail = textError;
      }
    }
    throw new Error(errorDetail);
  }
}

/**
 * Deletes a project and all its associated data
 */
export async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`${apiUrl}/projects/${projectId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    let errorDetail = "Failed to delete project";
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorDetail = errorData.detail;
      }
    } catch (e) {
      const textError = await response.text().catch(() => "");
      if (textError) {
        errorDetail = textError;
      }
    }
    throw new Error(errorDetail);
  }
}
