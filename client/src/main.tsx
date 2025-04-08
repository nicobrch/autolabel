import { BrowserRouter, Routes, Route } from "react-router";
import { createRoot } from "react-dom/client";
import "./index.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
const queryClient = new QueryClient();

import FileManager from "./pages/FileManager";

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<FileManager />} />
      </Routes>
    </BrowserRouter>
  </QueryClientProvider>
);
