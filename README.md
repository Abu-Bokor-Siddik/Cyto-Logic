# Cyto Logic

An experimental compiler for synthetic biology.

## Overview

Cyto Logic explores a compiler-first approach to genetic circuit design.
Instead of manually selecting biological parts, the user describes
circuit behavior with a small domain-specific language (DSL). The
compiler parses the program, builds an Abstract Syntax Tree (AST), maps
logic gates to biological components, and exports the design as an SBOL
document.

Cyto Logic is the first compiler being developed as part of the larger
**Cyto OS** project.

## Pipeline

``` text
Logic DSL
    │
    ▼
Lexer
    │
    ▼
Parser
    │
    ▼
AST
    │
    ▼
Gate Mapper
    │
    ▼
BioBrick Mapping
    │
    ▼
SBOL Export
```

## Example

Input

``` text
IF (aTc AND AraC) -> GFP
```

## Grammar

``` text
program      ::= IF expression -> IDENTIFIER

expression   ::= term
               | term OR expression

term         ::= factor
               | factor AND term

factor       ::= IDENTIFIER
               | NOT factor
               | ( expression )
```

## Current Features

-   Lexer
-   Recursive descent parser
-   AST generation
-   Logic gate mapping
-   BioBrick database
-   SBOL export
-   React Flow visual editor
-   REST API backend

## Project Structure

``` text
frontend/
├── components/
├── api/
└── App.jsx

backend/
├── compiler/
│   ├── lexer.py
│   ├── parser.py
│   ├── ast_node.py
│   ├── gate_mapper.py
│   ├── parts_db.py
│   └── sbol_exporter.py
└── app.py
```

## Roadmap

### Phase 1

-   [x] Compiler frontend
-   [x] AST
-   [x] Gate mapping
-   [x] SBOL export
-   [x] Visual editor

### Phase 2

-   [ ] Circuit IR
-   [ ] Semantic analysis
-   [ ] Better diagnostics

### Phase 3

-   [ ] ODE simulation
-   [ ] Parameter estimation

### Phase 4

-   [ ] Optimization engine
-   [ ] Automatic circuit synthesis

### Phase 5

-   [ ] Cyto OS integration

## Long-Term Vision

Cyto Logic is intended to become one module inside **Cyto OS**, where
biological systems can be designed, simulated, optimized, and exported
through a unified compiler pipeline.
