from .ast_nodes import *
import os, json, subprocess, sys, re as _re, time as _time, importlib as _importlib
import math as _math, random as _random, datetime as _datetime
import ast as _ast

try:
    import tkinter as tk
except ImportError:
    pass

try:
    import requests as _requests
    _REQ = True
except ImportError:
    _REQ = False

def _safe_range(*args):
    return range(*[int(float(a)) if isinstance(a, str) else int(a) for a in args])

_SAFE_FUNCS = {
    "len": len,
    "int": int,
    "float": float,
    "str": str,
    "round": round,
    "abs": abs,
    "min": min,
    "max": max,
    "range": _safe_range,
}
_SAFE_CONSTANTS = {"pi": _math.pi, "e": _math.e}
if hasattr(_math, "tau"):
    _SAFE_CONSTANTS["tau"] = _math.tau

_MISSING = object()


class FunctionRef:
    def __init__(self, interpreter, name):
        self.interpreter = interpreter
        self.name = name


class ModuleNamespace:
    def __init__(self, name, interpreter, export_names):
        self.name = name
        self.interpreter = interpreter
        self.export_names = set(export_names)

    def resolve(self, name):
        if name not in self.export_names:
            return _MISSING
        if name in self.interpreter.functions:
            return FunctionRef(self.interpreter, name)
        if name in self.interpreter.variables:
            return self.interpreter.variables[name]
        return _MISSING

    def set(self, name, value):
        self.interpreter.variables[name] = value
        return value



