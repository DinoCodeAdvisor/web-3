import { useState } from "react";
import HistorySheet from "./components/history-sheet";
import HistoryCard from "./components/history-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import { toast } from "sonner";

function App() {
  const [expression, setExpression] = useState("");
  const [result, setResult] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);

  const handleButtonClick = (value: string) => {
    if (value === "Clear") {
      setExpression("");
      setResult("");
    } else if (value === "Supress") {
      setExpression((prev) => prev.slice(0, -1));
    } else {
      setExpression((prev) => prev + value);
    }
  };

  
  const handleCalculate = () => {
    if (expression.trim()) {
      try {
        // Evaluate the expression safely
        const evalResult = Function(`return (${expression})`)();
        setResult(evalResult.toString());
      } catch {
        setResult("Error");
      }
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
  ];

  return (
    <>
      {/* Main layout */}
      <div className="flex flex-col md:flex-row h-screen p-6 max-w-7xl mx-auto gap-6 items-stretch">
        {/* Sidebar: HistoryCard */}
        <aside className="w-full md:w-80 flex-shrink-0 border rounded-md p-4 shadow-md flex flex-col">
          <h2 className="text-2xl font-semibold text-center mb-4 sticky top-0 z-10 py-2">
            Last Operation Made
          </h2>
          <ScrollArea className="flex-1 h-[calc(100vh-8rem)] scroll-smooth">
            <HistoryCard />
          </ScrollArea>
        </aside>

        {/* Calculator main area */}
        <main className="flex flex-col items-center justify-center gap-4 flex-1 max-w-md mx-auto">
          <h1 className="text-2xl font-semibold text-center w-full">
            RPN Calculator
          </h1>

          <Input
            value={result || expression}
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
    </>
  );
}

export default App;
