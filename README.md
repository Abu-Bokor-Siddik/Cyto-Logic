# Cyto Logic

A compiler framework for synthetic biology that transforms high-level biological logic into genetic circuit representations.

> **Current Status:** Phase 1 and Phase 2 completed. Parser is under active development.

---

## Overview

Cyto Logic is an experimental compiler infrastructure designed for synthetic biology. The project explores a compiler-oriented approach to genetic circuit engineering, where biological logic is treated similarly to source code in a traditional programming language.

Instead of directly generating DNA sequences from user input, Cyto Logic separates the compilation process into independent stages. A logic expression is parsed into an Abstract Syntax Tree (AST), transformed into a Circuit Intermediate Representation (CIR), and later consumed by different backend systems such as simulation, optimization, and biological exporters.

The long-term goal is to build a reusable compiler platform that can support multiple biological programming languages and multiple output targets without redesigning the entire system.

---

## Motivation

Most synthetic biology software combines circuit design, simulation, and exporting into tightly coupled workflows. While this approach works for specific applications, it becomes difficult to extend as projects grow.

Cyto Logic follows a different philosophy.

The compiler frontend is responsible only for understanding biological logic. Every later stage works on a common intermediate representation rather than the original source code. This separation allows simulation, optimization, validation, and export systems to evolve independently.

The architecture is inspired by modern compiler infrastructures such as LLVM, adapted for synthetic biology.

---

## Current Development Status

| Phase | Status |
|--------|--------|
| Phase 1 • Compiler Frontend | Completed |
| Phase 2 • Circuit Intermediate Representation (CIR) | Completed |
| Phase 3 • Simulation Engine | Planned |
| Phase 4 • Optimization Engine | Planned |
| Phase 5 • Validation & Publication | Planned |

---

# Completed Features

## Phase 1

Compiler Frontend

- Lexer
- Token generation
- Token position tracking
- AST node definitions
- Parser framework
- Compiler architecture
- Error reporting foundation

## Phase 2

Intermediate Representation

- Circuit IR design
- IR Builder architecture
- Graph-based circuit representation
- Backend abstraction
- Compiler pipeline integration
- Modular system architecture

---

# Compiler Pipeline

```
Source Logic
      │
      ▼
 Lexer
      │
      ▼
 Token Stream
      │
      ▼
 Parser
      │
      ▼
 Abstract Syntax Tree
      │
      ▼
 Semantic Analysis
      │
      ▼
 Circuit IR
      │
      ├───────────────┐
      │               │
      ▼               ▼
Simulation      Optimization
      │               │
      └───────┬───────┘
              ▼
       Code Generators
              │
              ▼
 SBOL • BioBrick • DNA • JSON
```

Only the first two phases have been implemented at the moment.

---

# Architecture

Cyto Logic follows a layered compiler architecture.

```
                    Client Layer
                         │
                         ▼
                    API Gateway
                         │
                         ▼
                 Compiler Frontend
                         │
                         ▼
        Circuit Intermediate Representation (CIR)
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
      Simulation   Optimization   Code Generators
              │          │          │
              └──────────┼──────────┘
                         │
                         ▼
                    Persistence
```

Every major subsystem has a single responsibility.

The frontend never communicates directly with simulation or exporters.

All downstream systems consume the Circuit Intermediate Representation.

---

# Compiler Frontend

The frontend consists of three sequential stages.

## Lexer

The lexer converts raw source text into a sequence of tokens.

Each token stores

- Type
- Value
- Source position

---

## Parser

The parser consumes the token stream and constructs an Abstract Syntax Tree (AST).

The AST represents the logical structure of a biological circuit without including implementation-specific information.

---

## Semantic Analysis

The semantic analysis stage validates biologically meaningful rules.

Examples include

- Undefined proteins
- Invalid gate arity
- Incorrect circuit structure

---

# Circuit Intermediate Representation (CIR)

The Circuit IR is the core abstraction inside Cyto Logic.

Instead of allowing every backend to consume the AST directly, all compiler outputs are transformed into a graph-based intermediate representation.

Each CIR node stores

- Unique identifier
- Gate type
- Parent and child relationships
- Metadata
- Biological parameters (future)

The CIR acts as the single source of truth throughout the compiler.

---

# Project Philosophy

Cyto Logic is designed as reusable compiler infrastructure rather than a single-purpose application.

The architecture follows several principles.

- Stateless compiler stages
- Modular components
- Layer separation
- Replaceable backends
- Shared intermediate representation
- Independent simulation
- Independent optimization
- Extensible export system

---

# Planned Features

The following systems are part of the roadmap.

## Phase 3

Simulation Engine

- Hill kinetics
- ODE solver
- Time-series simulation
- Circuit visualization

---

## Phase 4

Optimization Engine

- Genetic Algorithm
- NSGA-II
- Multi-objective optimization
- Automatic parameter tuning

Objectives include

- Expression accuracy
- Metabolic burden
- Noise robustness

---

## Phase 5

Validation

- Repressilator benchmark
- SBOL validation
- Golden IR tests
- Biological verification

---

# Future Backends

The architecture has been designed to support multiple exporters.

Planned targets include

- SBOL
- BioBrick
- DNA sequences
- JSON
- SVG
- Laboratory protocols

Future backends can be added without changing the compiler frontend.

---

# Mathematical Foundation

Future simulation is based on deterministic Ordinary Differential Equations using Hill kinetics.

Optimization will use NSGA-II to search for parameter sets that balance

- Desired expression
- Metabolic burden
- Robustness

These mathematical models are specified in the architecture but have not yet been implemented.

---

# Testing Strategy

Current and planned testing includes

- Lexer unit tests
- Parser unit tests
- AST verification
- Golden IR snapshot testing
- Simulation benchmark validation
- Pareto front verification
- SBOL round-trip testing

---

# Repository Structure

```
cyto_logic/
│
├── compiler/
├── lexer/
├── parser/
├── ast/
├── cir/
├── backend/
├── frontend/
├── api/
├── tests/
├── docs/
└── ...
```

The structure may continue to evolve as additional compiler stages are implemented.

---

# Roadmap

- [x] Compiler architecture
- [x] Lexer
- [x] AST
- [x] Circuit IR architecture
- [x] Backend abstraction
- [ ] Semantic Analyzer
- [ ] Complete Parser
- [ ] Simulation Engine
- [ ] Optimization Engine
- [ ] SBOL Exporter
- [ ] DNA Exporter
- [ ] Plugin System
- [ ] Cloud Compiler
- [ ] Documentation

---

# Disclaimer

Cyto Logic is an active research project.

The current repository represents the compiler foundation. Many architectural components described in the documentation have been specified but are still under development.

The project is intended for research, experimentation, and learning in compiler design and synthetic biology.

---

# References

- LLVM Compiler Infrastructure
- SBOL (Synthetic Biology Open Language)
- iGEM Registry of Standard Biological Parts
- Hill Function Models
- NSGA-II Multi-objective Optimization
