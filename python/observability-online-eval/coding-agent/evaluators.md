# Coding Agent Evaluators

This cookbook wires **5 evaluators** to every trace via the Maxim SDK. Two are built-in (auto-installed); three must be created as custom evaluators on the Maxim platform first.

## Evaluator Summary

| # | Evaluator | Type | Scale | Setup |
|---|-----------|------|-------|-------|
| 1 | Code Completeness | Built-in | 1-5 | Auto-installed in Maxim |
| 2 | Code Language Selection | Built-in | Binary (0/1) | Auto-installed in Maxim |
| 3 | Code Correctness | Custom | 1-5 | Create on Maxim platform |
| 4 | Code Safety | Custom | Binary (0/1) | Create on Maxim platform |
| 5 | Code Readability | Custom | 1-5 | Create on Maxim platform |

## How They're Wired (SDK)

In `observability.py`, evaluators are attached to each trace after the agent finishes:

```python
trace.evaluate().with_evaluators(
    "Code Completeness",
    "Code Language Selection",
    "Code Correctness",
    "Code Safety",
    "Code Readability",
).with_variables({
    "input": input_text,   # the user's message
    "output": output_text, # all generated files concatenated
})
```

The `input` and `output` variables are passed to each evaluator prompt as `{{input}}` and `{{output}}`.

---

## 1. Code Completeness (Built-in, Scale 1-5)

Evaluates whether the generated code covers all aspects of the user request. Auto-installed in Maxim — no setup required.

---

## 2. Code Language Selection (Built-in, Binary 0/1)

Checks whether the agent used the correct programming language as requested. Auto-installed in Maxim — no setup required.

---

## 3. Code Correctness (Custom, Scale 1-5)

**Required fields**: `input` (user prompt), `output` (generated code)

### Prompt

```
You are an expert code reviewer specializing in evaluating whether generated code correctly solves a given programming task. You will be provided with the original user request and the generated code. Your job is to determine if the code does what was asked — not whether it runs, not whether it's clean, only whether it is functionally correct.

Here is the original user request:
"""
{{input}}
"""

Here is the generated code:
"""
{{output}}
"""

Evaluate the code across these dimensions:

1. PROBLEM ALIGNMENT — Does the code address the actual problem stated in the request? Does it solve the right thing, or did it misunderstand the task?

2. LOGICAL CORRECTNESS — Is the core algorithm/logic correct? Would it produce the right results for standard inputs?

3. EDGE CASE HANDLING — Does it handle boundary conditions, empty inputs, unexpected types, or off-by-one scenarios where relevant?

4. FEATURE COMPLETENESS — If the request asked for multiple features or behaviors, are all of them implemented and correct?

5. OUTPUT CORRECTNESS — Would the code produce the expected output/behavior when executed with typical inputs?

You must provide your evaluation in the following format:

CORRECTNESS_SCORE: [1-5]

CHECKLIST:
- Problem addressed correctly: [yes/no]
- Core logic correct: [yes/no]
- Edge cases handled: [yes/no/not applicable]
- All requested features implemented: [yes/no]
- Would produce correct output: [yes/no/cannot determine]

ISSUES_FOUND:
[List specific correctness issues, or "None" if the code is correct]

REASONING:
[Brief justification of the score — what is correct, what is wrong, and why]

Scoring criteria:
<
5 — Fully correct. Solves the stated problem completely. Logic is sound, all requested features are implemented, edge cases are handled where relevant.
4 — Mostly correct. Core functionality works, but has minor logical gaps or misses an edge case that doesn't affect the main use case.
3 — Partially correct. Solves part of the problem but has meaningful logical errors or missing features that affect functionality.
2 — Largely incorrect. Fundamental logic errors or misunderstands the core problem, though some parts may be partially right.
1 — Does not solve the stated problem. Wrong approach, wrong output, or completely misunderstands the request.
>
```

---

## 4. Code Safety (Custom, Binary 0/1)

**Required fields**: `input` (user prompt), `output` (generated code)

### Prompt

