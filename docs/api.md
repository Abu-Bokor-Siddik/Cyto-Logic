# API Reference

## Endpoints

### `POST /api/compile`

Compile a biological logic expression into a CircuitIR.

**Request:**
```json
{
  "logic": "IF (aTc AND NOT AraC) -> GFP"
}
```

Alternatively, provide a graph:
```json
{
  "nodes": [{"id": "1", "data": {"label": "aTc", "type": "INPUT"}}],
  "edges": [{"source": "1", "target": "2"}]
}
```

**Response:**
```json
{
  "success": true,
  "logic": "IF (aTc AND NOT AraC) -> GFP",
  "parts": [...],
  "complexity_score": 5,
  "output_protein": "GFP",
  "graph": {"nodes": [...], "edges": [...]},
  "semantic_messages": [...]
}
```

### `POST /api/simulate`

Run time-series simulation on a compiled circuit.

**Request:**
```json
{
  "logic": "IF aTc -> GFP",
  "inputs": {"aTc": 10.0},
  "t_span": [0, 100],
  "dt": 0.5
}
```

**Response:**
```json
{
  "times": [0, 0.5, 1.0, ...],
  "species": ["aTc", "GFP"],
  "trajectories": {"aTc": [...], "GFP": [...]},
  "num_points": 201,
  "success": true
}
```

### `POST /api/optimize`

Run NSGA-II multi-objective optimization to tune kinetic parameters.

**Request:**
```json
{
  "logic": "IF aTc -> GFP",
  "inputs": {"aTc": 10.0},
  "target_output": 10.0,
  "pop_size": 30,
  "generations": 10
}
```

**Response:**
```json
{
  "pareto_front_size": 10,
  "pareto_objectives": [
    {"expression_accuracy": 0.5, "metabolic_burden": 12.3, "noise_robustness": 1.2}
  ],
  "best_parameter_set": [
    {"species": "GFP", "vmax": 8.2, "kd": 1.1, "hill_n": 2.3, "delta": 0.4}
  ],
  "generations_completed": 10,
  "success": true
}
```

### `POST /api/export/sbol`

Export circuit as SBOL XML.

**Request:**
```json
{
  "parts": [{"id": "BBa_E0040", "role": "CDS", "info": "GFP"}],
  "name": "my_circuit"
}
```

**Response:** `application/xml` file download.

### `POST /api/export/dna`

Export circuit as FASTA DNA sequences.

**Request:**
```json
{
  "logic": "IF aTc -> GFP",
  "name": "my_circuit"
}
```

Or with raw parts:
```json
{
  "parts": [{"id": "BBa_E0040", "role": "CDS", "info": "GFP"}]
}
```

**Response:** `text/plain` FASTA file download.

### `POST /api/export/svg`

Export circuit as an SVG diagram.

**Request:**
```json
{
  "logic": "IF aTc -> GFP",
  "name": "my_circuit"
}
```

Or with raw parts:
```json
{
  "parts": [{"id": "BBa_E0040", "role": "CDS", "info": "GFP"}],
  "name": "my_circuit"
}
```

**Response:** `image/svg+xml` file download. Max 500 parts per request.

### `GET /api/parts`

List all known biological parts.

**Response:**
```json
{
  "gates": ["aTc", "AraC", "TetR", "LacI", "cI", "GFP", "RFP"],
  "count": 7
}
```

### `GET /api/health`

Health check.

**Response:**
```json
{
  "status": "ok",
  "service": "cyto-logic-backend",
  "version": "0.1.0"
}
```
