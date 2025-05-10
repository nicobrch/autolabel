import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/layout/ThemeProvider";
import {
  BrowserRouter,
  Route,
  Routes,
  Navigate,
  useParams,
} from "react-router"; // Added Navigate, useParams
const queryClient = new QueryClient();

import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import VideoLabeling from "./pages/VideoLabeling";
import VideoLabeledPreview from "./pages/VideoLabeledPreview";
import ProjectManager from "./pages/ProjectManager";

// Helper component for redirecting from /projects/:projectId/label
function ProjectLabelRedirect() {
  const { projectId } = useParams();
  return <Navigate to={`/projects/${projectId}`} replace />;
}

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="/projects" element={<Navigate to="/" replace />} />
              <Route path="/projects/:projectId" element={<ProjectManager />} />
              <Route
                path="/projects/:projectId/label"
                element={<ProjectLabelRedirect />}
              />
              <Route
                path="/projects/:projectId/label/:videoId"
                element={<VideoLabeling />}
              />
              <Route
                path="/projects/:projectId/download"
                element={<ProjectLabelRedirect />}
              />
              <Route
                path="/projects/:projectId/download/:videoId"
                element={<VideoLabeledPreview />}
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
