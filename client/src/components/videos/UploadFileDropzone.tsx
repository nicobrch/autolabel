import { Button } from "@/components/ui/button";
import {
  FileUpload,
  FileUploadDropzone,
  FileUploadItem,
  FileUploadItemDelete,
  FileUploadItemMetadata,
  FileUploadItemPreview,
  FileUploadList,
  FileUploadTrigger,
} from "@/components/ui/file-upload";
import { Upload, X } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

export function UploadFileDropzone({
  files,
  setFiles,
}: {
  files: File[];
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
}) {
  const onFileReject = React.useCallback((file: File, message: string) => {
    toast(message, {
      description: `"${
        file.name.length > 100 ? `${file.name.slice(0, 100)}...` : file.name
      }" has been rejected`,
    });
  }, []);

  return (
    <FileUpload
      maxFiles={1}
      maxSize={25 * 1024 * 1024}
      accept=".mp4"
      className="w-full max-w-md"
      value={files}
      onValueChange={setFiles}
      onFileReject={onFileReject}
    >
      <div
        className={`transition-all duration-500 ease-in-out overflow-hidden ${
          files.length > 0 ? "max-h-0 opacity-0" : "max-h-96 opacity-100"
        }`}
      >
        <FileUploadDropzone>
          <div className="flex flex-col items-center gap-1 text-center">
            <div className="flex items-center justify-center rounded-full border p-2.5">
              <Upload className="size-6 text-muted-foreground" />
            </div>
            <p className="font-medium text-sm">Drag & drop a video file here</p>
            <p className="text-muted-foreground text-xs">
              Or click to browse (only .mp4 files are allowed)
            </p>
          </div>
          <FileUploadTrigger asChild>
            <Button variant="outline" size="sm" className="mt-2 w-fit">
              Browse files
            </Button>
          </FileUploadTrigger>
        </FileUploadDropzone>
      </div>
      <FileUploadList>
        {files.map((file, index) => (
          <FileUploadItem key={index} value={file}>
            <FileUploadItemPreview />
            <FileUploadItemMetadata />
            <FileUploadItemDelete asChild>
              <Button variant="ghost" size="icon" className="size-7">
                <X />
              </Button>
            </FileUploadItemDelete>
          </FileUploadItem>
        ))}
      </FileUploadList>
    </FileUpload>
  );
}
