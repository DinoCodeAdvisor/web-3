import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import HistoryCard from "./history-card";
import HistoryHeader from "./history-header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "./ui/button";

interface HistorySheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const HistorySheet = ({ open, onOpenChange }: HistorySheetProps) => {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTrigger className="w-full">
        <Button variant={'outline'} className="w-full">View History</Button>
      </SheetTrigger>
      <SheetContent>
        <HistoryHeader />
        <div className="relative mt-4">
          <ScrollArea className="h-[calc(100vh-8rem)] pr-2 scroll-smooth">
            <div className="px-3 pb-20 grid grid-cols-1 gap-3">
              <HistoryCard />
              <HistoryCard />
              <HistoryCard />
              <HistoryCard />
              <HistoryCard />
              <HistoryCard />
            </div>
          </ScrollArea>

          {/* Bottom fade overlay */}
          <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-white to-transparent" />
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default HistorySheet;
