from pydantic import BaseModel
import operator
import re
import httpx
import asyncio

# Available operations
operations = {
    '+': "http://calculadora:8000/calculator/add",
    '-': "http://calculadora:8000/calculator/subtract",
    '*': "http://calculadora:8000/calculator/multiply",
    '/': "http://calculadora:8000/calculator/divide"
}

class Expression(BaseModel):
    expression: str

async def call_operator_api(op: str, a: float, b: float) -> float:
    """
    Calls the real microservice normally.
    But when running tests (TESTING=1), bypasses HTTP and
    executes the arithmetic locally.
    """
    import os

    # --- Test mode: No HTTP calls ---
    if os.getenv("TESTING") == "1":
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            return a / b
        raise ValueError(f"Unsupported operator: {op}")

    # --- Normal mode: microservice calls ---
    url = operations.get(op)
    if not url:
        raise ValueError(f"Unsupported operator: {op}")

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"a": a, "b": b})
        response.raise_for_status()
        return response.json()["result"]

def preprocess_negatives(expr: str) -> str:
    """
    Converts unary negatives into '(0 - number)' so the RPN parser handles them correctly.
    For example:
        -3 → (0-3)
        5 * -2 → 5*(0-2)
        -1 / -1 → (0-1)/(0-1)
    """
    expr = expr.replace(' ', '')  # Normalize whitespace

    # Case 1: Unary negative at the start of the expression
    expr = re.sub(r'^-(\d+(\.\d+)?)', r'(0-\1)', expr)

    # Case 2: Unary negative after operator or opening parenthesis
    expr = re.sub(r'([\+\-\*/\(])-(\d+(\.\d+)?)', r'\1(0-\2)', expr)

    return expr

def transform_to_rpn(expression: str) -> list:
    """Transforms an infix expression to RPN using the Shunting Yard algorithm."""
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    output = []
    stack = []

    # Preprocess expression to handle unary negatives
    expression = preprocess_negatives(expression)

    # Tokenize numbers, operators, and parentheses
    tokens = re.findall(r'\d+\.\d+|\d+|[+\-*/()]', expression)

    for token in tokens:
        # Number
        if re.fullmatch(r'\d+(\.\d+)?', token):
            output.append(float(token))

        # Operator
        elif token in precedence:
            while (stack and stack[-1] in precedence and
                   precedence[stack[-1]] >= precedence[token]):
                output.append(stack.pop())
            stack.append(token)

        # Left parenthesis
        elif token == '(':
            stack.append(token)

        # Right parenthesis
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()  # Remove '('

        else:
            raise ValueError(f"Invalid token: {token}")

    # Pop any remaining operators
    while stack:
        if stack[-1] in '()':
            raise ValueError("Mismatched parentheses")
        output.append(stack.pop())

    return output

async def evaluate_rpn_async(rpn_tokens: list, log_function, calculation_id: str) -> float:
    """Evaluates an RPN expression and logs each operation step."""

    stack = []

    for token in rpn_tokens:
        if isinstance(token, float):
            stack.append(token)
        elif token in operations:
            if len(stack) < 2:
                raise ValueError("Insufficient operands for the operator.")

            b = stack.pop()
            a = stack.pop()

            result = await call_operator_api(token, a, b)

            log_function(a, b, token, result, calculation_id)

            stack.append(result)
        else:
            raise ValueError(f"Unknown token: {token}")

    if len(stack) != 1:
        raise ValueError("Invalid RPN expression.")

    return stack[0]
