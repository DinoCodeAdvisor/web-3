import { useEffect, useState } from "react";
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
import { fetchCalculationDetails, type CalculationStep } from "@/../helpers/api";
import { Skeleton } from "./ui/skeleton";

interface HistoryCardProps {
  calculationId: string;
  expression: string;
  result: number;
  date: string;
}

function formatUtcDate(rawDate: string): string {
  // Match ISO-like strings with >3 millisecond digits and trim to 3
  const cleanedDate = rawDate.replace(/(\.\d{3})\d+/, '$1') + 'Z';
  const parsedDate = new Date(cleanedDate);

  // If invalid, fallback
  if (isNaN(parsedDate.getTime())) {
    return 'Invalid date';
  }

  return parsedDate.toUTCString();
}

const HistoryCard = ({
  calculationId,
  expression,
  result,
  date,
}: HistoryCardProps) => {
  const [expanded, setExpanded] = useState(false);
  const [steps, setSteps] = useState<CalculationStep[]>([]);
  const [hasFetched, setHasFetched] = useState(false);
  const [loading, setLoading] = useState(false);

  const toggleExpand = async () => {
    setExpanded((prev) => !prev);
  };

  useEffect(() => {
    // Only fetch the steps if the card is expanded and not fetched yet
    const fetchSteps = async () => {
      if (expanded && !hasFetched) {
        setLoading(true);
        try {
          const data = await fetchCalculationDetails(calculationId);
          setSteps(data.steps);
          setHasFetched(true);
        } catch (error) {
          console.error("Failed to fetch steps", error);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchSteps();
  }, [expanded, calculationId, hasFetched]);

  useEffect(() => {
    setExpanded(false);
    setHasFetched(false);
    setSteps([]);
  }, [calculationId])


  return (
    <Card
      className={`w-full transition-colors ${
        !expanded ? "hover:bg-accent cursor-pointer" : ""
      }`}
    >
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{expression}</CardTitle>
          <CardDescription>Result: {result}</CardDescription>
        </div>

        <CardAction>
          <Button
            variant="secondary"
            size="icon"
            onClick={(e) => {
              e.stopPropagation();
              toggleExpand();
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
          {loading ? (
            <div className="flex flex-col gap-2">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-6 w-full rounded-md" />
              ))}
            </div>
          ) : steps.length > 0 ? (
            steps.map((step, idx) => (
              <div
                key={idx}
                className="w-full border border-muted rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent"
              >
                <p className="font-medium">
                  {step.a} {step.operator} {step.b} = {step.result}
                </p>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground italic">
              No steps found.
            </p>
          )}
        </CardContent>
      )}

      <CardFooter>
        <p className="text-zinc-500 text-xs">{formatUtcDate(date)}</p>
      </CardFooter>
    </Card>
  );
};

export default HistoryCard;

