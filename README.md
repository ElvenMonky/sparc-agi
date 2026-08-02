# Spark of AGI

Synthetic Puzzle Generation for ARC-AGI.

## Install

```bash
pip install -e .
```

## Workflow

Phase 1: Generate Puzzle specification
* generate input:
* append transformations
* validate that all outputs are used and final output is object
* Save multiple specifications to file

Phase 2: Compile Puzzle specification
* Load from file
* Trace input specification via transformations to get intermediate and final output specifications
* Describe puzzle solution (describe input + describe transformations)
* store output specs and solution description on puzzle spec

Phase 3: Generate Puzzle Instance
* Instantiate cache items
* Generate random palette
* Generate samples (input instance, intermadiate and final output instances per transfromation)
* Copy description
* Save puzzle instance to file

Phase 4: render and validate puzzle instance

Future: improve description using LM, etc.