class Interpreter:

    def __init__(self, base_dir=None, module_cache=None):
        self.variables       = {}
        self.functions       = {}
        self.classes         = {}
        self.tables          = {}
        self.db              = {}
        self.db_file         = None
        self._pending_prompt = None
        self._socket         = None
        self._log_file       = "app.log"
        self.base_dir        = base_dir or os.getcwd()
        self.module_cache    = module_cache if module_cache is not None else {}
        self._exported_names = set()
        self._module_name    = None
        self._ast_cache      = {}
        self._models         = {}
        self._networks       = {}
        self._llms           = {}

    def _normalize_expr(self, expr):
        expr = str(expr)
        replacements = [
            (" divided by ", " / "),
            (" plus ", " + "),
            (" minus ", " - "),
            (" times ", " * "),
            (" mod ", " % "),
            (" power ", " ** "),
        ]
        for src, dst in replacements:
            expr = expr.replace(src, dst)
        expr = _re.sub(r'\btrue\b', "True", expr, flags=_re.IGNORECASE)
        expr = _re.sub(r'\bfalse\b', "False", expr, flags=_re.IGNORECASE)
        expr = _re.sub(r'\byes\b', "True", expr, flags=_re.IGNORECASE)
        expr = _re.sub(r'\bno\b', "False", expr, flags=_re.IGNORECASE)
        expr = _re.sub(r'\bnull\b', "None", expr, flags=_re.IGNORECASE)
        return expr

    def _normalize_condition(self, cond_text):
        cond = self._normalize_expr(cond_text)
        replacements = [
            (" is greater than or equal to ", " >= "),
            (" is less than or equal to ", " <= "),
            (" is greater or equal ", " >= "),
            (" is less or equal ", " <= "),
            (" is not equal to ", " != "),
            (" not equals ", " != "),
            (" is equal to ", " == "),
            (" equals ", " == "),
            (" greater than or equal to ", " >= "),
            (" greater or equal ", " >= "),
            (" less than or equal to ", " <= "),
            (" less or equal ", " <= "),
            (" is greater than ", " > "),
            (" greater than ", " > "),
            (" is less than ", " < "),
            (" less than ", " < "),
        ]
        for src, dst in replacements:
            cond = cond.replace(src, dst)
        return cond

    def _resolve_name(self, name, local_vars):
        if name in local_vars:
            return local_vars[name]
        if name in self.variables:
            return self.variables[name]
        key = name.lower()
        if key in ("true", "yes"): return True
        if key in ("false", "no"): return False
        if key in ("none", "null"): return None
        if key in _SAFE_CONSTANTS: return _SAFE_CONSTANTS[key]
        raise NameError(name)

    def _resolve_dotted_container(self, token, scope):
        parts = token.split(".")
        if len(parts) < 2: return None, None
        obj = scope.get(parts[0], self.variables.get(parts[0]))
        for part in parts[1:-1]:
            if isinstance(obj, dict): obj = obj.get(part)
            elif isinstance(obj, ModuleNamespace):
                obj = obj.resolve(part)
                if obj is _MISSING: return None, None
            elif hasattr(obj, part): obj = getattr(obj, part)
            else: return None, None
        return obj, parts[-1]

    def _resolve_dotted_value(self, token, scope):
        parts = token.split(".")
        if len(parts) < 2: return _MISSING
        obj = scope.get(parts[0], self.variables.get(parts[0]))
        for part in parts[1:]:
            if isinstance(obj, dict):
                if part not in obj: return f"[homo] '{parts[0]}' has no attribute '{part}'"
                obj = obj.get(part)
            elif isinstance(obj, ModuleNamespace):
                obj = obj.resolve(part)
                if obj is _MISSING: return f"[homo] '{parts[0]}' has no attribute '{part}'"
            elif hasattr(obj, part): obj = getattr(obj, part)
            else: return f"[homo] '{parts[0]}' has no attribute '{part}'"
        if isinstance(obj, FunctionRef): return f"[homo] function {obj.name}"
        return obj

    def _eval_ast(self, node, local_vars):
        if isinstance(node, _ast.Constant): return node.value
        if isinstance(node, _ast.Name): return self._resolve_name(node.id, local_vars)
        if isinstance(node, _ast.List): return [self._eval_ast(e, local_vars) for e in node.elts]
        if isinstance(node, _ast.Tuple): return tuple(self._eval_ast(e, local_vars) for e in node.elts)
        if isinstance(node, _ast.Dict): return {self._eval_ast(k, local_vars): self._eval_ast(v, local_vars) for k, v in zip(node.keys, node.values)}
        if isinstance(node, _ast.BinOp):
            left = self._eval_ast(node.left, local_vars)
            right = self._eval_ast(node.right, local_vars)
            if isinstance(node.op, _ast.Add):
                if isinstance(left, str) or isinstance(right, str): return str(left) + str(right)
                if isinstance(left, list) and isinstance(right, list): return left + right
                return left + right
            if isinstance(node.op, _ast.Sub): return left - right
            if isinstance(node.op, _ast.Mult): return left * right
            if isinstance(node.op, _ast.Div): return left / right
            if isinstance(node.op, _ast.Mod): return left % right
            if isinstance(node.op, _ast.Pow): return left ** right
            raise ValueError("Unsupported operator")
        if isinstance(node, _ast.UnaryOp):
            operand = self._eval_ast(node.operand, local_vars)
            if isinstance(node.op, _ast.Not): return not operand
            if isinstance(node.op, _ast.UAdd): return +operand
            if isinstance(node.op, _ast.USub): return -operand
            raise ValueError("Unsupported unary operator")
        if isinstance(node, _ast.BoolOp):
            if isinstance(node.op, _ast.And):
                for v in node.values:
                    if not self._eval_ast(v, local_vars): return False
                return True
            if isinstance(node.op, _ast.Or):
                for v in node.values:
                    if self._eval_ast(v, local_vars): return True
                return False
            raise ValueError("Unsupported boolean operator")
        if isinstance(node, _ast.Compare):
            left = self._eval_ast(node.left, local_vars)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_ast(comparator, local_vars)
                if isinstance(op, _ast.Eq): ok = left == right
                elif isinstance(op, _ast.NotEq): ok = left != right
                elif isinstance(op, _ast.Lt): ok = left < right
                elif isinstance(op, _ast.LtE): ok = left <= right
                elif isinstance(op, _ast.Gt): ok = left > right
                elif isinstance(op, _ast.GtE): ok = left >= right
                elif isinstance(op, _ast.In): ok = left in right
                elif isinstance(op, _ast.NotIn): ok = left not in right
                else: raise ValueError("Unsupported comparison operator")
                if not ok: return False
                left = right
            return True
        if isinstance(node, _ast.Subscript):
            value = self._eval_ast(node.value, local_vars)
            sl = node.slice
            if hasattr(_ast, "Index") and isinstance(sl, _ast.Index): sl = sl.value
            if isinstance(sl, _ast.Slice):
                lower = self._eval_ast(sl.lower, local_vars) if sl.lower else None
                upper = self._eval_ast(sl.upper, local_vars) if sl.upper else None
                step = self._eval_ast(sl.step, local_vars) if sl.step else None
                return value[slice(lower, upper, step)]
            idx = self._eval_ast(sl, local_vars)
            return value[idx]
        if isinstance(node, _ast.Attribute):
            obj = self._eval_ast(node.value, local_vars)
            if isinstance(obj, dict): return obj.get(node.attr)
            if isinstance(obj, ModuleNamespace):
                val = obj.resolve(node.attr)
                if val is _MISSING: raise ValueError("Unsupported attribute access")
                return val
            if hasattr(obj, node.attr): return getattr(obj, node.attr)
            raise ValueError("Unsupported attribute access")
        if isinstance(node, _ast.Call):
            if not isinstance(node.func, _ast.Name): raise ValueError("Unsupported function call")
            func_name = node.func.id
            if func_name not in _SAFE_FUNCS: raise ValueError("Unsupported function call")
            args = [self._eval_ast(a, local_vars) for a in node.args]
            kwargs = {}
            for kw in node.keywords:
                if kw.arg is None: raise ValueError("Unsupported kwargs")
                kwargs[kw.arg] = self._eval_ast(kw.value, local_vars)
            return _SAFE_FUNCS[func_name](*args, **kwargs)
        raise ValueError("Unsupported expression")

    def _safe_eval(self, expr, local_vars, *, normalized=False):
        if expr is None: return ""
        if not normalized: expr = self._normalize_expr(expr)
        expr = str(expr).strip()
        if not expr: return ""
        if expr not in self._ast_cache:
            self._ast_cache[expr] = _ast.parse(expr, mode="eval")
        return self._eval_ast(self._ast_cache[expr].body, local_vars)

    def evaluate(self, expr, local_vars):
        expr = str(expr).strip()
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
            
        if expr.startswith("call "):
            cp = expr[5:].split()
            return self.call_function(cp[0], cp[1:], local_vars)
            
        if " call " in expr:
            def _replace_call(m):
                res = self.call_function(m.group(1), m.group(2).split(), local_vars)
                return str(res)
            expr = _re.sub(r'\bcall\s+(\w+)\s+(.*)$', _replace_call, expr)
            
        expr = self._normalize_expr(expr)
        try:
            return self._safe_eval(expr, local_vars, normalized=True)
        except NameError as e:
            return f"Variable '{e.args[0]}' not found"
        except Exception:
            if " + " in expr:
                parts = expr.split(" + ")
                result = ""
                for p in parts:
                    p = p.strip()
                    if (p.startswith("'") and p.endswith("'")) or \
                       (p.startswith('"') and p.endswith('"')):
                        result += p[1:-1]
                    else:
                        result += p
                return result
            return expr

    def _eval_path(self, expr, scope):
        raw = str(expr).strip()
        # If it's a quoted string, strip the quotes and return as-is
        if (raw.startswith('"') and raw.endswith('"')) or \
           (raw.startswith("'") and raw.endswith("'")):
            return raw[1:-1]
        # Try to resolve as a variable first
        if raw in scope:
            return str(scope[raw]).strip('"\'')
        if raw in self.variables:
            return str(self.variables[raw]).strip('"\'')
        # Fall back: evaluate the expression; if it errors, use the raw text
        val = str(self.evaluate(raw, scope))
        if val.startswith("Variable '") and val.endswith("' not found"):
            return raw.strip('"\'')
        return val.strip("'\"")

    def _show_value(self, token, scope=None):
        scope = scope if scope is not None else self.variables
        raw = token.strip()
        
        if raw.startswith("call "):
            cp = raw[5:].split()
            return self.call_function(cp[0], cp[1:], scope)
            
        if (raw.startswith('"') and raw.endswith('"')) or \
           (raw.startswith("'") and raw.endswith("'")):
            inner = raw[1:-1]
            def _interp(m):
                key = m.group(1).strip()
                val = scope.get(key, self.variables.get(key, m.group(0)))
                return str(val)
            interpolated = _re.sub(r'\{(\w+)\}', _interp, inner)
            if interpolated != inner:
                return interpolated
            return inner

        m = _re.fullmatch(r'(\w+)\[(-?\d+)\]', token.strip())
        if m:
            var, idx = m.group(1), int(m.group(2))
            val = scope.get(var, self.variables.get(var))
            if isinstance(val, list):
                try: return val[idx]
                except IndexError: return f"[homo] Index {idx} out of range"
            if isinstance(val, str) and val.startswith('['):
                items = val.strip('[]').split(',')
                try: return items[idx].strip().strip('"\'')
                except IndexError: return f"[homo] Index {idx} out of range"
            return f"[homo] '{var}' is not a list"

        if '.' in token and not token.startswith('"'):
            val = self._resolve_dotted_value(token.strip(), scope)
            if val is not _MISSING:
                return val

        low = token.strip().lower()

        m = _re.match(r'square root of (.+)', low)
        if m:
            val = self.evaluate(m.group(1), scope)
            try: return _math.sqrt(float(val))
            except Exception: return f"[homo] Cannot sqrt({val})"

        m = _re.match(r'random number between (\S+) and (\S+)', low)
        if m:
            a = self.evaluate(m.group(1), scope)
            b = self.evaluate(m.group(2), scope)
            try: return _random.randint(int(a), int(b))
            except Exception: return "[homo] Random error"

        if low in ('current time', 'time'):
            return _datetime.datetime.now().strftime('%H:%M:%S')
        if low in ('current date', 'date', 'today'):
            return _datetime.datetime.now().strftime('%Y-%m-%d')

        m = _re.match(r'length of (.+)', low)
        if m:
            val = scope.get(m.group(1).strip(), m.group(1).strip())
            return len(str(val))

        m = _re.match(r'type of (.+)', low)
        if m:
            val = scope.get(m.group(1).strip(), m.group(1).strip())
            return type(val).__name__

        if token in scope:          return scope[token]
        if token in self.variables: return self.variables[token]
        if (token.startswith('"') and token.endswith('"')) or \
           (token.startswith("'") and token.endswith("'")):
            return token[1:-1]
        return self.evaluate(token, scope)

    def _format_value(self, val):
        """Format a value for display output."""
        if isinstance(val, list):
            formatted_items = []
            for item in val:
                if isinstance(item, str):
                    formatted_items.append(f'"{item}"')
                else:
                    formatted_items.append(str(item))
            return "[" + ",".join(formatted_items) + "]"
        if isinstance(val, dict):
            pairs = []
            for k, v in val.items():
                if k == "__class__":
                    continue
                kf = f'"{k}"' if isinstance(k, str) else str(k)
                vf = f'"{v}"' if isinstance(v, str) else str(v)
                pairs.append(f"{kf}: {vf}")
            return "{" + ", ".join(pairs) + "}"
        return str(val)

    def _eval_condition(self, cond_text, local_vars):
        cond_text = cond_text.strip()
        if " contains " in cond_text:
            cond_text = _re.sub(r'(\S+)\s+contains\s+(\S+)', r'\2 in \1', cond_text)
        try:
            expr = self._normalize_condition(cond_text)
            return bool(self._safe_eval(expr, local_vars, normalized=True))
        except Exception:
            return False

    def _split_if_otherwise(self, body, start_idx):
        true_b, else_b = [], []
        in_else = False
        idx = start_idx
        
        # We find the indentation of the starting "if" line (which is start_idx - 1)
        if_line_raw = body[start_idx - 1]
        base_indent = len(if_line_raw) - len(if_line_raw.lstrip())
        
        while idx < len(body):
            raw_line = body[idx]
            if not raw_line.strip():
                (else_b if in_else else true_b).append(raw_line)
                idx += 1
                continue
                
            curr_indent = len(raw_line) - len(raw_line.lstrip())
            line = raw_line.strip()
            
            # An "otherwise" at the exact same indentation as the "if" switches to else_b
            if curr_indent == base_indent and line == "otherwise":
                in_else = True
                idx += 1
                continue
                
            # Any non-empty line at or below base_indent ends the entire if-otherwise construct
            if curr_indent <= base_indent:
                break
                
            (else_b if in_else else true_b).append(raw_line)
            idx += 1
            
        return true_b, else_b, idx

    def run_block(self, body, local_vars):
        i = 0
        while i < len(body):
            raw_line = body[i]
            if not raw_line.strip():
                i += 1; continue
            
            indent_len = len(raw_line) - len(raw_line.lstrip())
            line = raw_line.strip()

            if line == "break":
                return "__break__"

            if line.startswith("if "):
                true_b, else_b, end = self._split_if_otherwise(body, i + 1)
                branch = true_b if self._eval_condition(line[3:].strip(), local_vars) else else_b
                result = self.run_block(branch, local_vars)
                if result is not None: return result
                i = end; continue

            elif line == "otherwise":
                i += 1; continue

            elif line.startswith("define "):
                parts = line.split()
                func_name, params = parts[1], parts[2:]
                func_body = []
                j = i + 1
                while j < len(body):
                    bline = body[j]
                    if not bline.strip():
                        j += 1; continue
                    b_indent = len(bline) - len(bline.lstrip())
                    if b_indent > indent_len:
                        func_body.append(bline)
                        j += 1
                    else:
                        break
                self.functions[func_name] = {"params": params, "body": func_body}
                i = j; continue

            elif line.startswith("while "):
                condition = line[6:].strip()
                while_body = []
                j = i + 1
                while j < len(body):
                    bline = body[j]
                    if not bline.strip(): j += 1; continue
                    b_indent = len(bline) - len(bline.lstrip())
                    if b_indent > indent_len:
                        while_body.append(bline)
                        j += 1
                    else:
                        break
                safety = 0
                cond_low = condition.strip().lower()
                while True:
                    if cond_low not in ("true", "1", "yes"):
                        if not self._eval_condition(condition, local_vars):
                            break
                    result = self.run_block(while_body, local_vars)
                    if result == "__break__":
                        break
                    if result is not None and result != "__break__":
                        return result
                    safety += 1
                    if safety > 100_000:
                        print("[homo] Warning: loop limit reached"); break
                i = j; continue

            elif line.startswith("for ") and " in " in line:
                parts = line[4:].strip().split(" in ")
                variable = parts[0].strip()
                iterable = parts[1].strip()
                for_body = []
                j = i + 1
                while j < len(body):
                    bline = body[j]
                    if not bline.strip():
                        j += 1; continue
                    b_indent = len(bline) - len(bline.lstrip())
                    if b_indent > indent_len:
                        for_body.append(bline)
                        j += 1
                    else:
                        break
                items = local_vars.get(iterable, self.variables.get(iterable))
                if items is None:
                    items = self._resolve_iterable(iterable)
                for item in items:
                    local_vars[variable] = item
                    result = self.run_block(for_body, local_vars)
                    if result == "__break__":
                        break
                    if result is not None and result != "__break__":
                        return result
                i = j; continue

            elif line.startswith("repeat "):
                count_expr = line[7:].strip()
                if count_expr.endswith(" times"):
                    count_expr = count_expr[:-6].strip()
                repeat_body = []
                j = i + 1
                while j < len(body):
                    bline = body[j]
                    if not bline.strip():
                        j += 1; continue
                    b_indent = len(bline) - len(bline.lstrip())
                    if b_indent > indent_len:
                        repeat_body.append(bline)
                        j += 1
                    else:
                        break
                count = int(self.evaluate(count_expr, local_vars))
                for _ in range(count):
                    result = self.run_block(repeat_body, local_vars)
                    if result == "__break__":
                        break
                    if result is not None and result != "__break__":
                        return result
                i = j; continue

            elif line.startswith("calculate "):
                rest  = line[len("calculate "):]
                parts = rest.split(" as ", 1)
                local_vars[parts[0].strip()] = self.evaluate(
                    parts[1].strip() if len(parts) > 1 else "0", local_vars)

            elif line.startswith("set "):
                rest  = line[len("set "):]
                parts = rest.split(" as ", 1)
                var_name = parts[0].strip()
                rhs      = parts[1].strip() if len(parts) > 1 else ""
                import re as _re2
                m = _re2.fullmatch(r'(\w+)\[(-?\d+|\w+)\]', var_name)
                if m:
                    lst_name, idx_raw = m.group(1), m.group(2)
                    try: idx = int(idx_raw)
                    except ValueError: idx = int(local_vars.get(idx_raw, idx_raw))
                    val = self.evaluate(rhs, local_vars)
                    target = local_vars.get(lst_name, self.variables.get(lst_name, []))
                    if isinstance(target, list):
                        target[idx] = val
                        local_vars[lst_name] = target
                        self.variables[lst_name] = target
                elif '.' in var_name:
                    val = self.evaluate(rhs, local_vars)
                    target, attr = self._resolve_dotted_container(var_name, local_vars)
                    if isinstance(target, dict): target[attr] = val
                    elif isinstance(target, ModuleNamespace): target.set(attr, val)
                    else: print(f"[homo] '{var_name}' is not an object")
                    local_vars[var_name.split('.')[0]] = target
                elif rhs.startswith("call "):
                    cp = rhs[len("call "):].split()
                    local_vars[var_name] = self.call_function(cp[0], cp[1:], local_vars)
                else:
                    local_vars[var_name] = self.evaluate(rhs, local_vars)

            elif line.startswith("show "):
                token = line[5:].strip()
                val = self._show_value(token, local_vars)
                val_str = self._format_value(val)
                if val_str.rstrip().endswith(":"):
                    print(val_str, end=" ")
                else:
                    print(val_str)

            elif line.startswith("ask "):
                rest = line[4:].strip()
                if rest.startswith('"'):
                    end_quote   = rest.index('"', 1)
                    prompt_text = rest[1:end_quote].rstrip()
                    if not prompt_text.endswith(" "): prompt_text += " "
                    var = rest[end_quote + 1:].strip().lstrip(",").strip()
                    local_vars[var if var else rest] = input(prompt_text).strip()
                else:
                    local_vars[rest] = input(f"{rest}? ").strip()

            elif line.startswith("append ") and " to " in line:
                parts = line[7:].split(" to ", 1)
                val   = self.evaluate(parts[0].strip(), local_vars)
                lst   = parts[1].strip()
                target = local_vars.get(lst, self.variables.get(lst, []))
                if not isinstance(target, list): target = []
                target.append(val)
                local_vars[lst] = target
                self.variables[lst] = target

            elif line.startswith("return "):
                return self.evaluate(line[7:].strip(), local_vars)

            elif line.startswith("call "):
                cp = line[5:].split()
                result = self.call_function(cp[0], cp[1:], local_vars)
                if result is not None:
                    local_vars["result"] = result
                
            elif line.startswith("read "):
                rest = line[5:].strip()
                if " as " in rest:
                    parts = rest.split(" as ", 1)
                    fname_expr = parts[0].strip()
                    var_name = parts[1].strip()
                else:
                    fname_expr = rest
                    var_name = "content"
                fname = self._eval_path(fname_expr, local_vars)
                try:
                    with open(fname) as f:
                        file_content = f.read()
                    local_vars[var_name] = file_content
                except FileNotFoundError:
                    print(f"[homo] Error: file '{fname}' not found")

            elif line.startswith("write ") and " as " in line:
                parts = line[6:].split(" as ", 1)
                fname = self._eval_path(parts[0].strip(), local_vars)
                content_val = str(self._show_value(parts[1].strip(), local_vars))
                with open(fname, "w") as f:
                    f.write(content_val)
                    
            elif line.startswith("create object ") and " as " in line:
                parts = line[14:].split(" as ")
                cls = parts[0].strip()
                var = parts[1].strip()
                if cls not in self.classes:
                    print(f"[homo] Error: class '{cls}' not defined")
                else:
                    obj = dict(self.classes[cls]["fields"])
                    obj["__class__"] = cls
                    local_vars[var] = obj
                    
            elif line.startswith("create ") and " as " in line:
                parts = line[7:].split(" as ")
                cls = parts[0].strip()
                var = parts[1].strip()
                if cls not in self.classes:
                    print(f"[homo] Error: class '{cls}' not defined")
                else:
                    obj = dict(self.classes[cls]["fields"])
                    obj["__class__"] = cls
                    local_vars[var] = obj

            i += 1
        return None

    def call_function(self, name, args, parent_vars, *, allow_parent_vars=True):
        if "." in name:
            parts = name.split(".")
            func_name = parts[-1]
            module_path = ".".join(parts[:-1])
            if len(parts) == 2:
                container = (parent_vars or {}).get(parts[0], self.variables.get(parts[0]))
            else:
                container = self._resolve_dotted_value(module_path, parent_vars or self.variables)
            if isinstance(container, ModuleNamespace):
                export = container.resolve(func_name)
                if isinstance(export, FunctionRef):
                    return export.interpreter.call_function(func_name, args, parent_vars, allow_parent_vars=False)
                print(f"[homo] Error: '{name}' is not a function")
                return None
        if name not in self.functions:
            print(f"[homo] Error: function '{name}' not defined")
            return None
        func = self.functions[name]
        # Build a clean scope: global vars + parent context + params
        # This ensures recursion works with isolated scopes
        local_vars = dict(self.variables)
        if parent_vars and allow_parent_vars:
            local_vars.update(parent_vars)
            
        for i, param in enumerate(func["params"]): 
            if i < len(args):
                arg_str = " ".join(args[i:]) if i == len(func["params"]) - 1 else args[i]
                local_vars[param] = self.evaluate(arg_str, parent_vars if parent_vars else self.variables)
            
        return self.run_block(func["body"], local_vars)

    def _resolve_module_path(self, mod_name):
        mod_name = mod_name.strip('"\'')
        if mod_name.endswith(".homo") or "\\" in mod_name or "/" in mod_name:
            rel = mod_name
        else:
            rel = mod_name.replace(".", os.sep) + ".homo"
            
        path1 = os.path.abspath(os.path.join(self.base_dir, rel))
        if os.path.isfile(path1): return path1
        
        path2 = os.path.abspath(os.path.join(os.getcwd(), rel))
        if os.path.isfile(path2): return path2
        
        return path1

    def _attach_module(self, mod_name, module_obj):
        parts = mod_name.split(".")
        if len(parts) == 1:
            self.variables[parts[0]] = module_obj
            return
        root = self.variables.get(parts[0])
        if not isinstance(root, dict):
            root = {}
            self.variables[parts[0]] = root
        current = root
        for part in parts[1:-1]:
            nxt = current.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                current[part] = nxt
            current = nxt
        current[parts[-1]] = module_obj

    def _load_homo_module(self, mod_name):
        if mod_name in self.module_cache:
            return self.module_cache[mod_name]
        path = self._resolve_module_path(mod_name)
        if not os.path.isfile(path):
            return None
        from lexer import Lexer
        from parser import Parser
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
            tokens = Lexer().tokenize(source)
            ast = Parser().parse(tokens)
            module_interpreter = Interpreter(base_dir=os.path.dirname(path), module_cache=self.module_cache)
            module_interpreter._module_name = mod_name
            module_ns = ModuleNamespace(mod_name, module_interpreter, set())
            self.module_cache[mod_name] = module_ns
            module_interpreter.execute(ast)
            # Auto-export all functions and variables if no explicit exports
            if module_interpreter._exported_names:
                module_ns.export_names = set(module_interpreter._exported_names)
            else:
                module_ns.export_names = set(module_interpreter.functions.keys()) | set(module_interpreter.variables.keys())
            return module_ns
        except Exception as e:
            self.module_cache.pop(mod_name, None)
            print(f"[homo] Module load error: {mod_name} ({e})")
            return None

    def _resolve_iterable(self, token):
        val = self.variables.get(token, token)
        if isinstance(val, (list, range)): return val
        s = str(val).strip()
        if s.startswith('[') and s.endswith(']'):
            inner = s[1:-1]
            items = [x.strip().strip('"\'') for x in inner.split(',') if x.strip()]
            result = []
            for item in items:
                try: result.append(int(item))
                except ValueError:
                    try: result.append(float(item))
                    except ValueError: result.append(item)
            return result
        try:
            evaled = self._safe_eval(s, self.variables)
            if isinstance(evaled, (list, range, tuple)): return evaled
        except Exception:
            pass
        return s.split(',')

    def _log(self, message):
        ts = _datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"[{ts}] {message}"
        print(entry)
        try:
            with open(self._log_file, "a") as f: f.write(entry + "\n")
        except Exception: pass

    def _import_module(self, module, pip_name=None):
        try:
            return _importlib.import_module(module)
        except ImportError:
            print(f"[homo] install {pip_name or module} to use {module}")
            return None

    def _coerce_value(self, val):
        if isinstance(val, (int, float, bool)): return val
        s = str(val).strip().strip('"\'')
        low = s.lower()
        if low in ("true", "yes"): return True
        if low in ("false", "no"): return False
        if low in ("none", "null"): return None
        try: return int(s)
        except ValueError:
            try: return float(s)
            except ValueError: return s

    def _parse_columns(self, cols):
        if cols is None: return None
        if isinstance(cols, (list, tuple)): return [str(c).strip() for c in cols]
        return [c.strip() for c in str(cols).split(",") if c.strip()]

    def _get_df(self, name):
        df = self.variables.get(name)
        if df is None:
            print(f"[homo] DataFrame '{name}' not found")
            return None
        return df

    def _prepare_ml_data(self, df, features, target=None, info=None, is_train=False):
        pd = self._import_module("pandas", "pandas")
        if not pd: return df, None if target else df
        
        def _is_categorical(col):
            try:
                from pandas.api.types import is_string_dtype, is_object_dtype
                if is_string_dtype(col) or is_object_dtype(col): return True
                if isinstance(col.dtype, pd.CategoricalDtype): return True
            except ImportError:
                pass
            return str(col.dtype).lower() in ("object", "category", "string", "str")

        X = df[features].copy()
        y = df[target].copy() if target and target in df.columns else None

        if info is None:
            info = {}

        if is_train:
            info["encoders"] = {}
            for col in X.columns:
                if _is_categorical(X[col]):
                    X[col] = X[col].fillna("Missing")
                    from sklearn.preprocessing import LabelEncoder
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
                    info["encoders"][col] = le
                else:
                    X[col] = X[col].fillna(X[col].median() if not X[col].isnull().all() else 0)
            
            if y is not None:
                if _is_categorical(y):
                    y = y.fillna("Missing")
                    from sklearn.preprocessing import LabelEncoder
                    le_y = LabelEncoder()
                    y = le_y.fit_transform(y.astype(str))
                    info["target_encoder"] = le_y
                else:
                    y = y.fillna(y.median() if not y.isnull().all() else 0)
        else:
            encoders = info.get("encoders", {})
            for col in X.columns:
                if col in encoders:
                    le = encoders[col]
                    X[col] = X[col].fillna("Missing")
                    # Handle unseen labels by mapping them to a special class or the first class
                    classes = list(le.classes_)
                    X[col] = X[col].apply(lambda val: val if str(val) in classes else (classes[0] if classes else val))
                    X[col] = le.transform(X[col].astype(str))
                else:
                    if _is_categorical(X[col]):
                        X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
                    else:
                        X[col] = X[col].fillna(X[col].median() if not X[col].isnull().all() else 0)
            if y is not None:
                target_encoder = info.get("target_encoder")
                if target_encoder:
                    y = y.fillna("Missing")
                    classes = list(target_encoder.classes_)
                    y = y.apply(lambda val: val if str(val) in classes else (classes[0] if classes else val))
                    y = target_encoder.transform(y.astype(str))
                else:
                    if _is_categorical(y):
                        y = pd.to_numeric(y, errors='coerce').fillna(0)
                    else:
                        y = y.fillna(y.median() if not y.isnull().all() else 0)

        return X, y

    def execute(self, ast):
        for line_no, node in enumerate(ast, start=1):
            try:
                self._exec_node(node)
            except Exception as e:
                print(f"[homo] Runtime error on statement {line_no} ({type(node).__name__}): {e}")

    def _exec_node(self, node): 

        if isinstance(node, BreakNode): return
        
        elif isinstance(node, SetIndexNode):
            target = self.variables.get(node.name, [])
            idx = int(self.evaluate(str(node.index), self.variables))
            val = self.evaluate(str(node.value), self.variables)
            if isinstance(target, list):
                target[idx] = val
                self.variables[node.name] = target

        elif isinstance(node, FunctionNode):
            self.functions[node.name] = {"params": node.parameters, "body": node.body}

        elif isinstance(node, ExportNode):
            names = [n.strip() for n in str(node.name).split(",") if n.strip()]
            for name in names:
                self._exported_names.add(name)

        elif isinstance(node, SetNode):
            name  = str(node.name)
            value = str(node.value).strip()
            import re as _re2
            m = _re2.fullmatch(r'(\w+)\[(-?\d+|\w+)\]', name.strip())
            if m:
                lst_name, idx_raw = m.group(1), m.group(2)
                try: idx = int(idx_raw)
                except ValueError: idx = int(self.variables.get(idx_raw, idx_raw))
                val = self.evaluate(value, self.variables)
                target = self.variables.get(lst_name, [])
                if isinstance(target, list):
                    target[idx] = val
                    self.variables[lst_name] = target
                return
            if '.' in name:
                val = self.evaluate(value, self.variables)
                target, attr = self._resolve_dotted_container(name, self.variables)
                if isinstance(target, dict):
                    target[attr] = val
                elif isinstance(target, ModuleNamespace):
                    target.set(attr, val)
                else:
                    print(f"[homo] '{name}' is not an object")
                return
            m = _re.fullmatch(r'(\w+)\[(-?\d+)\]', name.strip())
            if m:
                var, idx = m.group(1), int(m.group(2))
                val = self.evaluate(value, self.variables)
                if var in self.variables and isinstance(self.variables[var], list):
                    self.variables[var][idx] = val
                return
            if value.startswith("call "):
                cp = value[len("call "):].split()
                ret = self.call_function(cp[0], cp[1:], self.variables)
                self.variables[name] = ret if ret is not None else self.variables.get("result")
            else:
                self.variables[name] = self.evaluate(value, self.variables)

        elif isinstance(node, SetDictNode):
            self.variables[node.name] = {
                k: self.evaluate(v.rstrip(','), self.variables) for k, v in node.pairs.items()
            }

        elif isinstance(node, ShowNode):
            raw_val = self._show_value(node.value)
            val = self._format_value(raw_val)
            print(val)

        elif isinstance(node, CalculateNode):
            expr = str(node.expression).strip()
            _special = ("square root of", "random number between",
                        "length of", "type of")
            _exact = {"current time", "current date", "today", "time", "date"}
            if any(expr.lower().startswith(s) for s in _special) or \
               expr.lower() in _exact:
                self.variables[node.result] = self._show_value(expr)
            else:
                self.variables[node.result] = self.evaluate(expr, self.variables)

        elif isinstance(node, AskNode):
            prompt = node.prompt if node.prompt else f"{node.variable}? "
            if not prompt.endswith(" "): prompt += " "
            self.variables[node.variable] = input(prompt).strip()

        elif isinstance(node, IfNode):
            branch = node.true_body if self._eval_condition(node.condition, self.variables) \
                     else node.false_body
            if isinstance(branch, list):
                if len(branch) == 1 and isinstance(branch[0], str) and branch[0].startswith("__IF__"):
                    s = branch[0]
                    import ast as _ast_mod
                    try:
                        s = s[6:]
                        cond, rest = s.split("__THEN__", 1)
                        true_raw, false_raw = rest.split("__ELSE__", 1)
                        true_b  = _ast_mod.literal_eval(true_raw)
                        false_b = _ast_mod.literal_eval(false_raw)
                        nested = true_b if self._eval_condition(cond, self.variables) else false_b
                        self.run_block(nested, self.variables)
                    except Exception:
                        print(s)
                else:
                    self.run_block(branch, self.variables)
            elif branch:
                s = str(branch)
                if s.startswith("__IF__"):
                    import ast as _ast_mod
                    try:
                        s = s[6:]
                        cond, rest = s.split("__THEN__", 1)
                        true_raw, false_raw = rest.split("__ELSE__", 1)
                        true_b  = _ast_mod.literal_eval(true_raw)
                        false_b = _ast_mod.literal_eval(false_raw)
                        nested = true_b if self._eval_condition(cond, self.variables) else false_b
                        self.run_block(nested, self.variables)
                    except Exception:
                        print(s)
                else:
                    print(str(self._show_value(s)))

        elif isinstance(node, WhileNode):
            safety = 0
            cond = node.condition.strip().lower()
            while True:
                if cond not in ("true", "1", "yes"):
                    if not self._eval_condition(node.condition, self.variables):
                        break
                result = self.run_block(node.body, self.variables)
                if result == "__break__":
                    break
                safety += 1
                if safety > 100_000:
                    print("[homo] Warning: loop limit reached"); break

        elif isinstance(node, ForNode):
            for item in self._resolve_iterable(node.iterable):
                self.variables[node.variable] = item
                result = self.run_block(node.body, self.variables)
                if result == "__break__":
                    break

        elif isinstance(node, RepeatNode):
            count = int(self.evaluate(str(node.count), self.variables))
            for _ in range(count):
                result = self.run_block(node.body, self.variables)
                if result == "__break__":
                    break

        elif isinstance(node, ReadNode):
            fname = self._eval_path(node.filename, self.variables)
            try:
                with open(fname) as f: file_data = f.read()
                self.variables[node.variable] = file_data
            except FileNotFoundError:
                print(f"[homo] Error: file '{fname}' not found")

        elif isinstance(node, WriteNode):
            fname   = self._eval_path(str(node.filename), self.variables)
            content = str(self._show_value(str(node.content), self.variables))
            with open(fname, "w") as f: f.write(content)

        elif isinstance(node, TryNode):
            scope = dict(self.variables); caught = False
            for line in node.try_body:
                line = line.strip()
                try:
                    if line.startswith("calculate "):
                        rest  = line[len("calculate "):]
                        parts = rest.split(" as ", 1)
                        val   = self.evaluate(parts[1].strip(), scope)
                        if isinstance(val, str) and not val.replace('.','').lstrip('-').isdigit():
                            raise ValueError(f"Cannot evaluate: {parts[1].strip()!r}")
                        scope[parts[0].strip()] = val
                    elif line.startswith("set "):
                        rest  = line[len("set "):]
                        parts = rest.split(" as ", 1)
                        scope[parts[0].strip()] = self.evaluate(parts[1].strip(), scope)
                    elif line.startswith("show "):
                        print(self._show_value(line[5:].strip(), scope))
                    elif line.startswith("call "):
                        cp = line[5:].split()
                        self.call_function(cp[0], cp[1:], scope)
                except Exception as e:
                    self.variables["error"] = str(e)
                    self.run_block(node.catch_body, dict(self.variables))
                    caught = True; break
            if not caught: self.variables.update(scope)

        elif isinstance(node, OpenDBNode):
            self.db_file = str(node.db_name).strip('"\'') + ".json"
            if os.path.exists(self.db_file):
                with open(self.db_file) as f: self.db = json.load(f)
            else: self.db = {}
            print(f"[homo] Database '{self.db_file}' opened ({len(self.db)} records)")

        elif isinstance(node, SaveDBNode):
            key = str(node.entity).strip('"\'')
            val = self._show_value(str(node.value))
            self.db[key] = val
            if self.db_file:
                with open(self.db_file, "w") as f: json.dump(self.db, f, indent=2)
            print(f"[homo] Saved '{key}' = '{val}'")

        elif isinstance(node, ConnectDBNode):
            print(f"[homo] Connecting to {node.db_type} at {node.url or '(local)'}")
            try:
                if node.db_type.lower() in ("sqlite", "sqlite3"):
                    import sqlite3
                    self.variables["_db_conn"] = sqlite3.connect(node.url or ":memory:")
                    print("[homo] SQLite connected")
                else:
                    print(f"[homo] External DB '{node.db_type}' — use install + use for full drivers")
            except Exception as e:
                print(f"[homo] DB connect error: {e}")

        elif isinstance(node, QueryDBNode):
            results = [v for k, v in self.db.items() if node.condition in str(v) or node.condition == "*"]
            self.variables[node.variable] = results
            print(f"[homo] Query '{node.condition}' from '{node.table}' → {len(results)} results")

        elif isinstance(node, DeleteDBNode):
            key = str(node.key).strip('"\'')
            if key in self.db:
                del self.db[key]
                if self.db_file:
                    with open(self.db_file, "w") as f: json.dump(self.db, f, indent=2)
                print(f"[homo] Deleted '{key}'")
            else:
                print(f"[homo] Key '{key}' not found in database")

        elif isinstance(node, InstallNode):
            pkg = str(node.package).strip('"\'')
            print(f"[homo] Installing '{pkg}'...")
            r = subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                               capture_output=True, text=True)
            print(f"[homo] {'Done' if r.returncode == 0 else 'Failed: ' + r.stderr[:120]}")

        elif isinstance(node, CheckNode):
            lval = self._show_value(str(node.left))
            rval = self._show_value(str(node.right))
            if str(lval) == str(rval):
                print(f"[homo] Check passed: {node.left} == {node.right}")
            else:
                print(f"[homo] Check FAILED: {node.left} ({lval}) != {node.right} ({rval})")

        elif isinstance(node, AssertNode):
            if not self._eval_condition(node.condition, self.variables):
                msg = str(self._show_value(node.message))
                print(f"[homo] ASSERTION FAILED: {msg}")
                raise AssertionError(msg)

        elif isinstance(node, ConvertNode):
            val    = self._show_value(str(node.variable))
            action = str(node.action).lower()
            conv = {"integer":   lambda v: int(float(v)),
                    "int":       lambda v: int(float(v)),
                    "float":     float,
                    "string":    str,  
                    "str":       str,
                    "text":      str,
                    "uppercase": lambda v: str(v).upper(),
                    "lowercase": lambda v: str(v).lower(),
                    "length":    lambda v: len(str(v)),
                    "list":      list}
            if action in conv:
                val = conv[action](val)
                self.variables[str(node.variable)] = val
                print(f"[homo] {node.variable} → {action}: {val}")
            else:
                print(f"[homo] Unknown conversion: '{action}'")

        elif isinstance(node, CreateTableNode):
            self.tables[node.name] = []; print(f"[homo] Table '{node.name}' created")

        elif isinstance(node, AddToTableNode):
            row = [v.strip().strip('"\'') for v in str(node.row_data).strip('"\'').split(",")]
            self.tables.setdefault(node.table, []).append(row)
            print(f"[homo] Row added to '{node.table}': {row}")

        elif isinstance(node, PrintTableNode):
            tbl = self.tables.get(node.name, [])
            if not tbl: print(f"[homo] Table '{node.name}' is empty"); return
            if tbl:
                col_w = [max(len(str(r[c])) for r in tbl if c < len(r)) for c in range(len(tbl[0]))]
                sep   = "+-" + "-+-".join("-" * w for w in col_w) + "-+"
                print(sep)
                for row in tbl:
                    print("| " + " | ".join(str(row[c]).ljust(col_w[c]) for c in range(len(row))) + " |")
                    print(sep)

        elif isinstance(node, ClassNode):
            fields, methods = {}, {}
            for line in node.body:
                line = line.strip()
                if line.startswith("set ") and " as " in line:
                    parts = line[4:].split(" as ", 1)
                    fields[parts[0].strip()] = self.evaluate(parts[1].strip(), self.variables)
                elif line.startswith("define "):
                    parts = line.split(); methods[parts[1]] = parts[2:]
            self.classes[node.name] = {"fields": fields, "methods": methods}
            print(f"[homo] Class '{node.name}' defined")

        elif isinstance(node, CreateObjNode):
            cls = str(node.class_name)
            if cls not in self.classes:
                print(f"[homo] Error: class '{cls}' not defined"); return
            obj = dict(self.classes[cls]["fields"]); obj["__class__"] = cls
            self.variables[str(node.instance_name)] = obj
            print(f"[homo] Object '{node.instance_name}' created from '{cls}'")

        elif isinstance(node, InheritClassNode):
            child, parent = str(node.child), str(node.parent)
            if parent not in self.classes:
                print(f"[homo] Error: parent '{parent}' not defined"); return
            p = self.classes[parent]
            self.classes[child] = {"fields": dict(p["fields"]), "methods": dict(p["methods"])}
            print(f"[homo] Class '{child}' inherits from '{parent}'")

        elif isinstance(node, CallNode):
            result = self.call_function(node.name, node.arguments, self.variables)
            if result is not None: self.variables["result"] = result

        elif isinstance(node, ReturnNode):
            self.variables["_return"] = self.evaluate(node.expression, self.variables)

        elif isinstance(node, VisitNode):
            url = str(node.url).strip('"\'')
            if not url.startswith("http"): url = "https://" + url
            import webbrowser; webbrowser.open(url)
            print(f"[homo] Opened '{url}' in browser")

        elif isinstance(node, FetchNode):
            url = str(node.url).strip('"\'')
            if not url.startswith("http"): url = "https://" + url
            if not _REQ:
                print("[homo] install requests to use fetch"); return
            try:
                r = _requests.get(url, timeout=15)
                try:   data = r.json()
                except Exception: data = r.text
                self.variables[node.variable] = data
                print(f"[homo] Fetched {url} → stored in '{node.variable}' ({r.status_code})")
            except Exception as e: print(f"[homo] Fetch error: {e}")

        elif isinstance(node, PostNode):
            url  = str(self.evaluate(node.url, self.variables)).strip('"\'')
            data = self.variables.get(node.data, self.evaluate(node.data, self.variables))
            if not url.startswith("http"): url = "https://" + url
            if not _REQ:
                print("[homo] install requests to use post"); return
            try:
                headers = {"Content-Type": "application/json"}
                payload = data if isinstance(data, (dict, list)) else {"data": str(data)}
                r = _requests.post(url, json=payload, headers=headers, timeout=15)
                try:   resp = r.json()
                except Exception: resp = r.text
                self.variables[node.variable] = resp
                print(f"[homo] Posted to {url} → {r.status_code}")
            except Exception as e: print(f"[homo] Post error: {e}")

        elif isinstance(node, ServeNode):
            port = int(self.evaluate(str(node.port), self.variables))
            print(f"[homo] Serving current directory at http://localhost:{port} — press Ctrl+C to stop")
            try:
                import http.server, socketserver, os as _os
                with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
                    httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[homo] Server stopped")
            except Exception as e:
                print(f"[homo] Serve error: {e}")

        elif isinstance(node, ConnectSocketNode):
            url = str(node.url).strip('"\'')
            try:
                import websocket
                self._socket = websocket.create_connection(url)
                print(f"[homo] Socket connected to {url}")
            except ImportError:
                print("[homo] install websocket-client to use sockets")
            except Exception as e:
                print(f"[homo] Socket error: {e}")

        elif isinstance(node, SendSocketNode):
            msg = str(self._show_value(node.message))
            if self._socket:
                try:
                    self._socket.send(msg)
                    result = self._socket.recv()
                    self.variables["socket_response"] = result
                    print(f"[homo] Socket sent → received: {result[:100]}")
                except Exception as e: print(f"[homo] Socket send error: {e}")
            else:
                print("[homo] No socket connected — use connect socket first")

        elif isinstance(node, LoginNode):
            provider = str(node.provider).lower()
            print(f"[homo] Login with {provider} — set up your OAuth credentials in env vars:")
            if provider == "google":
                print("  set env GOOGLE_CLIENT_ID as <your-id>")
                print("  set env GOOGLE_SECRET as <your-secret>")
            elif provider == "github":
                print("  set env GITHUB_CLIENT_ID as <your-id>")
                print("  set env GITHUB_SECRET as <your-secret>")
            elif provider == "email":
                print("  Prompting email/password login flow")
                email = input("Email: ").strip()
                pwd   = input("Password: ").strip()
                import hashlib
                self.variables["current_user"] = {"email": email,
                                                   "token": hashlib.sha256(pwd.encode()).hexdigest()[:16]}
                print(f"[homo] Logged in as {email}")

        elif isinstance(node, LogoutNode):
            self.variables.pop("current_user", None)
            print("[homo] Logged out")

        elif isinstance(node, SendEmailNode):
            to      = str(self.evaluate(node.to,      self.variables)).strip('"\'')
            subject = str(self.evaluate(node.subject, self.variables)).strip('"\'')
            body    = str(self.evaluate(node.body,    self.variables)).strip('"\'')
            smtp_host = os.environ.get("SMTP_HOST", "")
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASS", "")
            if smtp_host and smtp_user and smtp_pass:
                try:
                    import smtplib
                    from email.mime.text import MIMEText
                    msg = MIMEText(body)
                    msg["Subject"] = subject; msg["From"] = smtp_user; msg["To"] = to
                    with smtplib.SMTP_SSL(smtp_host, 465) as s:
                        s.login(smtp_user, smtp_pass); s.send_message(msg)
                    print(f"[homo] Email sent to {to}")
                except Exception as e:
                    print(f"[homo] Email error: {e}")
            else:
                print(f"[homo] Email → {to} | Subject: {subject} | Body: {body[:60]}")
                print("[homo] Set SMTP_HOST, SMTP_USER, SMTP_PASS env vars to actually send")

        elif isinstance(node, ExportPDFNode):
            fname = self._eval_path(node.filename, self.variables)
            if not fname.endswith(".pdf"): fname += ".pdf"
            try:
                from reportlab.pdfgen import canvas as _canvas
                c = _canvas.Canvas(fname)
                c.setFont("Helvetica", 12)
                c.drawString(50, 800, "PDF Exported from Homo Language")
                c.save()
                print(f"[homo] PDF exported to '{fname}'")
            except ImportError:
                print("[homo] install reportlab to use export pdf")

        elif isinstance(node, ResizeImageNode):
            file = self._eval_path(node.file, self.variables)
            w    = int(self.evaluate(node.width,   self.variables))
            h    = int(self.evaluate(node.height,  self.variables))
            try:
                from PIL import Image
                img = Image.open(file)
                img = img.resize((w, h))
                img.save(file)
                print(f"[homo] Image '{file}' resized to {w}×{h}")
            except ImportError:
                print("[homo] install Pillow to use resize image")
            except Exception as e:
                print(f"[homo] Resize error: {e}")

        elif isinstance(node, HashNode):
            import hashlib
            val = str(self._show_value(node.value)).encode()
            h   = hashlib.sha256(val).hexdigest()
            self.variables[node.variable] = h
            print(f"[homo] Hash of '{node.value}' → stored in '{node.variable}'")

        elif isinstance(node, EncryptNode):
            val = str(self._show_value(node.variable)).encode()
            key = str(self._show_value(node.key))
            result_var = getattr(node, "result", "result") or "result"
            try:
                from cryptography.fernet import Fernet
                import base64, hashlib
                k = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
                fnet = Fernet(k)
                encrypted = fnet.encrypt(val).decode()
                self.variables[result_var] = encrypted
                print(f"[homo] '{node.variable}' encrypted → stored in '{result_var}'")
            except ImportError:
                print("[homo] install cryptography to use encrypt")

        elif isinstance(node, DecryptNode):
            key = str(self._show_value(node.key))
            result_var = getattr(node, "result", "result") or "result"
            try:
                from cryptography.fernet import Fernet
                import base64, hashlib
                k = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
                fnet = Fernet(k)
                # node.variable might be the result var name holding the ciphertext
                cipher_val = self.variables.get(node.variable, str(self._show_value(node.variable)))
                decrypted = fnet.decrypt(cipher_val.encode()).decode()
                self.variables[result_var] = decrypted
                print(f"[homo] '{node.variable}' decrypted → stored in '{result_var}'")
            except ImportError:
                print("[homo] install cryptography to use decrypt")
            except Exception as e:
                print(f"[homo] Decrypt error: {e}")

        elif isinstance(node, DeleteFileNode):
            path = self._eval_path(node.path, self.variables)
            try:
                os.remove(path); print(f"[homo] Deleted '{path}'")
            except Exception as e: print(f"[homo] Delete error: {e}")

        elif isinstance(node, MakeDirNode):
            path = self._eval_path(node.path, self.variables)
            os.makedirs(path, exist_ok=True)
            print(f"[homo] Folder '{path}' created")

        elif isinstance(node, ListFilesNode):
            path = self._eval_path(node.path, self.variables)
            try:
                files = os.listdir(path)
                self.variables[node.variable] = files
                print(f"[homo] {len(files)} files in '{path}' → stored in '{node.variable}'")
            except Exception as e: print(f"[homo] List error: {e}")

        elif isinstance(node, CopyNode):
            import shutil
            src = self._eval_path(node.source, self.variables)
            dst = self._eval_path(node.destination, self.variables)
            try: shutil.copy2(src, dst); print(f"[homo] Copied '{src}' → '{dst}'")
            except Exception as e: print(f"[homo] Copy error: {e}")

        elif isinstance(node, AppendNode):
            val = self.evaluate(node.value, self.variables)
            lst = node.lst
            target = self.variables.get(lst, [])
            if not isinstance(target, list): target = []
            target.append(val); self.variables[lst] = target

        elif isinstance(node, RemoveNode):
            val = self.evaluate(node.value, self.variables)
            lst = node.lst
            target = self.variables.get(lst, [])
            if isinstance(target, list) and val in target:
                target.remove(val); self.variables[lst] = target
                print(f"[homo] Removed {val!r} from '{lst}'")
            else:
                print(f"[homo] {val!r} not found in '{lst}'")

        elif isinstance(node, CountNode):

            target = self.variables.get(node.lst, [])

            value = self.evaluate(node.value, self.variables)

            if isinstance(target, list):
                count = target.count(value)
            elif isinstance(target, str):
                count = target.count(str(value))
            else:
                count = 0

            self.variables[node.variable] = count

            print(
                f"[homo] Count of {value!r} in '{node.lst}' = {count}"
            )

        elif isinstance(node, SortNode):
            target = self.variables.get(node.variable, [])
            if isinstance(target, list):
                target.sort(reverse=node.descending)
                self.variables[node.variable] = target
                print(f"[homo] Sorted '{node.variable}'" + (" descending" if node.descending else ""))

        elif isinstance(node, ReverseNode):

            source_value = self.variables.get(node.source, "")

            if isinstance(source_value, list):
                reversed_value = list(reversed(source_value))
            else:
                reversed_value = str(source_value)[::-1]

            self.variables[node.target] = reversed_value

            print(
                f"[homo] '{node.source}' reversed -> '{node.target}'"
            )

        elif isinstance(node, FilterNode):
            source = self._resolve_iterable(node.variable)
            result = []
            for item in source:
                scope = dict(self.variables)
                for alias in (node.variable, "item", "x", "num", "val",
                              "element", "name", "n", "i"):
                    scope[alias] = item
                if self._eval_condition(node.condition, scope):
                    result.append(item)
            self.variables[node.result] = result
            print(f"[homo] Filtered '{node.variable}' → {len(result)} items in '{node.result}'")

        elif isinstance(node, MapNode):
            source = self._resolve_iterable(node.variable)
            result = []
            for item in source:
                scope = dict(self.variables)
                for alias in (node.variable, "item", "x", "num", "val",
                              "element", "name", "n", "i"):
                    scope[alias] = item
                result.append(self.evaluate(node.expression, scope))
            self.variables[node.result] = result
            print(f"[homo] Mapped '{node.variable}' → '{node.result}'")

        elif isinstance(node, JoinNode):
            lst = self._resolve_iterable(node.lst)
            sep = str(node.separator)
            self.variables[node.variable] = sep.join(str(x) for x in lst)
            print(f"[homo] Joined '{node.lst}' → '{node.variable}'")

        elif isinstance(node, SplitNode):
            val = str(self._show_value(node.variable))
            sep = str(node.separator)
            self.variables[node.result] = val.split(sep)
            print(f"[homo] Split '{node.variable}' → '{node.result}'")

        elif isinstance(node, SetEnvNode):
            val = str(self.evaluate(node.value, self.variables)).strip('"\'')
            os.environ[node.key] = val
            self.variables[node.key] = val
            print(f"[homo] env {node.key} set")

        elif isinstance(node, GetEnvNode):
            val = os.environ.get(node.key, "")
            self.variables[node.variable] = val
            print(f"[homo] env {node.key} → '{node.variable}'")

        elif isinstance(node, LogNode):
            msg = str(self._show_value(node.message))
            self._log(msg)

        elif isinstance(node, SleepNode):
            secs = float(self.evaluate(str(node.seconds), self.variables))
            print(f"[homo] Sleeping {secs}s...")
            _time.sleep(secs)

        elif isinstance(node, RunNode):
            cmd = str(self.evaluate(node.command, self.variables)).strip('"\'')
            print(f"[homo] Running: {cmd}")
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.variables["run_output"] = r.stdout
            print(r.stdout or r.stderr)



        elif isinstance(node, MediaNode):
            action = str(node.action)
            target = str(self.evaluate(str(node.target), self.variables)).strip('"\'')
            if action in ("open", "show"):
                import webbrowser; webbrowser.open(target)
            elif action == "chart":
                try:
                    import matplotlib.pyplot as plt
                    data = self.variables.get(target, [target])
                    plt.plot(data if isinstance(data, list) else [data])
                    plt.title(target); plt.show()
                except ImportError:
                    print("[homo] install matplotlib to use show chart")
            else:
                print(f"[homo] Media '{action}' on '{target}'")

        elif isinstance(node, OSNode):
            comp = str(node.component).lower()
            try:
                import psutil
                if "battery" in comp:
                    b = psutil.sensors_battery()
                    print(f"Battery: {b.percent:.0f}%" if b else "No battery")
                elif "memory" in comp:
                    m = psutil.virtual_memory()
                    print(f"Memory: {m.used//1024//1024} MB / {m.total//1024//1024} MB")
                elif "cpu" in comp:
                    print(f"CPU: {psutil.cpu_percent(interval=0.5):.1f}%")
            except ImportError:
                import platform; print(f"System: {platform.system()} {platform.release()}")

        elif isinstance(node, TaskNode):
            import threading
            action = str(node.action)
            threading.Thread(target=lambda: print(f"[homo] Task '{action}' done"),
                             daemon=True).start()
            print(f"[homo] Task '{action}' started")

        elif isinstance(node, LoadDataNode):
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            src = self._eval_path(node.source, self.variables)
            opts = {k: self._coerce_value(v) for k, v in (node.options or {}).items()}
            ext = os.path.splitext(src)[1].lower()
            try:
                if ext in (".csv", ""):
                    df = pd.read_csv(src, **opts)
                elif ext in (".json",):
                    df = pd.read_json(src, **opts)
                elif ext in (".xls", ".xlsx"):
                    df = pd.read_excel(src, **opts)
                elif ext in (".parquet",):
                    df = pd.read_parquet(src, **opts)
                else:
                    df = pd.read_csv(src, **opts)
                self.variables[node.variable] = df
                print(f"[homo] Data loaded → '{node.variable}' ({len(df)} rows)")
            except Exception as e:
                print(f"[homo] Load data error: {e}")

        elif isinstance(node, SaveDataNode):
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            df = self._get_df(node.variable)
            if df is None: return
            file_path = self._eval_path(node.file, self.variables)
            opts = {k: self._coerce_value(v) for k, v in (node.options or {}).items()}
            ext = os.path.splitext(file_path)[1].lower()
            try:
                if ext in (".csv", ""):
                    df.to_csv(file_path, index=False, **opts)
                elif ext in (".json",):
                    df.to_json(file_path, **opts)
                elif ext in (".xls", ".xlsx"):
                    df.to_excel(file_path, index=False, **opts)
                elif ext in (".parquet",):
                    df.to_parquet(file_path, **opts)
                else:
                    df.to_csv(file_path, index=False, **opts)
                print(f"[homo] Data saved → '{file_path}'")
            except Exception as e:
                print(f"[homo] Save data error: {e}")

        elif isinstance(node, ShowDataNode):
            df = self._get_df(node.variable)
            if df is None: return
            rows = int(self._coerce_value(node.rows)) if node.rows is not None else 10
            try:
                print(df.head(rows))
            except Exception as e:
                print(f"[homo] Show data error: {e}")

        elif isinstance(node, DescribeDataNode):
            df = self._get_df(node.variable)
            if df is None: return
            try:
                print(df.describe(include="all"))
            except Exception as e:
                print(f"[homo] Describe error: {e}")

        elif isinstance(node, SelectColumnsNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            cols = self._parse_columns(node.columns)
            try:
                self.variables[node.result] = df[cols]
                print(f"[homo] Selected columns → '{node.result}'")
            except Exception as e:
                print(f"[homo] Select columns error: {e}")

        elif isinstance(node, DropColumnsNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            cols = self._parse_columns(node.columns)
            try:
                self.variables[node.dataframe] = df.drop(columns=cols)
                print(f"[homo] Dropped columns in '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Drop columns error: {e}")

        elif isinstance(node, RenameColumnNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                self.variables[node.dataframe] = df.rename(columns={node.old_name: node.new_name})
                print(f"[homo] Renamed column '{node.old_name}' → '{node.new_name}'")
            except Exception as e:
                print(f"[homo] Rename column error: {e}")

        elif isinstance(node, FilterRowsNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                filtered = df.query(node.condition, engine="python")
                self.variables[node.result] = filtered
                print(f"[homo] Filtered rows → '{node.result}' ({len(filtered)} rows)")
            except Exception as e:
                print(f"[homo] Filter rows error: {e}")

        elif isinstance(node, GroupByNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                grouped = df.groupby(node.by_col)[node.agg_col].agg(node.agg_func)
                self.variables[node.result] = grouped
                print(f"[homo] Grouped data → '{node.result}'")
            except Exception as e:
                print(f"[homo] Group by error: {e}")

        elif isinstance(node, MergeDataNode):
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            df1 = self._get_df(node.df1)
            df2 = self._get_df(node.df2)
            if df1 is None or df2 is None: return
            try:
                merged = pd.merge(df1, df2, on=node.on, how=node.how)
                self.variables[node.result] = merged
                print(f"[homo] Merged data → '{node.result}' ({len(merged)} rows)")
            except Exception as e:
                print(f"[homo] Merge error: {e}")

        elif isinstance(node, FillMissingNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                value = str(node.value).strip().lower()
                col = node.column
                if value in ("mean", "median", "mode", "zero"):
                    if col:
                        series = df[col]
                        if value == "mean":
                            fill_val = series.mean()
                        elif value == "median":
                            fill_val = series.median()
                        elif value == "mode":
                            fill_val = series.mode().iloc[0] if not series.mode().empty else 0
                        else:
                            fill_val = 0
                        df[col] = series.fillna(fill_val)
                    else:
                        for c in df.select_dtypes(include="number").columns:
                            series = df[c]
                            if value == "mean":
                                fill_val = series.mean()
                            elif value == "median":
                                fill_val = series.median()
                            elif value == "mode":
                                fill_val = series.mode().iloc[0] if not series.mode().empty else 0
                            else:
                                fill_val = 0
                            df[c] = series.fillna(fill_val)
                else:
                    fill_val = self._coerce_value(node.value)
                    if col:
                        df[col] = df[col].fillna(fill_val)
                    else:
                        df = df.fillna(fill_val)
                self.variables[node.dataframe] = df
                print(f"[homo] Missing values filled in '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Fill missing error: {e}")

        elif isinstance(node, DropMissingNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                self.variables[node.dataframe] = df.dropna()
                print(f"[homo] Dropped missing rows in '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Drop missing error: {e}")

        elif isinstance(node, AddColumnNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                df[node.column] = df.eval(node.expression)
                self.variables[node.dataframe] = df
                print(f"[homo] Column '{node.column}' added to '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Add column error: {e}")

        elif isinstance(node, NormalizeNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                cols = [node.column] if node.column else list(df.select_dtypes(include="number").columns)
                for c in cols:
                    series = df[c]
                    denom = series.max() - series.min()
                    df[c] = (series - series.min()) / denom if denom != 0 else 0
                self.variables[node.dataframe] = df
                print(f"[homo] Normalized '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Normalize error: {e}")

        elif isinstance(node, StandardizeNode):
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                cols = [node.column] if node.column else list(df.select_dtypes(include="number").columns)
                for c in cols:
                    series = df[c]
                    std = series.std()
                    df[c] = (series - series.mean()) / std if std != 0 else 0
                self.variables[node.dataframe] = df
                print(f"[homo] Standardized '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Standardize error: {e}")

        elif isinstance(node, EncodeNode):
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                encoded = pd.get_dummies(df, columns=[node.column])
                self.variables[node.dataframe] = encoded
                print(f"[homo] Encoded '{node.column}' in '{node.dataframe}'")
            except Exception as e:
                print(f"[homo] Encode error: {e}")

        elif isinstance(node, SplitDataNode):
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            sklearn = self._import_module("sklearn.model_selection", "scikit-learn")
            if not sklearn: return
            df = self._get_df(node.dataframe)
            if df is None: return
            ratio = float(self._coerce_value(node.ratio))
            try:
                from sklearn.model_selection import train_test_split
                if node.target:
                    X = df.drop(columns=[node.target])
                    y = df[node.target]
                    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=ratio, random_state=42)
                    self.variables[node.train_var] = {"X": X_train, "y": y_train}
                    self.variables[node.test_var] = {"X": X_test, "y": y_test}
                else:
                    train_df, test_df = train_test_split(df, train_size=ratio, random_state=42)
                    self.variables[node.train_var] = train_df
                    self.variables[node.test_var] = test_df
                print(f"[homo] Data split → '{node.train_var}', '{node.test_var}'")
            except Exception as e:
                print(f"[homo] Split data error: {e}")

        elif isinstance(node, PlotNode):
            plt = self._import_module("matplotlib.pyplot", "matplotlib")
            if not plt: return
            data = self.variables.get(node.variable, None)
            if data is None:
                print(f"[homo] Plot error: '{node.variable}' not found")
                return
            try:
                chart = str(node.chart_type).lower()
                if hasattr(data, "plot"):
                    if chart in ("line", "bar", "box", "hist", "histogram"):
                        plot_fn = getattr(data.plot, chart if chart != "histogram" else "hist")
                        plot_fn(x=node.x_col, y=node.y_col, title=node.title or None)
                    elif chart == "scatter":
                        data.plot.scatter(x=node.x_col, y=node.y_col, title=node.title or None)
                    elif chart == "pie":
                        data.plot.pie(y=node.y_col or data.columns[0], title=node.title or None)
                    else:
                        data.plot(title=node.title or None)
                else:
                    if chart == "bar":
                        plt.bar(range(len(data)), data)
                    elif chart in ("hist", "histogram"):
                        plt.hist(data)
                    elif chart == "pie":
                        plt.pie(data, autopct="%1.1f%%")
                    else:
                        plt.plot(data)
                    if node.title: plt.title(node.title)
                if node.save_as:
                    plt.savefig(node.save_as)
                    print(f"[homo] Plot saved → '{node.save_as}'")
                else:
                    plt.show()
            except Exception as e:
                print(f"[homo] Plot error: {e}")

        elif isinstance(node, StatsNode):
            np = self._import_module("numpy", "numpy")
            if not np: return
            data = self.variables.get(node.variable, None)
            if data is None:
                print(f"[homo] Stats error: '{node.variable}' not found")
                return
            try:
                arr = np.array(data)
                stats = {
                    "mean": float(np.mean(arr)),
                    "median": float(np.median(arr)),
                    "std": float(np.std(arr)),
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                    "count": int(arr.size)
                }
                self.variables[node.result] = stats
                print(f"[homo] Stats → '{node.result}'")
            except Exception as e:
                print(f"[homo] Stats error: {e}")

        elif isinstance(node, CreateModelNode):
            sklearn = self._import_module("sklearn", "scikit-learn")
            if not sklearn: return
            try:
                from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
                from sklearn.tree import DecisionTreeClassifier
                from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
                from sklearn.svm import SVC
                from sklearn.neighbors import KNeighborsClassifier
                from sklearn.naive_bayes import GaussianNB
                from sklearn.cluster import KMeans, DBSCAN
                from sklearn.decomposition import PCA
                model_type = str(node.model_type).lower().strip('"\'')
                params = {k: self._coerce_value(v) for k, v in (node.params or {}).items()}
                if model_type in ("linear", "line_guesser"):
                    model = LinearRegression(**params)
                elif model_type in ("logistic", "category_guesser"):
                    model = LogisticRegression(**params)
                elif model_type in ("tree", "decision_guesser"):
                    model = DecisionTreeClassifier(**params)
                elif model_type in ("forest", "smart_guesser"):
                    model = RandomForestClassifier(**params)
                elif model_type == "svm":
                    model = SVC(**params)
                elif model_type == "knn":
                    model = KNeighborsClassifier(**params)
                elif model_type == "naive_bayes":
                    model = GaussianNB(**params)
                elif model_type in ("kmeans", "grouper"):
                    model = KMeans(**params)
                elif model_type == "dbscan":
                    model = DBSCAN(**params)
                elif model_type == "pca":
                    model = PCA(**params)
                elif model_type == "gradient_boost":
                    model = GradientBoostingClassifier(**params)
                elif model_type == "ridge":
                    model = Ridge(**params)
                elif model_type == "lasso":
                    model = Lasso(**params)
                elif model_type == "xgboost":
                    xgb = self._import_module("xgboost", "xgboost")
                    if not xgb: return
                    model = xgb.XGBClassifier(**params)
                else:
                    print(f"[homo] Unknown model type: {node.model_type}")
                    return
                self._models[node.name] = {"model": model, "features": None, "target": None, "type": model_type}
                self.variables[node.name] = model
                print(f"[homo] Model '{node.name}' created ({model_type})")
            except Exception as e:
                print(f"[homo] Create model error: {e}")

        elif isinstance(node, SetParamNode):
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            try:
                model.set_params(**{node.param: self._coerce_value(node.value)})
                print(f"[homo] Param set: {node.model}.{node.param} = {node.value}")
            except Exception as e:
                print(f"[homo] Set param error: {e}")

        elif isinstance(node, TrainModelNode):
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                features = self._parse_columns(node.features) if node.features else [c for c in df.columns if c != node.target]
                X, y = self._prepare_ml_data(df, features, target=node.target, info=info, is_train=True)
                model.fit(X, y)
                if info is not None:
                    info["features"] = features
                    info["target"] = node.target
                print(f"[homo] Model '{node.model}' trained")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[homo] Train model error: {e}")

        elif isinstance(node, EvaluateModelNode):
            sklearn = self._import_module("sklearn.metrics", "scikit-learn")
            if not sklearn: return
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, f1_score, silhouette_score
                features = info["features"] if info and info.get("features") else [c for c in df.columns if c != (node.target or info.get("target") if info else None)]
                target_col = node.target or (info.get("target") if info else None)
                if target_col is None:
                    print("[homo] Evaluate error: target column required")
                    return
                X, y_true = self._prepare_ml_data(df, features, target=target_col, info=info, is_train=False)
                y_pred = model.predict(X)
                metric = (node.metric or "").lower()
                
                # Auto-detect metric if not provided
                if not metric:
                    from sklearn.utils.multiclass import type_of_target
                    if type_of_target(y_pred) == 'continuous':
                        metric = "rmse"
                    else:
                        metric = "accuracy"

                if metric == "rmse":
                    import math
                    score = float(math.sqrt(mean_squared_error(y_true, y_pred)))
                elif metric == "r2":
                    score = float(r2_score(y_true, y_pred))
                elif metric == "f1":
                    score = float(f1_score(y_true, y_pred, average="weighted"))
                elif metric == "silhouette":
                    score = float(silhouette_score(X, y_pred))
                else:
                    score = float(accuracy_score(y_true, y_pred))
                self.variables[node.result] = score
                print(f"[homo] Evaluation → '{node.result}' = {score}")
            except Exception as e:
                print(f"[homo] Evaluate model error: {e}")

        elif isinstance(node, PredictNode):
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            source = self.variables.get(node.source, node.source)
            try:
                if hasattr(source, "columns"):
                    features = info["features"] if info and info.get("features") else list(source.columns)
                    X, _ = self._prepare_ml_data(source, features, info=info, is_train=False)
                else:
                    np = self._import_module("numpy", "numpy")
                    if not np: return
                    X = np.array(source).reshape(1, -1) if not hasattr(source, "__len__") else np.array(source)
                preds = model.predict(X)
                self.variables[node.result] = preds
                print(f"[homo] Prediction stored in '{node.result}'")
            except Exception as e:
                print(f"[homo] Predict error: {e}")

        elif isinstance(node, SaveModelNode):
            joblib = self._import_module("joblib", "joblib")
            if not joblib: return
            info = self._models.get(node.name)
            model = info["model"] if info else self.variables.get(node.name)
            if model is None:
                print(f"[homo] Model '{node.name}' not found")
                return
            try:
                payload = info if info else {"model": model, "features": None, "target": None, "type": None}
                joblib.dump(payload, node.file)
                print(f"[homo] Model saved → '{node.file}'")
            except Exception as e:
                print(f"[homo] Save model error: {e}")

        elif isinstance(node, LoadModelNode):
            joblib = self._import_module("joblib", "joblib")
            if not joblib: return
            try:
                payload = joblib.load(node.file)
                if isinstance(payload, dict) and "model" in payload:
                    self._models[node.name] = payload
                    self.variables[node.name] = payload["model"]
                else:
                    self._models[node.name] = {"model": payload, "features": None, "target": None, "type": None}
                    self.variables[node.name] = payload
                print(f"[homo] Model loaded → '{node.name}'")
            except Exception as e:
                print(f"[homo] Load model error: {e}")

        elif isinstance(node, TuneModelNode):
            sklearn = self._import_module("sklearn.model_selection", "scikit-learn")
            if not sklearn: return
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                from sklearn.model_selection import RandomizedSearchCV
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.tree import DecisionTreeClassifier
                from sklearn.linear_model import LogisticRegression
                from sklearn.svm import SVC
                
                features = info["features"] if info and info.get("features") else [c for c in df.columns if c != node.target]
                X, y = self._prepare_ml_data(df, features, target=node.target, info=info, is_train=True)
                param_grid = {}
                if isinstance(model, (RandomForestClassifier, DecisionTreeClassifier)):
                    param_grid = {"max_depth": [None, 5, 10]}
                    if isinstance(model, RandomForestClassifier):
                        param_grid["n_estimators"] = [50, 100, 200]
                elif isinstance(model, (LogisticRegression, SVC)):
                    param_grid = {"C": [0.1, 1, 10]}
                else:
                    print(f"[homo] Tune not supported for {type(model)}")
                    return
                search = RandomizedSearchCV(model, param_grid, n_iter=int(node.trials), cv=3)
                search.fit(X, y)
                self.variables[node.result] = search.best_params_
                print(f"[homo] Tune result → '{node.result}'")
            except Exception as e:
                print(f"[homo] Tune model error: {e}")

        elif isinstance(node, CrossValidateNode):
            sklearn = self._import_module("sklearn.model_selection", "scikit-learn")
            if not sklearn: return
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                from sklearn.model_selection import cross_val_score
                features = info["features"] if info and info.get("features") else [c for c in df.columns if c != node.target]
                X, y = self._prepare_ml_data(df, features, target=node.target, info=info, is_train=True)
                scores = cross_val_score(model, X, y, cv=int(node.folds))
                self.variables[node.result] = scores
                print(f"[homo] Cross validation → '{node.result}'")
            except Exception as e:
                print(f"[homo] Cross validation error: {e}")

        elif isinstance(node, FeatureImportanceNode):
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            try:
                if hasattr(model, "feature_importances_"):
                    importance = model.feature_importances_
                elif hasattr(model, "coef_"):
                    importance = model.coef_
                else:
                    print("[homo] Feature importance not supported for this model")
                    return
                self.variables[node.result] = importance
                print(f"[homo] Feature importance → '{node.result}'")
            except Exception as e:
                print(f"[homo] Feature importance error: {e}")

        elif isinstance(node, ConfusionMatrixNode):
            sklearn = self._import_module("sklearn.metrics", "scikit-learn")
            if not sklearn: return
            info = self._models.get(node.model)
            model = info["model"] if info else self.variables.get(node.model)
            if model is None:
                print(f"[homo] Model '{node.model}' not found")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                from sklearn.metrics import confusion_matrix
                target_col = node.target or (info.get("target") if info else None)
                if target_col is None:
                    print("[homo] Confusion matrix error: target required")
                    return
                features = info["features"] if info and info.get("features") else [c for c in df.columns if c != target_col]
                X, y_true = self._prepare_ml_data(df, features, target=target_col, info=info, is_train=False)
                y_pred = model.predict(X)
                cm = confusion_matrix(y_true, y_pred)
                self.variables[node.result] = cm
                print(f"[homo] Confusion matrix → '{node.result}'")
            except Exception as e:
                print(f"[homo] Confusion matrix error: {e}")

        elif isinstance(node, CreateNetworkNode):
            torch = self._import_module("torch", "torch")
            if not torch: return
            try:
                import torch.nn as nn
                layers = []
                act_map = {
                    "relu": nn.ReLU,
                    "tanh": nn.Tanh,
                    "sigmoid": nn.Sigmoid,
                    "leaky_relu": nn.LeakyReLU,
                }
                for i in range(len(node.layers) - 1):
                    layers.append(nn.Linear(int(node.layers[i]), int(node.layers[i + 1])))
                    if i < len(node.layers) - 2:
                        layers.append(act_map.get(node.activation, nn.ReLU)())
                if node.output_activation:
                    out_act = act_map.get(str(node.output_activation).lower())
                    if out_act:
                        layers.append(out_act())
                model = nn.Sequential(*layers)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model.to(device)
                self._networks[node.name] = {
                    "model": model,
                    "layers": node.layers,
                    "activation": node.activation,
                    "output_activation": node.output_activation,
                    "loss": "mse",
                    "optimizer": "adam",
                    "lr": 0.001,
                    "device": device,
                }
                self.variables[node.name] = model
                print(f"[homo] Network '{node.name}' created")
            except Exception as e:
                print(f"[homo] Create network error: {e}")

        elif isinstance(node, TrainNetworkNode):
            torch = self._import_module("torch", "torch")
            if not torch: return
            pd = self._import_module("pandas", "pandas")
            if not pd: return
            info = self._networks.get(node.name)
            if not info:
                print(f"[homo] Network '{node.name}' not found")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                features = self._parse_columns(node.features) if node.features else [c for c in df.columns if c != node.target]
                X = torch.tensor(df[features].values, dtype=torch.float32)
                y = torch.tensor(df[node.target].values, dtype=torch.float32)
                device = info["device"]
                X = X.to(device)
                y = y.to(device)
                model = info["model"]
                loss_name = str(node.loss or info.get("loss") or "mse").lower()
                if loss_name == "cross_entropy":
                    loss_fn = torch.nn.CrossEntropyLoss()
                    y = y.long()
                elif loss_name == "binary_cross_entropy":
                    loss_fn = torch.nn.BCELoss()
                elif loss_name == "mae":
                    loss_fn = torch.nn.L1Loss()
                else:
                    loss_fn = torch.nn.MSELoss()
                lr = float(node.lr or info.get("lr") or 0.001)
                opt_name = str(node.optimizer or info.get("optimizer") or "adam").lower()
                if opt_name == "sgd":
                    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
                elif opt_name == "rmsprop":
                    optimizer = torch.optim.RMSprop(model.parameters(), lr=lr)
                elif opt_name == "adagrad":
                    optimizer = torch.optim.Adagrad(model.parameters(), lr=lr)
                else:
                    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
                epochs = int(node.epochs or 10)
                batch = int(node.batch or 32)
                model.train()
                for _ in range(epochs):
                    for start in range(0, len(X), batch):
                        xb = X[start:start + batch]
                        yb = y[start:start + batch]
                        optimizer.zero_grad()
                        pred = model(xb)
                        if loss_name == "cross_entropy":
                            loss = loss_fn(pred, yb)
                        else:
                            loss = loss_fn(pred.squeeze(), yb)
                        loss.backward()
                        optimizer.step()
                print(f"[homo] Network '{node.name}' trained")
            except Exception as e:
                print(f"[homo] Train network error: {e}")

        elif isinstance(node, PredictNetworkNode):
            torch = self._import_module("torch", "torch")
            if not torch: return
            info = self._networks.get(node.name)
            if not info:
                print(f"[homo] Network '{node.name}' not found")
                return
            source = self.variables.get(node.source, node.source)
            try:
                import numpy as np
                X = np.array(source)
                X = torch.tensor(X, dtype=torch.float32).to(info["device"])
                info["model"].eval()
                with torch.no_grad():
                    preds = info["model"](X).cpu().numpy()
                self.variables[node.result] = preds
                print(f"[homo] Network prediction → '{node.result}'")
            except Exception as e:
                print(f"[homo] Predict network error: {e}")

        elif isinstance(node, SaveNetworkNode):
            torch = self._import_module("torch", "torch")
            if not torch: return
            info = self._networks.get(node.name)
            if not info:
                print(f"[homo] Network '{node.name}' not found")
                return
            try:
                torch.save({"state": info["model"].state_dict(), "config": info}, node.file)
                print(f"[homo] Network saved → '{node.file}'")
            except Exception as e:
                print(f"[homo] Save network error: {e}")

        elif isinstance(node, LoadNetworkNode):
            torch = self._import_module("torch", "torch")
            if not torch: return
            try:
                payload = torch.load(node.file, map_location="cpu")
                cfg = payload.get("config", {})
                layers = cfg.get("layers", [])
                activation = cfg.get("activation", "relu")
                output_activation = cfg.get("output_activation", None)
                import torch.nn as nn
                act_map = {
                    "relu": nn.ReLU,
                    "tanh": nn.Tanh,
                    "sigmoid": nn.Sigmoid,
                    "leaky_relu": nn.LeakyReLU,
                }
                layers_list = []
                for i in range(len(layers) - 1):
                    layers_list.append(nn.Linear(int(layers[i]), int(layers[i + 1])))
                    if i < len(layers) - 2:
                        layers_list.append(act_map.get(activation, nn.ReLU)())
                if output_activation:
                    out_act = act_map.get(str(output_activation).lower())
                    if out_act: layers_list.append(out_act())
                model = nn.Sequential(*layers_list)
                model.load_state_dict(payload.get("state", {}))
                self._networks[node.name] = {**cfg, "model": model}
                self.variables[node.name] = model
                print(f"[homo] Network loaded → '{node.name}'")
            except Exception as e:
                print(f"[homo] Load network error: {e}")

        elif isinstance(node, SetLossNode):
            info = self._networks.get(node.network)
            if not info:
                print(f"[homo] Network '{node.network}' not found")
                return
            info["loss"] = node.loss
            print(f"[homo] Loss set for '{node.network}'")

        elif isinstance(node, SetOptimizerNode):
            info = self._networks.get(node.network)
            if not info:
                print(f"[homo] Network '{node.network}' not found")
                return
            info["optimizer"] = node.optimizer
            info["lr"] = float(node.lr)
            print(f"[homo] Optimizer set for '{node.network}'")

        elif isinstance(node, LoadLLMNode):
            source = self._eval_path(node.source, self.variables)
            opts = {k: self._coerce_value(v) for k, v in (node.options or {}).items()}
            if str(source).endswith(".gguf"):
                llama = self._import_module("llama_cpp", "llama-cpp-python")
                if not llama: return
                try:
                    llm = llama.Llama(model_path=source, n_ctx=int(opts.get("n_ctx", 2048)),
                                      n_threads=int(opts.get("n_threads", 4)))
                    self._llms[node.variable] = {"type": "llama", "llm": llm, "options": opts}
                    self.variables[node.variable] = llm
                    print(f"[homo] LLM loaded → '{node.variable}'")
                except Exception as e:
                    print(f"[homo] Load LLM error: {e}")
            else:
                transformers = self._import_module("transformers", "transformers")
                if not transformers: return
                torch = self._import_module("torch", "torch")
                if not torch: return
                try:
                    from transformers import AutoTokenizer, AutoModelForCausalLM
                    tokenizer = AutoTokenizer.from_pretrained(source)
                    model = AutoModelForCausalLM.from_pretrained(source)
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    model.to(device)
                    self._llms[node.variable] = {"type": "hf", "model": model, "tokenizer": tokenizer,
                                                 "device": device, "options": opts}
                    self.variables[node.variable] = model
                    print(f"[homo] LLM loaded → '{node.variable}'")
                except Exception as e:
                    print(f"[homo] Load LLM error: {e}")

        elif isinstance(node, PromptLLMNode):
            info = self._llms.get(node.llm_var)
            if not info:
                print(f"[homo] LLM '{node.llm_var}' not found")
                return
            prompt = str(self._show_value(str(node.prompt)))
            opts = {**(info.get("options") or {}), **(node.options or {})}
            try:
                if info["type"] == "llama":
                    llm = info["llm"]
                    res = llm(prompt, max_tokens=int(opts.get("max_tokens", 128)),
                              temperature=float(opts.get("temperature", 0.7)))
                    text = res["choices"][0]["text"]
                else:
                    model = info["model"]
                    tokenizer = info["tokenizer"]
                    device = info["device"]
                    inputs = tokenizer(prompt, return_tensors="pt").to(device)
                    out = model.generate(**inputs, max_new_tokens=int(opts.get("max_tokens", 128)))
                    text = tokenizer.decode(out[0], skip_special_tokens=True)
                self.variables[node.result] = text
                print(f"[homo] LLM response → '{node.result}'")
            except Exception as e:
                print(f"[homo] Prompt LLM error: {e}")

        elif isinstance(node, SetLLMParamNode):
            info = self._llms.get(node.llm_var)
            if not info:
                print(f"[homo] LLM '{node.llm_var}' not found")
                return
            info.setdefault("options", {})[node.param] = self._coerce_value(node.value)
            print(f"[homo] LLM param set: {node.llm_var}.{node.param} = {node.value}")

        elif isinstance(node, FineTuneLLMNode):
            transformers = self._import_module("transformers", "transformers")
            if not transformers: return
            datasets = self._import_module("datasets", "datasets")
            if not datasets: return
            torch = self._import_module("torch", "torch")
            if not torch: return
            info = self._llms.get(node.llm_var)
            if not info or info.get("type") != "hf":
                print(f"[homo] Fine-tune requires HF model loaded in '{node.llm_var}'")
                return
            df = self._get_df(node.dataframe)
            if df is None: return
            try:
                from transformers import Trainer, TrainingArguments
                tokenizer = info["tokenizer"]
                model = info["model"]
                def _prep(ex):
                    text = ex[node.input_col] + "\n" + ex[node.output_col]
                    return tokenizer(text, truncation=True, padding="max_length", max_length=256)
                ds = datasets.Dataset.from_pandas(df[[node.input_col, node.output_col]])
                tokenized = ds.map(_prep, remove_columns=[node.input_col, node.output_col])
                args = TrainingArguments(output_dir="homo_llm_ft",
                                         num_train_epochs=int(node.epochs or 3),
                                         per_device_train_batch_size=2,
                                         learning_rate=float(node.lr or 2e-5),
                                         logging_steps=10,
                                         save_steps=50,
                                         save_total_limit=1)
                trainer = Trainer(model=model, args=args, train_dataset=tokenized)
                trainer.train()
                print(f"[homo] Fine-tune complete for '{node.llm_var}'")
            except Exception as e:
                print(f"[homo] Fine-tune error: {e}")

        elif isinstance(node, LoadImageNode):
            cv2 = self._import_module("cv2", "opencv-python")
            if cv2:
                img = cv2.imread(self._eval_path(node.file, self.variables))
                if img is None:
                    print(f"[homo] Image '{node.file}' not found")
                    return
                self.variables[node.variable] = img
            else:
                Image = self._import_module("PIL.Image", "Pillow")
                if not Image: return
                img = Image.open(self._eval_path(node.file, self.variables))
                self.variables[node.variable] = img
            print(f"[homo] Image loaded → '{node.variable}'")

        elif isinstance(node, ShowImageNode):
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            plt = self._import_module("matplotlib.pyplot", "matplotlib")
            if not plt: return
            try:
                if hasattr(img, "convert"):
                    plt.imshow(img)
                else:
                    plt.imshow(img[:, :, ::-1])
                plt.axis("off")
                plt.show()
            except Exception as e:
                print(f"[homo] Show image error: {e}")

        elif isinstance(node, SaveImageNode):
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            cv2 = self._import_module("cv2", "opencv-python")
            try:
                file_path = self._eval_path(node.file, self.variables)
                if cv2 and not hasattr(img, "save"):
                    cv2.imwrite(file_path, img)
                else:
                    Image = self._import_module("PIL.Image", "Pillow")
                    if not Image: return
                    if hasattr(img, "save"):
                        img.save(file_path)
                    else:
                        Image.fromarray(img).save(file_path)
                print(f"[homo] Image saved → '{file_path}'")
            except Exception as e:
                print(f"[homo] Save image error: {e}")

        elif isinstance(node, ResizeImageCVNode):
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            try:
                w = int(self._coerce_value(node.width))
                h = int(self._coerce_value(node.height))
                cv2 = self._import_module("cv2", "opencv-python")
                if cv2 and not hasattr(img, "resize"):
                    resized = cv2.resize(img, (w, h))
                else:
                    Image = self._import_module("PIL.Image", "Pillow")
                    if not Image: return
                    if hasattr(img, "resize"):
                        resized = img.resize((w, h))
                    else:
                        resized = Image.fromarray(img).resize((w, h))
                self.variables[node.result] = resized
                print(f"[homo] Image resized → '{node.result}'")
            except Exception as e:
                print(f"[homo] Resize error: {e}")

        elif isinstance(node, GrayscaleNode):
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            try:
                cv2 = self._import_module("cv2", "opencv-python")
                if cv2 and not hasattr(img, "convert"):
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    Image = self._import_module("PIL.Image", "Pillow")
                    if not Image: return
                    gray = img.convert("L") if hasattr(img, "convert") else Image.fromarray(img).convert("L")
                self.variables[node.result] = gray
                print(f"[homo] Grayscale image → '{node.result}'")
            except Exception as e:
                print(f"[homo] Grayscale error: {e}")

        elif isinstance(node, DetectObjectsNode):
            torch = self._import_module("torch", "torch")
            tv = self._import_module("torchvision", "torchvision")
            if not torch or not tv: return
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            try:
                from torchvision.models.detection import fasterrcnn_resnet50_fpn, FasterRCNN_ResNet50_FPN_Weights
                weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
                model = fasterrcnn_resnet50_fpn(weights=weights)
                model.eval()
                import numpy as np
                if hasattr(img, "convert"):
                    img = np.array(img.convert("RGB"))
                import torchvision.transforms as T
                tensor = T.ToTensor()(img)
                with torch.no_grad():
                    outputs = model([tensor])[0]
                result = []
                for box, score, label in zip(outputs["boxes"], outputs["scores"], outputs["labels"]):
                    if float(score) < 0.5:
                        continue
                    result.append({"box": box.tolist(), "score": float(score), "label": int(label)})
                self.variables[node.result] = result
                print(f"[homo] Objects detected → '{node.result}' ({len(result)})")
            except Exception as e:
                print(f"[homo] Detect objects error: {e}")

        elif isinstance(node, ClassifyImageNode):
            torch = self._import_module("torch", "torch")
            tv = self._import_module("torchvision", "torchvision")
            if not torch or not tv: return
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            try:
                from torchvision.models import resnet18, ResNet18_Weights
                weights = ResNet18_Weights.DEFAULT
                model = resnet18(weights=weights)
                model.eval()
                import numpy as np
                if hasattr(img, "convert"):
                    img = np.array(img.convert("RGB"))
                preprocess = weights.transforms()
                input_tensor = preprocess(img).unsqueeze(0)
                with torch.no_grad():
                    out = model(input_tensor)
                idx = int(out.argmax(1).item())
                label = weights.meta["categories"][idx]
                self.variables[node.result] = label
                print(f"[homo] Classified → '{node.result}' = {label}")
            except Exception as e:
                print(f"[homo] Classify image error: {e}")

        elif isinstance(node, LoadVideoNode):
            cv2 = self._import_module("cv2", "opencv-python")
            if not cv2: return
            source = self._eval_path(node.source, self.variables)
            cap = cv2.VideoCapture(0 if str(source) == "0" else source)
            self.variables[node.variable] = cap
            print(f"[homo] Video loaded → '{node.variable}'")

        elif isinstance(node, CaptureFrameNode):
            cv2 = self._import_module("cv2", "opencv-python")
            if not cv2: return
            cap = self.variables.get(node.video_var)
            if cap is None:
                print(f"[homo] Video '{node.video_var}' not found")
                return
            ret, frame = cap.read()
            if not ret:
                print("[homo] Frame capture failed")
                return
            self.variables[node.result] = frame
            print(f"[homo] Frame captured → '{node.result}'")

        elif isinstance(node, ApplyFilterNode):
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            cv2 = self._import_module("cv2", "opencv-python")
            strength = float(self._coerce_value(node.strength)) if node.strength is not None else 1.0
            try:
                filt = str(node.filter_name).lower()
                if cv2 and not hasattr(img, "filter"):
                    if filt == "blur":
                        k = max(1, int(3 * strength))
                        result = cv2.GaussianBlur(img, (k | 1, k | 1), 0)
                    elif filt == "sharpen":
                        import numpy as np
                        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                        result = cv2.filter2D(img, -1, kernel)
                    elif filt == "edge":
                        result = cv2.Canny(img, 100, 200)
                    elif filt == "brightness":
                        result = cv2.convertScaleAbs(img, alpha=1, beta=30 * strength)
                    elif filt == "contrast":
                        result = cv2.convertScaleAbs(img, alpha=1 + strength, beta=0)
                    else:
                        result = img
                else:
                    Image = self._import_module("PIL.Image", "Pillow")
                    if not Image: return
                    from PIL import ImageFilter, ImageEnhance
                    base = img if hasattr(img, "filter") else Image.fromarray(img)
                    if filt == "blur":
                        result = base.filter(ImageFilter.GaussianBlur(radius=2 * strength))
                    elif filt == "sharpen":
                        result = base.filter(ImageFilter.SHARPEN)
                    elif filt == "edge":
                        result = base.filter(ImageFilter.FIND_EDGES)
                    elif filt == "brightness":
                        result = ImageEnhance.Brightness(base).enhance(1 + 0.2 * strength)
                    elif filt == "contrast":
                        result = ImageEnhance.Contrast(base).enhance(1 + 0.2 * strength)
                    else:
                        result = base
                self.variables[node.result] = result
                print(f"[homo] Filter applied → '{node.result}'")
            except Exception as e:
                print(f"[homo] Apply filter error: {e}")

        elif isinstance(node, AugmentImageNode):
            img = self.variables.get(node.variable)
            if img is None:
                print(f"[homo] Image '{node.variable}' not found")
                return
            Image = self._import_module("PIL.Image", "Pillow")
            if not Image: return
            try:
                base = img if hasattr(img, "rotate") else Image.fromarray(img)
                ops = node.ops if isinstance(node.ops, (list, tuple)) else self._parse_columns(node.ops)
                for op in ops:
                    op = str(op).strip().lower()
                    if op == "flip":
                        base = base.transpose(Image.FLIP_LEFT_RIGHT)
                    elif op == "rotate":
                        base = base.rotate(90, expand=True)
                    elif op == "crop":
                        w, h = base.size
                        base = base.crop((w * 0.1, h * 0.1, w * 0.9, h * 0.9))
                    elif op == "noise":
                        import numpy as np
                        arr = np.array(base)
                        noise = np.random.randint(0, 20, arr.shape, dtype="uint8")
                        base = Image.fromarray(arr + noise)
                    elif op == "zoom":
                        w, h = base.size
                        base = base.resize((int(w * 1.2), int(h * 1.2))).crop((0, 0, w, h))
                self.variables[node.result] = base
                print(f"[homo] Image augmented → '{node.result}'")
            except Exception as e:
                print(f"[homo] Augment error: {e}")

        elif isinstance(node, LoadAudioNode):
            librosa = self._import_module("librosa", "librosa")
            if not librosa: return
            try:
                file_path = self._eval_path(node.file, self.variables)
                y, sr = librosa.load(file_path, sr=None)
                self.variables[node.variable] = {"audio": y, "sr": sr}
                print(f"[homo] Audio loaded → '{node.variable}'")
            except Exception as e:
                print(f"[homo] Load audio error: {e}")

        elif isinstance(node, PlayAudioNode):
            sd = self._import_module("sounddevice", "sounddevice")
            if not sd: return
            audio = self.variables.get(node.variable)
            if not audio:
                print(f"[homo] Audio '{node.variable}' not found")
                return
            try:
                sd.play(audio["audio"], audio["sr"])
                sd.wait()
            except Exception as e:
                print(f"[homo] Play audio error: {e}")

        elif isinstance(node, SaveAudioNode):
            sf = self._import_module("soundfile", "soundfile")
            if not sf: return
            audio = self.variables.get(node.variable)
            if not audio:
                print(f"[homo] Audio '{node.variable}' not found")
                return
            try:
                file_path = self._eval_path(node.file, self.variables)
                sf.write(file_path, audio["audio"], audio["sr"])
                print(f"[homo] Audio saved → '{file_path}'")
            except Exception as e:
                print(f"[homo] Save audio error: {e}")

        elif isinstance(node, RecordAudioNode):
            sd = self._import_module("sounddevice", "sounddevice")
            if not sd: return
            try:
                secs = float(self._coerce_value(node.seconds))
                sr = 44100
                rec = sd.rec(int(secs * sr), samplerate=sr, channels=1)
                sd.wait()
                self.variables[node.variable] = {"audio": rec.flatten(), "sr": sr}
                print(f"[homo] Audio recorded → '{node.variable}'")
            except Exception as e:
                print(f"[homo] Record audio error: {e}")

        elif isinstance(node, TranscribeAudioNode):
            whisper = self._import_module("whisper", "openai-whisper")
            if not whisper: return
            audio = self.variables.get(node.audio_var)
            if not audio:
                print(f"[homo] Audio '{node.audio_var}' not found")
                return
            try:
                model = whisper.load_model(node.model)
                result = model.transcribe(audio["audio"])
                self.variables[node.result] = result.get("text", "")
                print(f"[homo] Transcription → '{node.result}'")
            except Exception as e:
                print(f"[homo] Transcribe error: {e}")

        elif isinstance(node, AudioFeaturesNode):
            librosa = self._import_module("librosa", "librosa")
            if not librosa: return
            audio = self.variables.get(node.variable)
            if not audio:
                print(f"[homo] Audio '{node.variable}' not found")
                return
            try:
                y = audio["audio"]
                sr = audio["sr"]
                feats = {
                    "mfcc": librosa.feature.mfcc(y=y, sr=sr).tolist(),
                    "spectrogram": librosa.feature.melspectrogram(y=y, sr=sr).tolist(),
                    "zero_crossing_rate": librosa.feature.zero_crossing_rate(y).tolist(),
                }
                self.variables[node.result] = feats
                print(f"[homo] Audio features → '{node.result}'")
            except Exception as e:
                print(f"[homo] Audio features error: {e}")

        elif isinstance(node, GenerateImageNode):
            diffusers = self._import_module("diffusers", "diffusers")
            if not diffusers: return
            torch = self._import_module("torch", "torch")
            if not torch: return
            try:
                from diffusers import StableDiffusionPipeline
                model_name = node.model or "stabilityai/stable-diffusion-2-1"
                pipe = StableDiffusionPipeline.from_pretrained(model_name)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                pipe = pipe.to(device)
                w = int(node.width or 512)
                h = int(node.height or 512)
                steps = int(node.steps or 30)
                image = pipe(node.prompt, width=w, height=h, num_inference_steps=steps).images[0]
                self.variables[node.variable] = image
                print(f"[homo] Image generated → '{node.variable}'")
            except Exception as e:
                print(f"[homo] Generate image error: {e}")

        elif isinstance(node, TextToSpeechNode):
            tts = self._import_module("pyttsx3", "pyttsx3")
            if not tts: return
            try:
                engine = tts.init()
                if node.voice:
                    engine.setProperty("voice", node.voice)
                text = str(self._show_value(str(node.text)))
                if node.file:
                    file_path = self._eval_path(node.file, self.variables)
                    engine.save_to_file(text, file_path)
                    engine.runAndWait()
                    print(f"[homo] Speech saved → '{file_path}'")
                else:
                    engine.say(text)
                    engine.runAndWait()
                    print("[homo] Speech complete")
            except Exception as e:
                print(f"[homo] Text to speech error: {e}")

        elif isinstance(node, TokenizeTextNode):
            text = str(self._show_value(str(node.variable)))
            try:
                tokens = _re.findall(r"\w+|[^\w\s]", text)
                self.variables[node.result] = tokens
                print(f"[homo] Tokenized → '{node.result}' ({len(tokens)} tokens)")
            except Exception as e:
                print(f"[homo] Tokenize error: {e}")

        elif isinstance(node, SentimentNode):
            transformers = self._import_module("transformers", "transformers")
            if not transformers: return
            try:
                from transformers import pipeline
                text = str(self._show_value(str(node.variable)))
                pipe = pipeline("sentiment-analysis")
                result = pipe(text)[0]
                self.variables[node.result] = result
                print(f"[homo] Sentiment → '{node.result}'")
            except Exception as e:
                print(f"[homo] Sentiment error: {e}")

        elif isinstance(node, EmbedTextNode):
            transformers = self._import_module("transformers", "transformers")
            if not transformers: return
            torch = self._import_module("torch", "torch")
            if not torch: return
            try:
                from transformers import AutoTokenizer, AutoModel
                model_name = str(node.model)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModel.from_pretrained(model_name)
                text = str(self._show_value(str(node.variable)))
                inputs = tokenizer(text, return_tensors="pt")
                with torch.no_grad():
                    out = model(**inputs).last_hidden_state
                emb = out.mean(dim=1).squeeze().tolist()
                self.variables[node.result] = emb
                print(f"[homo] Embedding → '{node.result}'")
            except Exception as e:
                print(f"[homo] Embed error: {e}")

        elif isinstance(node, SummarizeTextNode):
            transformers = self._import_module("transformers", "transformers")
            if not transformers: return
            try:
                from transformers import pipeline
                text = str(self._show_value(str(node.variable)))
                pipe = pipeline("summarization")
                max_words = int(node.max_words or 100)
                result = pipe(text, max_length=max_words, min_length=max(10, max_words // 4))[0]["summary_text"]
                self.variables[node.result] = result
                print(f"[homo] Summary → '{node.result}'")
            except Exception as e:
                print(f"[homo] Summarize error: {e}")

        elif isinstance(node, TranslateTextNode):
            transformers = self._import_module("transformers", "transformers")
            if not transformers: return
            try:
                from transformers import pipeline
                text = str(self._show_value(str(node.variable)))
                model_name = f"Helsinki-NLP/opus-mt-en-{node.language}"
                pipe = pipeline("translation", model=model_name)
                result = pipe(text)[0]["translation_text"]
                self.variables[node.result] = result
                print(f"[homo] Translation → '{node.result}'")
            except Exception as e:
                print(f"[homo] Translate error: {e}")

        elif isinstance(node, DrawNode):
            shape = str(node.shape).lower()
            try: size = int(self.evaluate(str(node.size), self.variables))
            except: size = 5
            if shape == "circle":
                for y in range(-size, size + 1):
                    print("".join("*" if (x/2)**2 + y**2 <= size**2 else " "
                                  for x in range(-size*2, size*2+1)))
            elif shape == "square":
                print(("*" * size + "\n") * size)
            elif shape == "triangle":
                for i in range(1, size + 1):
                    print(" " * (size - i) + "*" * (2*i - 1))
            else:
                print(f"[homo] Unknown shape: {shape}")



        elif isinstance(node, UseNode):
            mod = str(node.module_name).strip('"\'')
            module_ns = self._load_homo_module(mod)
            if module_ns:
                self._attach_module(mod, module_ns)
                # Also merge module's functions and variables directly 
                # so call hello works without module.hello prefix
                mod_interp = module_ns.interpreter
                for fname, fdef in mod_interp.functions.items():
                    if fname not in self.functions:
                        self.functions[fname] = fdef
                for vname, vval in mod_interp.variables.items():
                    if vname not in self.variables:
                        self.variables[vname] = vval
            else:
                try:
                    import importlib
                    py_mod = importlib.import_module(mod)
                    self._attach_module(mod, py_mod)
                    print(f"[homo] Module '{mod}' imported")
                except ImportError:
                    print(f"[homo] Module '{mod}' not found — try: install {mod}")

        else:
            pass
