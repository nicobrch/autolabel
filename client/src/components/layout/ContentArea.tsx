import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { FileCard } from "../files/FileCard";
import { useQuery } from "@tanstack/react-query";
import { fetchFiles } from "@/services/api";
import { Card } from "@/components/ui/card";

export function ContentArea() {
  const {
    isPending,
    error,
    data: files,
  } = useQuery({
    queryKey: ["files"],
    queryFn: fetchFiles,
  });

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-4">
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Create
        </Button>
        <Button variant="outline" className="gap-2">
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Upload
        </Button>
        <Button variant="outline" className="gap-2">
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Create folder
        </Button>
        <Button variant="outline" className="gap-2">
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              d="M12 18.5a6.5 6.5 0 100-13 6.5 6.5 0 000 13zM12 14a2 2 0 100-4 2 2 0 000 4z"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Record
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {isPending ? (
          // Loading state
          Array.from({ length: 3 }).map((_, index) => (
            <Card key={index} className="h-[240px] animate-pulse" />
          ))
        ) : error ? (
          // Error state
          <div className="col-span-full text-center">
            <p className="text-destructive">
              Error loading files: {error.message}
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        ) : (
          // Success state - render files
          files?.map((file, index) => (
            <FileCard
              key={index}
              title={file.title}
              metadata={file.metadata}
              thumbnail={file.thumbnail}
            />
          ))
        )}
      </div>
    </div>
  );
}
