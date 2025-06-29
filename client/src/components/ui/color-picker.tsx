import type React from "react";
import { useState, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface ColorPickerProps {
  defaultValue?: string;
  onChange?: (value: string) => void;
  className?: string;
}

interface RGB {
  r: number;
  g: number;
  b: number;
}

interface HSV {
  h: number;
  s: number;
  v: number;
}

// Color presets
export const colorPresets = [
  "#F44336",
  "#E91E63",
  "#9C27B0",
  "#673AB7",
  "#3F51B5",
  "#2196F3",
  "#03A9F4",
  "#00BCD4",
  "#009688",
  "#4CAF50",
  "#8BC34A",
  "#CDDC39",
  "#FFEB3B",
  "#FFC107",
  "#FF9800",
  "#FF5722",
];

export function ColorPicker({
  defaultValue = "#6366F1",
  onChange,
  className,
}: ColorPickerProps) {
  const [color, setColor] = useState(defaultValue);
  const [hsv, setHsv] = useState<HSV>({ h: 0, s: 0, v: 0 });
  const [_, setRgb] = useState<RGB>({ r: 0, g: 0, b: 0 });
  const [open, setOpen] = useState(false);

  const saturationRef = useRef<HTMLDivElement>(null);
  const hueSliderRef = useRef<HTMLDivElement>(null);

  // Convert hex to RGB
  const hexToRgb = (hex: string): RGB => {
    hex = hex.replace(/^#/, "");

    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }

    const r = Number.parseInt(hex.substring(0, 2), 16);
    const g = Number.parseInt(hex.substring(2, 4), 16);
    const b = Number.parseInt(hex.substring(4, 6), 16);

    return { r, g, b };
  };

  // Convert RGB to hex
  const rgbToHex = ({ r, g, b }: RGB): string => {
    return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1).toUpperCase()}`;
  };

  // Convert RGB to HSV
  const rgbToHsv = ({ r, g, b }: RGB): HSV => {
    r /= 255;
    g /= 255;
    b /= 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;

    let h = 0;
    if (delta !== 0) {
      if (max === r) {
        h = ((g - b) / delta) % 6;
      } else if (max === g) {
        h = (b - r) / delta + 2;
      } else {
        h = (r - g) / delta + 4;
      }
    }

    h = Math.round(h * 60);
    if (h < 0) h += 360;

    const s = max === 0 ? 0 : delta / max;
    const v = max;

    return { h, s: s * 100, v: v * 100 };
  };

  // Convert HSV to RGB
  const hsvToRgb = ({ h, s, v }: HSV): RGB => {
    s /= 100;
    v /= 100;

    const c = v * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = v - c;

    let r = 0,
      g = 0,
      b = 0;

    if (h >= 0 && h < 60) {
      r = c;
      g = x;
      b = 0;
    } else if (h >= 60 && h < 120) {
      r = x;
      g = c;
      b = 0;
    } else if (h >= 120 && h < 180) {
      r = 0;
      g = c;
      b = x;
    } else if (h >= 180 && h < 240) {
      r = 0;
      g = x;
      b = c;
    } else if (h >= 240 && h < 300) {
      r = x;
      g = 0;
      b = c;
    } else {
      r = c;
      g = 0;
      b = x;
    }

    return {
      r: Math.round((r + m) * 255),
      g: Math.round((g + m) * 255),
      b: Math.round((b + m) * 255),
    };
  };

  // Validate and format hex color
  const formatHexColor = (value: string): string => {
    // Add # if missing
    if (value.charAt(0) !== "#") {
      value = "#" + value;
    }

    // Validate hex format
    const isValidHex = /^#([A-Fa-f0-9]{3}){1,2}$/.test(value);
    return isValidHex ? value.toUpperCase() : color;
  };

  // Update all color states
  const updateColor = (newColor: string) => {
    const formattedColor = formatHexColor(newColor);
    setColor(formattedColor);

    const newRgb = hexToRgb(formattedColor);
    setRgb(newRgb);

    const newHsv = rgbToHsv(newRgb);
    setHsv(newHsv);

    onChange?.(formattedColor);
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    updateColor(e.target.value);
  };

  // Handle hue change
  const handleHueChange = (
    e: React.MouseEvent<HTMLDivElement> | React.TouchEvent<HTMLDivElement>,
  ) => {
    if (!hueSliderRef.current) return;

    const rect = hueSliderRef.current.getBoundingClientRect();

    // Get coordinates (handle both mouse and touch events)
    let clientX;
    if ("touches" in e) {
      clientX = e.touches[0].clientX;
    } else {
      clientX = e.clientX;
    }

    // Calculate hue based on position
    let h = ((clientX - rect.left) / rect.width) * 360;

    // Clamp values
    h = Math.max(0, Math.min(360, h));

    const newHsv = { ...hsv, h };
    setHsv(newHsv);

    const newRgb = hsvToRgb(newHsv);
    setRgb(newRgb);

    const newColor = rgbToHex(newRgb);
    setColor(newColor);
    onChange?.(newColor);
  };

  // Handle saturation/value change
  const handleSaturationValueChange = (
    e: React.MouseEvent<HTMLDivElement> | React.TouchEvent<HTMLDivElement>,
  ) => {
    if (!saturationRef.current) return;

    const rect = saturationRef.current.getBoundingClientRect();

    // Get coordinates (handle both mouse and touch events)
    let clientX, clientY;
    if ("touches" in e) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }

    // Calculate saturation and value based on position
    let s = ((clientX - rect.left) / rect.width) * 100;
    let v = 100 - ((clientY - rect.top) / rect.height) * 100;

    // Clamp values
    s = Math.max(0, Math.min(100, s));
    v = Math.max(0, Math.min(100, v));

    const newHsv = { ...hsv, s, v };
    setHsv(newHsv);

    const newRgb = hsvToRgb(newHsv);
    setRgb(newRgb);

    const newColor = rgbToHex(newRgb);
    setColor(newColor);
    onChange?.(newColor);
  };

  // Handle preset selection
  const handlePresetClick = (presetColor: string) => {
    updateColor(presetColor);
  };

  // Initialize color values on mount or when defaultValue changes
  useEffect(() => {
    updateColor(defaultValue);
  }, [defaultValue]);

  // Mouse/touch event handlers for saturation-value picker
  const handleMouseDown = (
    e: React.MouseEvent<HTMLDivElement>,
    handler: typeof handleSaturationValueChange | typeof handleHueChange,
  ) => {
    handler(e);

    const handleMouseMove = (e: MouseEvent) => {
      handler(e as unknown as React.MouseEvent<HTMLDivElement>);
    };

    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const handleTouchStart = (
    e: React.TouchEvent<HTMLDivElement>,
    handler: typeof handleSaturationValueChange | typeof handleHueChange,
  ) => {
    handler(e);

    const handleTouchMove = (e: TouchEvent) => {
      handler(e as unknown as React.TouchEvent<HTMLDivElement>);
    };

    const handleTouchEnd = () => {
      document.removeEventListener("touchmove", handleTouchMove);
      document.removeEventListener("touchend", handleTouchEnd);
    };

    document.addEventListener("touchmove", handleTouchMove);
    document.addEventListener("touchend", handleTouchEnd);
  };

  return (
    <div className={cn("relative", className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <div className="flex items-center gap-2 cursor-pointer">
            <Input
              type="text"
              value={color}
              onChange={handleInputChange}
              className="pr-10"
              maxLength={7}
              aria-label="Color hex value"
            />
            <div
              className="absolute right-2 top-1/2 -translate-y-1/2 size-6 rounded-md cursor-pointer border border-border"
              style={{ backgroundColor: color }}
              aria-label="Color preview"
              role="button"
              tabIndex={0}
            />
          </div>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-3" sideOffset={5}>
          <div className="space-y-4">
            {/* Saturation-Value picker */}
            <div
              ref={saturationRef}
              className="relative h-36 rounded-md cursor-crosshair"
              style={{
                backgroundColor: `hsl(${hsv.h}, 100%, 50%)`,
                backgroundImage:
                  "linear-gradient(to top, #000, transparent), linear-gradient(to right, #fff, transparent)",
              }}
              onMouseDown={(e) =>
                handleMouseDown(e, handleSaturationValueChange)
              }
              onTouchStart={(e) =>
                handleTouchStart(e, handleSaturationValueChange)
              }
            >
              <div
                className="absolute size-4 rounded-full transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                style={{
                  left: `${hsv.s}%`,
                  top: `${100 - hsv.v}%`,
                  boxShadow:
                    "0 0 0 2px white, 0 0 0 3px rgba(0,0,0,0.3), 0 0 2px 4px rgba(0,0,0,0.2)",
                }}
              />
            </div>

            {/* Hue slider - now with transparent track */}
            <div
              ref={hueSliderRef}
              className="relative h-5 rounded-md cursor-pointer"
              style={{
                background:
                  "linear-gradient(to right, #f00, #ff0, #0f0, #0ff, #00f, #f0f, #f00)",
              }}
              onMouseDown={(e) => handleMouseDown(e, handleHueChange)}
              onTouchStart={(e) => handleTouchStart(e, handleHueChange)}
            >
              <div
                className="absolute top-1/2 size-4 rounded-full bg-white transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                style={{
                  left: `${(hsv.h / 360) * 100}%`,
                  boxShadow: "0 0 4px 1px rgba(0,0,0,0.4)",
                }}
              />
            </div>

            {/* HEX input */}
            <div className="pt-1">
              <Input
                value={color}
                onChange={handleInputChange}
                maxLength={7}
                className="font-mono"
                aria-label="HEX color value"
              />
            </div>

            {/* Color presets */}
            <div className="grid grid-cols-8 gap-1 pt-1">
              {colorPresets.map((presetColor) => (
                <button
                  key={presetColor}
                  className="size-5 rounded-md cursor-pointer transition-transform hover:scale-110 focus:scale-110 focus:outline-none"
                  style={{ backgroundColor: presetColor }}
                  onClick={() => handlePresetClick(presetColor)}
                  aria-label={`Color preset: ${presetColor}`}
                />
              ))}
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
