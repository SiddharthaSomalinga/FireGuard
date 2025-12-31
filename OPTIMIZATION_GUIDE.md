# FireGuard Optimization Guide for Developers

## Quick Start for Understanding Changes

### 1. Global Session Management (fdi.py)
```python
# ✅ USE THIS: Reuses connection pool
session = _get_session()
openmeteo = openmeteo_requests.Client(session=session)
```

**Why:** Each HTTP request can reuse TCP connections, reducing overhead.

---

### 2. Prolog Fact Management (fdi.py)
```python
# ❌ OLD: Complex regex operations
pattern = rf"area_details\({area_name},.*?\)\."
content = re.sub(pattern, fact, content)

# ✅ NEW: Simple string matching
area_pattern = f"area_details({area_name},"
for line in lines:
    if area_pattern in line:
        new_lines.append(fact + "\n")
```

**Why:** String operations are faster than regex for simple patterns.

---

### 3. Pre-computed Lookup Tables (fdi.py)
```python
# ✅ Module-level constant (computed once at import)
_FDI_THRESHOLDS = [
    (0, 2.7, [0.7, 0.9, 1.0]),
    (2.7, 5.3, [0.6, 0.8, 0.9, 1.0]),
    # ... etc
]

# Use in function
def get_adjustment_factor(rain, days_rain):
    for low, high, factors in _FDI_THRESHOLDS:
        if low <= rain < high:
            index = min(days_rain - 1, len(factors) - 1)
            return factors[index]
    return 1.0
```

**Why:** Constants are computed once at module load, not on every function call.

---

### 4. Better Error Handling (fdi.py, app.py)
```python
# ✅ NEW: Explicit timeout and clear error messages
try:
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Prolog error: {result.stderr}")
    return result.stdout.strip()
except subprocess.TimeoutExpired:
    raise RuntimeError("Prolog query timed out after 30s")
except Exception as e:
    raise RuntimeError(f"Prolog execution failed: {str(e)}")
```

**Why:** Prevents hung processes and provides actionable error messages.

---

### 5. Parallel Testing (apitests.py)
```python
# ✅ NEW: Run tests concurrently
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(test_func): name for test_name, test_func in tests}
    for future in as_completed(futures):
        results[futures[future]] = future.result()
```

**Why:** Tests that call external APIs can run in parallel, 3-4x speedup.

---

## Performance Checklist

When adding new features, ensure:

- [ ] **API Calls** use `_get_session()` for connection pooling
- [ ] **Lookups** use pre-computed module-level dictionaries/lists
- [ ] **File Operations** use simple string matching, not regex
- [ ] **Subprocess Calls** have explicit timeouts
- [ ] **Error Handling** includes try-except with fallbacks
- [ ] **Input Validation** happens before processing

---

## Monitoring Performance

### Request Profiling
```python
import time

start = time.time()
result = analyze_location_dynamic(lat, lon, "test")
duration = time.time() - start
print(f"Analysis took {duration:.2f}s")
```

### Memory Usage
```python
import tracemalloc

tracemalloc.start()
result = analyze_location_dynamic(lat, lon, "test")
current, peak = tracemalloc.get_traced_memory()
print(f"Memory: {peak / 1024 / 1024:.2f} MB")
```

### Session Pool Stats
```python
# After _get_session() is called multiple times
session = _get_session()
if hasattr(session, 'cache'):
    print(f"Cache size: {len(session.cache.responses)}")
```

---

## Common Pitfalls to Avoid

❌ **DON'T:**
```python
# Creating new session per API call
cache_session = requests_cache.CachedSession('.cache')  # Per call!
```

❌ **DON'T:**
```python
# Using regex for simple string matching
pattern = rf"area_details\({area_name},.*?\)\."
content = re.sub(pattern, fact, content)
```

❌ **DON'T:**
```python
# Subprocess without timeout
subprocess.check_output(cmd)  # Can hang forever!
```

✅ **DO:**
```python
# Reuse global session
session = _get_session()

# Use string matching for simple patterns
if f"area_details({area_name}," in line:
    # ...

# Always add timeout
subprocess.run(cmd, timeout=30)
```

---

## Future Optimization Ideas

### High Priority
1. **Redis Caching** - Cache classification results by (lat, lon)
2. **Batch API Requests** - Combine multiple locations in single request
3. **Database** - Store historical results to avoid recomputation

### Medium Priority
4. **Async Flask** - Use Quart instead for non-blocking I/O
5. **Pre-compiled Prolog** - Compile Prolog queries at startup
6. **Native Python Engine** - Consider Python-based fire risk model as Prolog alternative

### Low Priority
7. **CDN** - Cache static files
8. **API Rate Limiting** - Prevent abuse
9. **Compression** - gzip responses

---

## Testing the Optimizations

### 1. Verify Connection Pooling
```bash
# Should see reused connections
python -c "from fdi import *; print(_get_session()); print(_get_session())"
# Should be same object
```

### 2. Benchmark FDI Calculation
```bash
python -c "
from fdi import calculate_fdi
import time

start = time.time()
for _ in range(10000):
    calculate_fdi(28, 45, 15, 5, 10)
print(f'10k FDI calcs: {time.time() - start:.3f}s')
"
```

### 3. Run Parallel Tests
```bash
time python apitests.py
# Should complete faster than before
```

---

## Contact & Questions

For questions about specific optimizations, refer to `OPTIMIZATION_SUMMARY.md` for detailed explanations and performance metrics.
