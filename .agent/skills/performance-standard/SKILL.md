---
description: Enforce high-performance standards (npmx Standard) for React/Vite development (Virtualization, SWR, Debouncing).
---

# 🚀 Performance Standard (The "npmx" Way)

This skill defines the **MANDATORY** performance architecture for ZeePub-bot. All future features must adhere to these patterns to maintain "Enterprise" speed.

## 1. List Virtualization (`virtua`)
**Context**: Any list carrying more than 50 items (Library, Search Results, Logs, Admin User Lists).
**Rule**: NEVER render full lists. ALWAYS use `virtua`.

### Pattern
```tsx
import { VList } from 'virtua';

// ❌ BAD: Rendering all map items
{items.map(item => <Card key={item.id} />)}

// ✅ GOOD: Virtualized Loop
<VList style={{ height: '100vh' }}>
  {items.map(item => <Card key={item.id} />)}
</VList>
```

### Grid Pattern (Chunked Rows)
For grids, you must chunk the array yourself, as `VList` is a vertical list virtualizer.
```tsx
// Helper
const chunkArray = (arr, size) => ...

// Render
const rows = useMemo(() => chunkArray(items, columns), [items, columns]);
<VList>
  {rows.map((row) => (
     <div className="grid grid-cols-5 gap-4">
        {row.map(item => <Card item={item} />)}
     </div>
  ))}
</VList>
```

## 2. Smart Caching (`SWR`)
**Context**: Fetching data from API (Dashboard, Profiles, Metadata).
**Rule**: NEVER use `useEffect` + `setState` for fetching. ALWAYS use `useSWR`.

### Pattern
```ts
import useSWR from 'swr';

// ❌ BAD: Manual Effect
useEffect(() => { setLoading(true); api.get().then(setData) }, []);

// ✅ GOOD: SWR Hook
const { data, error } = useSWR('unique/key', fetcher, {
  revalidateOnFocus: false,
  dedupingInterval: 60000 
});
```

## 3. Interaction Debouncing (`perfect-debounce`)
**Context**: Search inputs, sliders, auto-saving forms.
**Rule**: DECOUPLE UI update from Logic update.

### Pattern
```tsx
import { debounce } from 'perfect-debounce';

// 1. Local state for instant UI (Input value)
const [localVal, setLocalVal] = useState(initial);

// 2. Debounced logic trigger
const debouncedSearch = useMemo(() => debounce((val) => api.search(val), 300), []);

// 3. Handler
const onChange = (e) => {
   setLocalVal(e.target.value); // Instant
   debouncedSearch(e.target.value); // Delayed
}
```

## 4. Asset Loading
**Rule**:
- Images: `<img loading="lazy" />` (Native).
- Components: `React.lazy()` for all Route components.
- Fonts/Scripts: Defer non-critical assets.

## 5. View Transitions
**Context**: Navigating between major views.
**Rule**: Use `document.startViewTransition` if available.

```tsx
if (document.startViewTransition) {
   document.startViewTransition(() => navigate(path));
} else {
   navigate(path);
}
```
