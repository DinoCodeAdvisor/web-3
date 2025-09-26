import { useEffect, useState } from "react";
import { fetchHistory, type CalculationHistoryItem } from "@/../helpers/api";
import HistoryCard from "./history-card";
import HistoryHeader from "./history-header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "./ui/button";

interface HistorySheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const HistorySheet = ({ open, onOpenChange }: HistorySheetProps) => {
  const [history, setHistory] = useState<CalculationHistoryItem[]>([]);

  useEffect(() => {
    if (open) {
      fetchHistory()
        .then((data) => setHistory(data))
        .catch((err) => console.error("Failed to load history", err));
    }
  }, [open]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTrigger className="w-full">
        <Button variant={"outline"} className="w-full">
          View History
        </Button>
      </SheetTrigger>
      <SheetContent>
        <HistoryHeader />
        <div className="relative mt-4">
          <ScrollArea className="h-[calc(100vh-8rem)] pr-2 scroll-smooth">
            <div className="px-3 pb-20 grid grid-cols-1 gap-3">
              {history.map((item) => (
                <HistoryCard
                  key={item.calculation_id}
                  calculationId={item.calculation_id}
                  expression={item.expression}
                  result={item.result}
                  date={item.date}
                />
              ))}
            </div>
          </ScrollArea>
          <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-white to-transparent" />
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default HistorySheet;
