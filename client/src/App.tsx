import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./components/layout/ThemeProvider";
import { BrowserRouter, Route, Routes } from "react-router";
const queryClient = new QueryClient();

import AppLayout from "./components/layout/AppLayout";
import ProjectManager from "./pages/ProjectManager";
import FrameLabeling from "./pages/FrameLabeling";

export default function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<ProjectManager />} />
              <Route path="/label/" element={<FrameLabeling />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
