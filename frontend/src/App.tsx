import { useEffect, useState } from "react";
import HistorySheet from "./components/history-sheet";
import HistoryCard from "./components/history-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  evaluateExpression,
  fetchLatestCalculation,
} from "../helpers/api";

import type { CalculationHistoryItem } from "../helpers/api";

function App() {
  const [expression, setExpression] = useState("");
  const [result, setResult] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [lastCalculation, setLastCalculation] =
    useState<CalculationHistoryItem | null>(null);

  const handleButtonClick = (value: string) => {
    if (value === "Clear") {
      setExpression("");
      setResult("");
      setShowResult(false);
    } else if (value === "Supress") {
      if (showResult) {
        setResult("");
        setShowResult(false);
        setExpression("");
      } else {
        setExpression((prev) => prev.slice(0, -1));
      }
    } else {
      // Handle operator and parentheses with spaces
      const operatorsAndParentheses = ["+", "-", "*", "/", "(", ")"];

      if (showResult) {
        if (operatorsAndParentheses.includes(value)) {
          // Append space before and after the operator
          setExpression(result + " " + value + " ");
        } else {
          // Start new expression
          setExpression(value);
        }
        setResult("");
        setShowResult(false);
      } else {
        if (operatorsAndParentheses.includes(value)) {
          // Add space before and after operators or parentheses
          setExpression((prev) => prev + " " + value + " ");
        } else {
          setExpression((prev) => prev + value);
        }
      }
    }
  };

  const handleCalculate = async () => {
    if (!expression.trim()) return;

    try {
      await evaluateExpression(expression);
      const latest = await fetchLatestCalculation();
      const latestData = latest.history[0];

      if (latestData) {
        setResult(latestData.result.toString());
        setLastCalculation(latestData);
        setShowResult(true); // Show result in input
      }

      toast.success("Calculation successful!", {
        description: `Result: ${latestData?.result}`,
      });

      setExpression(""); // Clear expression after calculation
    } catch (error) {
      console.error(error);
      let errorMessage = "Please check your input.";

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      toast.error("Calculation failed!", {
        description: errorMessage,
      });
    }

  };

  const buttons = [
    "7",
    "8",
    "9",
    "/",
    "4",
    "5",
    "6",
    "*",
    "1",
    "2",
    "3",
    "-",
    "Clear",
    "0",
    "Supress",
    "+",
    "(",
    ")",
  ];

  useEffect(() => {
    fetchLatestCalculation()
      .then((res) => {
        if (res.history.length > 0) {
          setLastCalculation(res.history[0]);
        }
      })
      .catch((err) => console.error("Failed to fetch latest calculation", err));
  }, [lastCalculation?.calculation_id]);

  return (
    <div className="flex flex-col md:flex-row h-screen p-6 max-w-7xl mx-auto gap-6 items-stretch">
      {/* Sidebar: Last Operation */}
      <aside className="w-full md:w-80 flex-shrink-0 border rounded-md p-4 shadow-md flex flex-col">
        <h2 className="text-2xl font-semibold text-center mb-4 sticky top-0 z-10 py-2">
          Last Operation Made
        </h2>

        <ScrollArea className="flex-1 h-[calc(100vh-8rem)] scroll-smooth">
          {lastCalculation ? (
            <HistoryCard
              calculationId={lastCalculation.calculation_id}
              expression={lastCalculation.expression}
              result={lastCalculation.result}
              date={lastCalculation.date}
            />
          ) : (
            <p className="text-sm text-muted-foreground text-center">
              No recent operation
            </p>
          )}
        </ScrollArea>
      </aside>

      {/* Calculator main area */}
      <main className="flex flex-col items-center justify-center gap-4 flex-1 max-w-md mx-auto">
        <h1 className="text-2xl font-semibold text-center w-full">
          RPN Calculator
        </h1>

        <Input
          value={showResult ? result : expression}
          placeholder="Enter expression"
          readOnly
          className="text-right w-full"
        />

        <div className="grid grid-cols-4 gap-2 w-full">
          {buttons.map((btn) => (
            <Button
              key={btn}
              variant="outline"
              onClick={() => handleButtonClick(btn)}
              className="h-12 hover:bg-gray-100 transition-colors"
            >
              {btn}
            </Button>
          ))}
        </div>

        <Button onClick={handleCalculate} className="w-full mt-2">
          Calculate
        </Button>

        <HistorySheet open={historyOpen} onOpenChange={setHistoryOpen} />

        <Button
          variant="destructive"
          onClick={() => toast.error("There was an error!")}
        >
          Show Alert
        </Button>
      </main>
    </div>
  );
}

export default App;
