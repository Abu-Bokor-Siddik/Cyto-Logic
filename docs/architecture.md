# Architecture

## Overview

Cyto Logic is a layered compiler for synthetic biology. Each stage transforms a
biological logic expression through progressively lower-level representations.

```
 Client Layer
     │
     ▼
 API Gateway
     │
     ▼
 Compiler Frontend  ─── Knowledge Base ───┐
     │                                     │
     ▼                                     │
 Circuit IR                                │
     │                                     │
     ▼                                     │
 Simulation / Optimization                 │
     │                                     │
     ▼                                     │
 Code Generators                           │
     │                                     │
     ▼                                     │
 Compiled Artifacts ◄──────────────────────┘
```

## 7-Block Pipeline

### 1. Client Layer (frontend/ React SPA)
Provides the user interface for:
- Visual circuit design (node-graph editor)
- Logic expression input
- Result visualization (simulation plots, DNA sequences, SBOL exports)

### 2. API Gateway (backend/app.py — Flask)
RESTful API with endpoints for:
- `/api/compile` — compile logic expression to CircuitIR
- `/api/simulate` — run ODE simulation
- `/api/optimize` — multi-objective parameter optimization
- `/api/export/sbol`, `/api/export/genbank`, `/api/export/dna`, `/api/export/svg`
- `/api/parts` — list available parts from the Knowledge Base
- `/api/health` — health check

### 3. Compiler Frontend
Lexer → Parser → Semantic Analyzer → IR Builder (Gate Mapper)

#### Lexer (`compiler/lexer.py`)
Tokenizes raw source text into `Token` objects. Recognizes keywords (`IF`, `NOT`,
`AND`, `OR`), identifiers (protein names), symbols (`(`, `)`, `->`).

#### Parser (`compiler/parser.py`)
Consumes tokens and produces an Abstract Syntax Tree (AST) using recursive descent.
AST node types: `Circuit`, `NotGate`, `AndGate`, `OrGate`, `ProteinNode`.

#### Semantic Analyzer (`compiler/semantic.py`)
Walks the AST to validate biological rules:
- Undefined proteins and outputs
- Null inputs to gates
- Deeply nested circuits (depth limit)
- Duplicate warnings

Returns a list of `SemanticMessage` objects (severity: error/warning/info).

#### IR Builder (`compiler/ir_builder.py`)
Transforms the AST into a `CircuitIR` — a graph-based intermediate representation.
Each node has a unique ID, label, type, and metadata. Edges represent regulatory
connections. Parts (DNA sequences) are attached to gates using data from the
Knowledge Base.

### 4. Circuit IR (`compiler/cir.py`)
The core data structure `CircuitIR` with fields:
- `logic_statement`: Original source
- `output_protein`: Target reporter
- `_nodes`: dict of `node_id → {label, type, ...}`
- `_edges`: list of `(source_id, target_id)`
- `_parts`: list of `{id, role, info}`

### 5. Simulation / Optimization

#### Simulation Engine (`compiler/simulation/`)
- **Models** (`models.py`): Hill kinetics functions (activator, repressor, OR, AND, degradation)
- **ODE System** (`ode_system.py`): Builds a system of ODEs from a CircuitIR
- **Solver** (`solver.py`): RK4 integrator with configurable step size

#### Optimization Engine (`compiler/optimization/`)
- **NSGA-II** (`nsga2.py`): Multi-objective genetic algorithm
- **Objectives** (`objectives.py`): Expression accuracy, metabolic burden, noise robustness

### 6. Code Generators (`compiler/backends/`)

| Backend | Output | Description |
|---------|--------|-------------|
| **SBOL** (`sbol_backend.py`) | XML | SBOL-compliant genetic design export |
| **GenBank** (`genbank_backend.py`) | Plain text | GenBank flat file format |
| **DNA** (`dna_backend.py`) | FASTA | Concatenated DNA sequence FASTA |
| **SVG** (`svg_backend.py`) | SVG | Visual circuit diagram |
| **Simulation** (`simulation_backend.py`) | JSON | Time-series simulation results |

### 7. Compiled Artifacts
Final output formats delivered to the client:
- JSON circuit representation
- SBOL XML
- GenBank flat file
- FASTA sequence
- SVG diagram
- Simulation time-series data

## Knowledge Base (`backend/data/parts.json`)

The Knowledge Base is a structured JSON file that decouples all BioBrick part
data from the compiler code. It is loaded at startup by `knowledge_base.py` and
exposed through `parts_db.py` for backward compatibility.

### Schema
Each part entry includes:
- `id`: iGEM part identifier
- `role`: Biological role (promoter, RBS, CDS, terminator, inducer, etc.)
- `name`: Human-readable name
- `description`: Functional description
- `sequence`: DNA sequence (empty for small molecules)
- `chassis_compatibility`: List of valid chassis organisms
- `parameters`: Numeric parameters (strength, Kd, Hill coefficient, etc.)

### Data Sections
- **parts**: Unified registry of all known BioBrick parts
- **gates**: Logical gate definitions (NOT, AND, OR, NAND, NOR)
- **biomolecules**: Input molecules and regulatory proteins
- **reporters**: Fluorescent and enzymatic reporter proteins
- **additional_parts**: Supplementary parts (terminators, alternative promoters)
- **regulatory_map**: Regulatory interaction rules (repression, activation)

## Plugin System

### Plugin Manager (`compiler/plugin/manager.py`)
Singleton that discovers and loads plugins. Hooks fire at pipeline stages:
`before_compile`, `after_compile`, `before_simulate`, `after_simulate`,
`before_optimize`, `after_optimize`, `before_export`, `after_export`.

Plugins can be loaded via the `CYTOLOGIC_PLUGINS` environment variable
(comma-separated Python module paths).

### Built-in Plugins
- **TimingPlugin**: Records elapsed time for compile/simulate/optimize stages.

## Persistence Layer

The Persistence layer (future work) will provide:
- Caching of compiled circuits
- User session management
- Circuit design history
- Export artifact storage

## Data Flow

```
User Input
    │
    ▼
app.py (Flask API)
    │
    ├── /api/compile  → CompilerPipeline → CircuitIR → JSON
    ├── /api/simulate → CompilerPipeline → SimulationBackend → JSON
    ├── /api/optimize → CompilerPipeline → OptimizationRunner → JSON
    ├── /api/export/sbol → SBOLBackend → XML
    ├── /api/export/svg  → SVGBackend → SVG
    ├── /api/export/dna  → DNABackend → FASTA
    ├── /api/parts   → Knowledge Base → JSON
    └── /api/health  → OK → JSON
```