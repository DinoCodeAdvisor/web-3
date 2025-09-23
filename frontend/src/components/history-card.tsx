import { useState } from "react";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronRight } from "lucide-react";

const HistoryCard = () => {
  const [expanded, setExpanded] = useState(false);

  const operations = [
    { id: 1, operation: "4 + 3", result: 7 },
    { id: 2, operation: "7 + 2", result: 9 },
    { id: 3, operation: "9 + 1", result: 10 },
  ];

  return (
    <Card
      className={`w-full transition-colors ${
        !expanded ? "hover:bg-accent cursor-pointer" : ""
      }`}
    >
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>4 + 3 + 2 + 1</CardTitle>
          <CardDescription>
            Total operations: {operations.length}
          </CardDescription>
        </div>

        <CardAction>
          <Button
            variant="secondary"
            size="icon"
            onClick={(e) => {
              e.stopPropagation(); // prevent triggering card-level hover
              setExpanded((prev) => !prev);
            }}
            className="transition-transform"
          >
            <ChevronRight
              className={`h-4 w-4 transform transition-transform ${
                expanded ? "rotate-90" : ""
              }`}
            />
          </Button>
        </CardAction>
      </CardHeader>

      {expanded && (
        <CardContent className="flex flex-col gap-2">
          {operations.map((op) => (
            <div
              key={op.id}
              className="w-full border border-muted rounded-md px-3 py-2 text-sm text-muted-foreground"
            >
              <p className="font-medium">
                {op.operation} = {op.result}
              </p>
            </div>
          ))}
        </CardContent>
      )}

      <CardFooter>
        <p className="text-zinc-500 text-xs">2025-09-22 16:32:19 UTC</p>
      </CardFooter>
    </Card>
  );
};

export default HistoryCard;
