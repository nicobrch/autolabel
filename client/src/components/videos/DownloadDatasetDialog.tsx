import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DialogTitle,
  DialogContent,
  DialogClose,
  DialogFooter,
  DialogHeader,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowUpDown, Download } from "lucide-react";
import { formatDate, getFileNameWithoutExtension } from "@/lib/utils";
import { downloadCombinedDataset } from "@/services/api";

interface Video {
  id: string | number;
  file_name: string;
  created_at: string;
  has_inference: boolean;
}

interface DownloadDatasetDialogProps {
  videos: Video[];
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  projectId: string | number;
}

type SortDirection = "asc" | "desc";

export function DownloadDatasetDialog({
  videos,
  setIsOpen,
  projectId,
}: DownloadDatasetDialogProps) {
  const [selectedVideos, setSelectedVideos] = useState<(string | number)[]>([]);
  const [sortColumn, setSortColumn] = useState<"file_name" | "created_at">(
    "file_name",
  );
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [datasetType, setDatasetType] = useState<string>("yolo_detection");
  const [trainValSplit, setTrainValSplit] = useState<number>(0.8);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleToggleAll = () => {
    if (selectedVideos.length === videos.length) {
      setSelectedVideos([]);
    } else {
      setSelectedVideos(videos.map((video) => video.id));
    }
  };

  const handleToggleVideo = (id: string | number) => {
    if (selectedVideos.includes(id)) {
      setSelectedVideos(selectedVideos.filter((videoId) => videoId !== id));
    } else {
      setSelectedVideos([...selectedVideos, id]);
    }
  };

  const handleSort = (column: "file_name" | "created_at") => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const sortedVideos = useMemo(() => {
    return [...videos].sort((a, b) => {
      const valueA = a[sortColumn];
      const valueB = b[sortColumn];

      if (sortColumn === "file_name") {
        const nameA = getFileNameWithoutExtension(
          valueA as string,
        ).toLowerCase();
        const nameB = getFileNameWithoutExtension(
          valueB as string,
        ).toLowerCase();
        return sortDirection === "asc"
          ? nameA.localeCompare(nameB)
          : nameB.localeCompare(nameA);
      } else {
        // For dates
        const dateA = new Date(valueA as string).getTime();
        const dateB = new Date(valueB as string).getTime();
        return sortDirection === "asc" ? dateA - dateB : dateB - dateA;
      }
    });
  }, [videos, sortColumn, sortDirection]);

  const handleDownload = async () => {
    if (selectedVideos.length === 0) return;

    setIsLoading(true);
    try {
      await downloadCombinedDataset({
        projectId,
        videoIds: selectedVideos,
        datasetType,
        trainValSplit,
      });
      setIsOpen(false);
    } catch (error) {
      console.error("Error downloading dataset:", error);
      // You could add a toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DialogContent className="max-w-3xl w-full">
      <DialogHeader>
        <DialogTitle>Download Dataset</DialogTitle>
        <DialogDescription>
          Select videos to include in your dataset download
        </DialogDescription>
      </DialogHeader>

      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">
                <Checkbox
                  checked={
                    selectedVideos.length === videos.length && videos.length > 0
                  }
                  onCheckedChange={handleToggleAll}
                  aria-label="Select all videos"
                />
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleSort("file_name")}
              >
                <div className="flex items-center">
                  Video Name
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </div>
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleSort("created_at")}
              >
                <div className="flex items-center">
                  Date
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </div>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedVideos.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center py-6">
                  No videos with inference available
                </TableCell>
              </TableRow>
            ) : (
              sortedVideos.map((video) => (
                <TableRow key={video.id}>
                  <TableCell>
                    <Checkbox
                      checked={selectedVideos.includes(video.id)}
                      onCheckedChange={() => handleToggleVideo(video.id)}
                      aria-label={`Select ${video.file_name}`}
                    />
                  </TableCell>
                  <TableCell>
                    {getFileNameWithoutExtension(video.file_name)}
                  </TableCell>
                  <TableCell>{formatDate(video.created_at)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex flex-row gap-4 mt-4">
        <div className="flex-1">
          <label className="text-sm font-medium mb-1 block">Dataset Type</label>
          <Select
            value={datasetType}
            onValueChange={(value) => setDatasetType(value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select dataset type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="yolo_detection">YOLO 1.0 Detection</SelectItem>
              <SelectItem value="yolo_segmentation">
                YOLO 1.0 Segmentation
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1">
          <label className="text-sm font-medium mb-1 block">
            Train/Validation Split
          </label>
          <Select
            value={trainValSplit.toString()}
            onValueChange={(value) => setTrainValSplit(parseFloat(value))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select split ratio" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0.9">90-10</SelectItem>
              <SelectItem value="0.8">80-20</SelectItem>
              <SelectItem value="0.7">70-30</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <DialogFooter className="flex justify-end space-x-2 pt-2">
        <DialogClose asChild>
          <Button type="button" variant="outline">
            Cancel
          </Button>
        </DialogClose>
        <Button
          onClick={handleDownload}
          disabled={selectedVideos.length === 0 || isLoading}
          className="gap-2"
        >
          <Download className="h-4 w-4" />
          {isLoading ? "Preparing..." : "Download Selected"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}
