const API_BASE_URL = "http://localhost:8089/calculator";

// ----------------------------------
// Types
// ----------------------------------

export interface CalculationStep {
  a: number;
  b: number;
  operator: string;
  result: number;
  date: string;
}

export interface CalculationDetailsResponse {
  calculation_id: string;
  steps: CalculationStep[];
}

export interface CalculationHistoryItem {
  calculation_id: string;
  expression: string;
  result: number;
  date: string;
}

export interface HistoryResponse {
  history: CalculationHistoryItem[];
}

export interface EvaluateExpressionResponse {
  calculation_id: string;
  expression: string;
  result: number;
}

export interface LatestCalculationResponse {
  history: {
    calculation_id: string;
    expression: string;
    result: number;
    date: string;
  }[];
  steps: {
    a: number;
    b: number;
    operator: string;
    result: number;
    date: string;
  }[];
}

// ----------------------------------
// API Functions
// ----------------------------------

export const evaluateExpression = async (
  expression: string
): Promise<EvaluateExpressionResponse> => {
  const response = await fetch(`${API_BASE_URL}/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ expression }),
  });

  if (!response.ok) {
    // Try to parse error message from API
    let errorMessage = "Failed to evaluate expression";
    try {
      const errorData = await response.json();
      if (errorData.detail) errorMessage = errorData.detail;
    } catch {
      // JSON parse failed, fallback to default message
    }
    throw new Error(errorMessage);
  }

  return response.json();
};


export const fetchHistory = async (
  operationTypes: string[] = [],
  startDate: Date | null = null,
  endDate: Date | null = null,
  sortBy: string = "date",
  sortOrder: string = "desc"
): Promise<CalculationHistoryItem[]> => {
  // Create query parameters
  const params: Record<string, string> = {};

  if (operationTypes.length > 0) {
    params.operation_types = operationTypes.join(",");
  }

  if (startDate) {
    params.start_date = startDate.toISOString();
  }

  if (endDate) {
    params.end_date = endDate.toISOString();
  }

  if (sortBy) {
    params.sort_by = sortBy;
  }

  if (sortOrder) {
    params.sort_order = sortOrder;
  }

  // Construct query string
  const queryString = new URLSearchParams(params).toString();

  const response = await fetch(`${API_BASE_URL}/history?${queryString}`);
  if (!response.ok) throw new Error("Failed to fetch history");

  const data: HistoryResponse = await response.json();
  return data.history;
};

export const fetchCalculationDetails = async (
  id: string
): Promise<CalculationDetailsResponse> => {
  const res = await fetch(`${API_BASE_URL}/history/${id}/details`);
  if (!res.ok) throw new Error("Failed to fetch details");

  return res.json();
};

export const fetchLatestCalculation =
  async (): Promise<LatestCalculationResponse> => {
    const response = await fetch(`${API_BASE_URL}/history/latest`);
    if (!response.ok) throw new Error("Failed to fetch latest calculation");
    return response.json();
};