interface FileData {
  title: string;
  metadata: string;
  thumbnail: string;
}

export async function fetchFiles(): Promise<FileData[]> {
  const response = await fetch("http://localhost:8000/files");

  if (!response.ok) {
    throw new Error("Failed to fetch files");
  }

  return response.json();
}
