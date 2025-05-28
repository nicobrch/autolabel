import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ModelState {
  modelCheckpoint: string;
  setModelCheckpoint: (checkpoint: string) => void;
}

export const useModelStore = create<ModelState>()(
  persist(
    (set) => ({
      modelCheckpoint: "tiny", // Default value
      setModelCheckpoint: (checkpoint: string) =>
        set({ modelCheckpoint: checkpoint }),
    }),
    {
      name: "model-checkpoint-storage", // localStorage key
    },
  ),
);
