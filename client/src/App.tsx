import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/layout/ThemeProvider";
import { BrowserRouter, Route, Routes } from "react-router";
const queryClient = new QueryClient();

import AppLayout from "./components/layout/AppLayout";
import ProjectManager from "./pages/ProjectManager";
import VideoLabeling from "./pages/VideoLabeling";
import VideoLabeledPreview from "./pages/VideoLabeledPreview";
import VideoManager from "./pages/VideoManager";

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<ProjectManager />} />
              <Route path="/projects/:projectId" element={<VideoManager />} />
              <Route path="/label/:videoId" element={<VideoLabeling />} />
              <Route
                path="/results/:videoId"
                element={<VideoLabeledPreview />}
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