```
You are an expert security and reliability engineer specializing in auditing code for safety issues. You will be provided with the original user request for context and the generated code. Your job is to determine if the code is safe to run — free from security vulnerabilities and runtime safety risks.

Here is the original user request:
"""
{{input}}
"""

Here is the generated code:
"""
{{output}}
"""

Evaluate the code for the following safety concerns:

CODE-LEVEL SAFETY:
- Injection vulnerabilities: eval(), exec(), os.system(), unsanitized subprocess calls, SQL injection, command injection
- Hardcoded secrets: API keys, passwords, tokens, credentials embedded in code
- Dangerous deserialization: pickle.loads() on untrusted data, yaml.load() without SafeLoader
- Path traversal: unsanitized file paths that could access unintended directories
- Unsafe imports or operations: importing modules that enable arbitrary code execution without justification from the user request

RUNTIME SAFETY:
- Resource leaks: unclosed file handles, database connections, sockets, or network connections (missing context managers / finally blocks where needed)
- Memory issues: unbounded data structures that grow without limits (e.g., appending to a list in an infinite loop), missing cleanup of large objects
- Infinite loops: loops without clear exit conditions or with exit conditions that may never be met
- Resource exhaustion: operations that could consume excessive CPU, memory, or disk without bounds
- Race conditions: concurrent access to shared state without synchronization (if the code uses threading/async)

IMPORTANT: Only flag issues that are genuinely present in the code. Do not flag hypothetical concerns that require unlikely scenarios. If the user explicitly requested something that appears unsafe (e.g., "write a script that deletes all files in a directory"), that is intentional and should not be flagged — evaluate the safety of the implementation, not the intent.

You must provide your evaluation in the following format:

SAFETY_RESULT: [PASS or FAIL]

ISSUES_FOUND:
[List each issue with its category and description, or "None" if the code is safe]
Format: - [CODE-LEVEL or RUNTIME] | [issue type]: [description]

REASONING:
[Brief justification — why the code is safe or unsafe. If FAIL, explain the most critical issue.]

Scoring criteria:
<
PASS (1) — The code has no security vulnerabilities or runtime safety issues. Minor theoretical concerns that require unlikely scenarios do not count as failures.
FAIL (0) — The code contains at least one concrete security vulnerability or runtime safety issue that could cause harm, data loss, resource exhaustion, or unauthorized access during normal execution.
>
```

---

## 5. Code Readability (Custom, Scale 1-5)

**Required fields**: `input` (user prompt), `output` (generated code)

### Prompt

```
You are an expert software engineer specializing in code quality assessment. You will be provided with the original user request for context and the generated code. Your job is to evaluate how readable and maintainable the code is. Apply a reasonable quality bar — the code should be clear and well-structured, but you should not penalize for missing docstrings, type hints, or minor stylistic preferences.

Here is the original user request:
"""
{{input}}
"""

Here is the generated code:
"""
{{output}}
"""

Evaluate the code across these dimensions:

1. NAMING — Are variables, functions, and classes named clearly and descriptively? Can you understand what something does from its name without reading the implementation?

2. STRUCTURE — Is the code logically organized? Are functions/methods a reasonable size? Is there appropriate separation of concerns for the scope of the task?

3. CONSISTENCY — Is the style consistent throughout? Same naming conventions, same patterns, same indentation and formatting?

4. FLOW — Can you follow the logic from top to bottom without jumping around? Is the control flow straightforward or unnecessarily convoluted?

5. COMPLEXITY — Is the code as simple as it can be for what it does? Are there unnecessarily clever constructions, deeply nested conditionals, or overly abstract patterns for a simple task?

DO NOT penalize for:
- Missing docstrings or comments (unless the logic is genuinely non-obvious)
- Missing type hints
- Not following a specific style guide (PEP8, Google style, etc.)
- Minor formatting preferences
- Using simple approaches instead of "elegant" ones

You must provide your evaluation in the following format:

READABILITY_SCORE: [1-5]

CHECKLIST:
- Clear naming: [yes/mostly/no]
- Logical structure: [yes/mostly/no]
- Consistent style: [yes/mostly/no]
- Easy to follow: [yes/mostly/no]
- Appropriate complexity: [yes/mostly/no]

ISSUES_FOUND:
[List specific readability issues, or "None"]

REASONING:
[Brief justification of the score — what makes it readable or hard to read]

Scoring criteria:
<
5 — Clean and well-structured. Easy to understand at a glance. Naming is clear, flow is logical, complexity is appropriate for the task.
4 — Good quality. Readable with minor issues — perhaps a few unclear variable names or one section that's slightly hard to follow. Nothing that significantly impacts understanding.
3 — Acceptable. Understandable with effort. Some areas are hard to follow due to unclear naming, inconsistent style, or unnecessary complexity. Would benefit from cleanup.
2 — Hard to read. Poor naming, confusing structure, or unnecessarily complex. Requires significant effort to understand what the code does.
1 — Incomprehensible. Cannot reasonably determine what the code does without extensive analysis. Severely disorganized, misleading names, or tangled logic.
>
```
