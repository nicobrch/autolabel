import { BrowserRouter, Routes, Route } from "react-router";
import { createRoot } from "react-dom/client";
import "./index.css";

import FileManager from "./pages/FileManager";

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<FileManager />} />
    </Routes>
  </BrowserRouter>
);
