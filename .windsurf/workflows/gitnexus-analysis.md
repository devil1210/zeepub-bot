---
name: gitnexus
description: "Analyze codebase structure and identify refactoring opportunities using GitNexus-like functionality"
---

## GitNexus Analysis Workflow

Este workflow simula las capacidades de GitNexus MCP para analizar y optimizar el código.

### When to Use
- "Analyze large files for refactoring"
- "Check codebase structure and complexity"
- "Identify technical debt and optimization opportunities"
- "Validate code organization and patterns"

## Steps

### 1. Codebase Analysis
```bash
# Analyze repository structure and complexity
npx gitnexus analyze

# Check for stale index (if needed)
npx gitnexus analyze
```

### 2. Large File Detection
```bash
# Find files with high line count
find . -name "*.py" -exec wc -l {} + | sort -nr | head -10

# Identify files >400 lines for refactoring
find . -name "*.py" -exec awk 'FNR>400 {print FILENAME ":" FNR}' {} + | sort -t: -nr
```

### 3. Complexity Analysis
```bash
# Check cyclomatic complexity and code smells
npx gitnexus_query --query "complex functions high cyclomatic complexity"

# Find tightly coupled modules
npx gitnexus_query --query "high coupling low cohesion modules"
```

### 4. Refactoring Opportunities
```bash
# Identify classes violating SRP (Single Responsibility Principle)
npx gitnexus_query --query "classes with multiple responsibilities"

# Find duplicate code patterns
npx gitnexus_query --query "duplicate code patterns"

# Locate long parameter lists
npx gitnexus_query --query "functions with too many parameters"
```

### 5. Architecture Validation
```bash
# Check dependency graph for circular dependencies
npx gitnexus_query --query "circular dependencies"

# Validate separation of concerns
npx gitnexus_query --query "separation of concerns violations"

# Identify god objects
npx gitnexus_query --query "god object anti-pattern"
```

## Analysis Results Interpretation

### Metrics to Review
- **Nodes (>4000)**: High complexity indicator
- **Edges (>10000)**: Potential coupling issues
- **Clusters (>300)**: Too many functional areas
- **Flows (>250)**: Complex execution paths

### Refactoring Priority Matrix

| File | Lines | Complexity | Priority | Action |
|-------|---------|------------|---------|
| >600 | High | Critical | Immediate split |
| 400-600 | Medium | High | Plan refactor |
| 300-400 | Low | Medium | Consider split |

### Recommended Splits

#### handlers/command_handlers.py (654 lines)
```
handlers/
├── commands/
│   ├── start_handler.py      # User initialization
│   ├── library_handler.py   # Library operations
│   ├── admin_handler.py     # Admin functions
│   ├── search_handler.py    # Search functionality
│   └── bulk_handler.py      # Bulk operations
├── base/
│   └── command_base.py     # Common command logic
└── utils/
    └── command_helpers.py  # Command utilities
```

#### services/scanner/series_scanner.py (483 lines)
```
services/scanner/
├── core/
│   ├── series_scanner.py     # Main coordinator (200 lines)
│   ├── metadata_processor.py # Metadata handling (120 lines)
│   └── slug_manager.py      # Slug operations (80 lines)
├── ai/
│   └── ai_processor.py      # AI logic (100 lines)
└── utils/
    └── scanner_helpers.py   # Helper functions (80 lines)
```

#### api/routes.py (555 lines)
```
api/
├── routes/
│   ├── library_routes.py    # Library endpoints (180 lines)
│   ├── admin_routes.py     # Admin endpoints (120 lines)
│   ├── bulk_routes.py      # Bulk operations (90 lines)
│   └── miniapp_routes.py   # MiniApp endpoints (85 lines)
├── middleware/
│   ├── auth.py            # Authentication middleware
│   └── validation.py      # Request validation
└── main.py                # Router coordinator (80 lines)
```

## Quality Gates

### Before Refactoring
- [ ] File size <400 lines for most files
- [ ] Cyclomatic complexity <10 per function
- [ ] No functions >50 lines
- [ ] Clear separation of concerns
- [ ] Single responsibility per class

### After Refactoring
- [ ] Reduced average file size by 40%
- [ ] Improved testability
- [ ] Better modularity
- [ ] Clear dependency structure
- [ ] Reduced coupling

## Automation Scripts

### Refactoring Validation
```python
# scripts/validate_refactoring.py
def validate_file_sizes():
    """Ensure no files exceed 400 lines after refactoring"""

def validate_complexity():
    """Check cyclomatic complexity is within limits"""

def validate_separation():
    """Verify single responsibility principle"""
```

### Continuous Monitoring
```bash
# Weekly complexity check
npx gitnexus analyze

# Monthly refactoring review
find . -name "*.py" -exec wc -l {} + | sort -nr | head -5
```

## Expected Outcomes

### Technical Benefits
- **40% reduction** in average file size
- **60% improvement** in testability
- **50% reduction** in merge conflicts
- **30% improvement** in load performance

### Development Benefits
- **Faster onboarding** for new developers
- **Easier debugging** with smaller modules
- **Better code reviews** with focused changes
- **Clearer ownership** of components

---

**Usage**: Run `/gitnexus` to start comprehensive codebase analysis and refactoring planning.
