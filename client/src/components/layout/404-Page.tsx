import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Home, ArrowLeft, Search } from "lucide-react";
import { useNavigate } from "react-router";
import {
  TypographyH1,
  TypographyH3,
  TypographyP,
  TypographySmall,
} from "../typography/typography";

export default function NotFoundPage() {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate("/");
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8 text-center space-y-6">
          {/* 404 Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <Search className="w-16 h-16" />
              <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center">
                <span className="text-xs font-bold">!</span>
              </div>
            </div>
          </div>

          {/* Error Message */}
          <div className="space-y-2">
            <TypographyH1>404</TypographyH1>
            <TypographyH3>Page Not Found</TypographyH3>
            <TypographyP>
              The page you're looking for doesn't exist or has been moved.
            </TypographyP>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 pt-4">
            <Button onClick={handleGoHome} className="w-full">
              <Home className="w-4 h-4 mr-2" />
              Go to Dashboard
            </Button>

            <Button onClick={handleGoBack} variant="outline" className="w-full">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          </div>

          {/* AutoLabel Branding */}
          <div className="pt-4 border-t">
            <TypographySmall>AutoLabel Project</TypographySmall>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
