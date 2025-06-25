import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { TypographyH4 } from "../typography/typography";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ModeToggle } from "./ThemeToggle";
import { NavLink, useLocation, useParams } from "react-router";
import { useEffect, useState } from "react";
import { fetchProjectById, fetchVideoById } from "@/services/api"; // Import video fetching function

export function Navbar() {
  const location = useLocation();
  const pathname = location.pathname;
  const { projectId, videoId } = useParams(); // Get both projectId and videoId
  const [projectName, setProjectName] = useState<string | null>(null);
  const [videoName, setVideoName] = useState<string | null>(null); // New state for video name
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const pathnameMap: { [key: string]: string } = {
    "/projects": "Project Manager",
    "/label": "Video Labeling",
    "/results": "Label Results",
    "/": "Dashboard",
  };

  useEffect(() => {
    // Reset names when not on a project route
    if (!pathname.includes("/projects/")) {
      setProjectName(null);
      setVideoName(null);
      return;
    }

    setIsLoading(true);

    // Determine if we need to fetch video details
    const isVideoRoute =
      pathname.includes("/label/") || pathname.includes("/download/");

    // Promise array to store all fetch operations
    const fetchPromises = [];

    // Always fetch project if we have projectId
    if (projectId) {
      const projectPromise = fetchProjectById(projectId)
        .then((project) => {
          setProjectName(project.name);
        })
        .catch((error) => {
          console.error("Failed to fetch project name:", error);
          setProjectName(projectId);
        });

      fetchPromises.push(projectPromise);
    }

    // Fetch video if we're on a video route and have videoId
    if (isVideoRoute && videoId) {
      const videoPromise = fetchVideoById(videoId)
        .then((video) => {
          setVideoName(video.file_name);
        })
        .catch((error) => {
          console.error("Failed to fetch video details:", error);
          setVideoName(videoId);
        });

      fetchPromises.push(videoPromise);
    } else {
      // Reset video name if not on a video route
      setVideoName(null);
    }

    // Wait for all promises to complete
    Promise.all(fetchPromises).finally(() => {
      setIsLoading(false);
    });
  }, [pathname, projectId, videoId]);

  let title = "Dashboard"; // Default title

  // Determine title based on route and available data
  if (pathname.includes("/projects/")) {
    if (isLoading) {
      title = "Loading...";
    } else if (pathname.includes("/label/") && videoName) {
      // Use video name for label routes
      title = `Labeling Video ${videoName}`;
    } else if (pathname.includes("/download/") && videoName) {
      // Use video name for download routes
      title = `Label Results for ${videoName}`;
    } else if (projectName) {
      // Fall back to project name for other project routes
      title = `${projectName} Project Videos`;
    } else {
      title = "Project";
    }
  } else {
    // Fall back to the static mapping for non-project routes
    for (const key in pathnameMap) {
      if (pathname.startsWith(key) && (key !== "/" || pathname === "/")) {
        title = pathnameMap[key];
        break;
      }
    }
  }

  return (
    <nav className="flex items-center justify-between p-4 h-16 border-b">
      <div className="flex items-center space-x-4">
        <SidebarTrigger />
        <TypographyH4>{title}</TypographyH4>
      </div>
      <div className="flex items-center space-x-4">
        <ModeToggle />
        <NavLink to="https://github.com/nicobrch">
          <Avatar>
            <AvatarImage src="nicopfp.png" alt="@nicobrch" />
            <AvatarFallback>NC</AvatarFallback>
          </Avatar>
        </NavLink>
      </div>
    </nav>
  );
}
