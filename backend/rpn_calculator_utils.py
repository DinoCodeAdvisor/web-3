from pydantic import BaseModel
import operator

# Available operations
operations = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

class Expression(BaseModel):
    expression: str

def transform_to_rpn(expression: str) -> list:
    """Transforms an infix expression to Reverse Polish Notation (RPN) using the Shuting Yard algorithm."""
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    output = []
    stack = []

    tokens = expression.replace('(', ' ( ').replace(')', ' ) ').split()
    for token in tokens:
        if token.replace('.', '', 1).isdigit(): # Check if token is a number
            output.append(float(token))
        elif token in precedence:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[token]:
                output.append(stack.pop())
            stack.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop() # Remove '('
    
    while stack:
        output.append(stack.pop())
    
    return output

def evaluate_rpn(rpn_tokens: list, log_function, calculation_id: str) -> float:
    """Evaluates RPN expression and logs each step with the calculation_id."""
    stack = []

    for token in rpn_tokens:
        if isinstance(token, float):
            stack.append(token)
        else:
            if token not in operations:
                raise ValueError(f"Unsupported operatation: {token}")

            b = stack.pop()
            a = stack.pop()

            result = operations[token](a, b)

            log_function(a, b, token, result, calculation_id)
            stack.append(result)

    return stack[0] 

