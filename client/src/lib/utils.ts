import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format duration to display as minutes:seconds
export const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

// Format date to YYYY-MM-DD
export const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const day = date.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
};

// Capitalize the first letter of a string
export const capitalize = (s: string) => {
  if (s.length === 0) return "";
  return s.charAt(0).toUpperCase() + s.slice(1);
};

export const getFileNameWithoutExtension = (filePath: string): string => {
  // Get the base name (the part after the last slash or the whole string if no slash)
  const lastSlashIndex = filePath.lastIndexOf("/");
  const fileNameWithExtension =
    lastSlashIndex === -1 ? filePath : filePath.substring(lastSlashIndex + 1);

  // Find the last dot in the base name
  const lastDotIndex = fileNameWithExtension.lastIndexOf(".");

  // If there's no dot, or if the dot is the first character (e.g., .env, .config),
  // then the entire fileNameWithExtension is considered the name without an extension.
  if (lastDotIndex <= 0) {
    return fileNameWithExtension;
  }

  // Otherwise, return the part before the last dot
  return fileNameWithExtension.substring(0, lastDotIndex);
};
