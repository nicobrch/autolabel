import { Button } from "@/components/ui/button";
import { Brain } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { TypographyH4 } from "../typography/typography";

interface ActionButtonsProps {
  onLabelVideo: () => void; // Placeholder for future functionality
}

export function ActionButtons({ onLabelVideo }: ActionButtonsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <TypographyH4>Make Inference</TypographyH4>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button className="w-full" onClick={onLabelVideo}>
          <Brain className="h-4 w-4 mr-2" />
          Label Video
        </Button>
      </CardContent>
    </Card>
  );
}
