import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/layout/ThemeProvider";
import { BrowserRouter, Route, Routes } from "react-router";
const queryClient = new QueryClient();

import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import VideoLabeling from "./pages/VideoLabeling";
import VideoLabeledPreview from "./pages/VideoLabeledPreview";
import ProjectManager from "./pages/ProjectManager";

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="/projects/:projectId" element={<ProjectManager />} />
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
