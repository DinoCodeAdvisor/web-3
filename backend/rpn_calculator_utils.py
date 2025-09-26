from pydantic import BaseModel
import operator
import re

# Available operations
operations = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

class Expression(BaseModel):
    expression: str

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

def evaluate_rpn(rpn_tokens: list, log_function, calculation_id: str) -> float:
    """Evaluates an RPN expression and logs each operation step."""
    print(f"Received RPN tokens: {rpn_tokens} (type: {type(rpn_tokens)})")

    stack = []

    for token in rpn_tokens:
        if isinstance(token, float):
            stack.append(token)

        elif token in operations:
            if len(stack) < 2:
                raise ValueError("Insufficient operands for the operator.")

            b = stack.pop()
            a = stack.pop()

            if token == '/' and b == 0:
                raise ZeroDivisionError("Division by zero is not allowed.")

            result = operations[token](a, b)

            # Log the operation
            log_function(a, b, token, result, calculation_id)

            stack.append(result)

        else:
            raise ValueError(f"Unknown token in RPN expression: {token}")

    if len(stack) != 1:
        raise ValueError("Invalid RPN expression. Too many operands.")

    return stack[0]
