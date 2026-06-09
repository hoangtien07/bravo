"""Deterministic calc sandbox (ADR-0004, PAL/PoT — findings/H). Phase 2.

The LLM emits a numeric EXPRESSION over named inputs; this evaluator computes the result
with a SAFE AST walker — no imports, no attribute access, no calls except a small
whitelist (round/min/max/abs/sum). The final number always comes from here, NEVER from
the LLM's free text. No I/O, no writes.
"""
from __future__ import annotations

import ast
import operator
from collections.abc import Mapping

_BIN = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCS = {"round": round, "min": min, "max": max, "abs": abs, "sum": sum}


class CalcError(ValueError):
    pass


def _eval(node: ast.AST, vars_: Mapping[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body, vars_)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in vars_:
            raise CalcError(f"Biến không xác định: {node.id}")
        return float(vars_[node.id])
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_eval(node.left, vars_), _eval(node.right, vars_))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand, vars_))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        args = [_eval(a, vars_) for a in node.args]
        if node.func.id == "round" and len(args) == 2:  # ndigits must be int
            return float(round(args[0], int(args[1])))
        return float(_FUNCS[node.func.id](*args))
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval(e, vars_) for e in node.elts]  # type: ignore[return-value]
    raise CalcError(f"Biểu thức không được phép: {ast.dump(node)}")


def compute(expression: str, inputs: Mapping[str, float]) -> float:
    """Evaluate an arithmetic `expression` over `inputs`. Deterministic; sandboxed.

    Example: compute("(rev_2023 - rev_2022) / rev_2022 * 100", {"rev_2023":914,"rev_2022":391})
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalcError(f"Cú pháp không hợp lệ: {exc}") from exc
    result = _eval(tree, inputs)
    if not isinstance(result, (int, float)):
        raise CalcError("Kết quả không phải số")
    return float(result)
