import { useEffect, useState } from "react";
import { fetchHistory, type CalculationHistoryItem } from "@/../helpers/api";
import HistoryCard from "./history-card";
import HistoryHeader from "./history-header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "./ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectLabel,
  SelectValue,
} from "@/components/ui/select";
import { CalendarIcon } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { format } from "date-fns";
import { SelectGroup } from "@radix-ui/react-select";

interface HistorySheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const HistorySheet = ({ open, onOpenChange }: HistorySheetProps) => {
  const [history, setHistory] = useState<CalculationHistoryItem[]>([]);
  const [operationTypes, setOperationTypes] = useState<string[]>(['none']); // Ensure this is an array
  const [startDate, setStartDate] = useState<Date | null>(null); // Start date for date range
  const [endDate, setEndDate] = useState<Date | null>(null); // End date for date range
  const [sortBy, setSortBy] = useState("asc"); // Ascending/Descending order for sorting
  const [sortCriteria, setSortCriteria] = useState("date"); // Sort by date or result

  // Fetch history when sheet is opened or when filters change
  useEffect(() => {
    if (open) {
      // Ensure that operationTypes is an array
      const filteredOperationTypes = Array.isArray(operationTypes)
        ? operationTypes
        : [];

      fetchHistory(
        filteredOperationTypes,
        startDate,
        endDate,
        sortCriteria,
        sortBy
      )
        .then((data) => setHistory(data))
        .catch((err) => console.error("Failed to load history", err));
    }
  }, [open, operationTypes, startDate, endDate, sortBy, sortCriteria]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTrigger className="w-full">
        <Button variant={"outline"} className="w-full">
          View History
        </Button>
      </SheetTrigger>
      <SheetContent>
        <HistoryHeader />
        <div className="flex px-4 gap-2 flex-wrap space-evenly w-full">
          {/* Operation Types (Multiple Select) */}
          <Select
            value={operationTypes}
            onValueChange={
              (newValue) =>
                setOperationTypes(
                  Array.isArray(newValue) ? newValue : [newValue]
                ) // Ensure it's an array
            }
            multiple
          >
            <SelectTrigger className="w-48">
              {/* Map selected values to their labels */}
              <SelectValue placeholder="Select Operations">
                {operationTypes.length === 0
                  ? "Select Operations"
                  : operationTypes
                      .map((value) => {
                        switch (value) {
                          case "none":
                            return "None";
                          case "sum":
                            return "Addition (+)";
                          case "sub":
                            return "Subtraction (-)";
                          case "mul":
                            return "Multiplication (*)";
                          case "div":
                            return "Division (/)";
                          default:
                            return value; // In case a custom value is used
                        }
                      })
                      .join(", ")}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Select Operation</SelectLabel>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="sum">Addition (+)</SelectItem>
                <SelectItem value="sub">Subtraction (-)</SelectItem>
                <SelectItem value="mul">Multiplication (*)</SelectItem>
                <SelectItem value="div">Division (/)</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>

          {/* Date Range Picker */}
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-48 justify-start text-left font-normal"
              >
                <CalendarIcon />
                {startDate && endDate
                  ? `${format(startDate, "PPP")} - ${format(endDate, "PPP")}`
                  : "Pick Date Range"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                selected={startDate}
                onSelect={setStartDate}
                mode="single"
                className="p-4"
              />
              <Calendar
                selected={endDate}
                onSelect={setEndDate}
                mode="single"
                className="p-4 mt-4"
              />
            </PopoverContent>
          </Popover>

          {/* Sort By */}
          <Select
            value={sortCriteria}
            onValueChange={setSortCriteria}
            className="w-48"
          >
            <SelectTrigger>
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="date">Date</SelectItem>
              <SelectItem value="result">Result</SelectItem>
            </SelectContent>
          </Select>

          {/* Sort Direction */}
          <Select value={sortBy} onValueChange={setSortBy} className="w-48">
            <SelectTrigger>
              <SelectValue placeholder="Order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Ascending</SelectItem>
              <SelectItem value="desc">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>

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
