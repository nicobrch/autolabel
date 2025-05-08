interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  showText?: boolean;
  text?: string;
}

export default function LoadingSpinner({
  size = "medium",
  showText = true,
  text = "Loading content...",
}: LoadingSpinnerProps) {
  // Determine size in pixels
  const sizeMap = {
    small: {
      container: "w-6 h-6",
      border: "border-2",
    },
    medium: {
      container: "w-10 h-10",
      border: "border-3",
    },
    large: {
      container: "w-14 h-14",
      border: "border-4",
    },
  };

  const { container, border } = sizeMap[size];

  return (
    <div className="flex flex-col items-center justify-center">
      <div className={`${container} relative`}>
        <div
          className={`absolute inset-0 rounded-full ${border} border-gray-700 border-t-orange-500 animate-spin`}
          style={{ animationDuration: "0.8s" }}
        ></div>
      </div>
      {showText && <p className="mt-3 text-sm text-gray-300">{text}</p>}
    </div>
  );
}
