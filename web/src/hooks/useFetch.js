import { useCallback, useEffect, useState } from 'react';

// Runs an async loader and tracks { data, loading, error }. `deps` controls
// when the loader re-runs; `reload` re-runs it on demand.
// `refreshInterval` (ms): if set, silently re-fetches data every N ms.
// Background refreshes do NOT trigger the loading spinner.
export function useFetch(loader, deps = [], { refreshInterval } = {}) {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(loader, deps);
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const reload = useCallback(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    run().then(
      (data) => !cancelled && setState({ data, loading: false, error: null }),
      (error) => !cancelled && setState({ data: null, loading: false, error }),
    );
    return () => {
      cancelled = true;
    };
  }, [run]);

  useEffect(() => reload(), [reload]);

  useEffect(() => {
    if (!refreshInterval) return;
    const id = setInterval(() => {
      let cancelled = false;
      run().then(
        (data) => !cancelled && setState({ data, loading: false, error: null }),
        () => { /* silently ignore background refresh errors */ },
      );
      return () => { cancelled = true; };
    }, refreshInterval);
    return () => clearInterval(id);
  }, [run, refreshInterval]);

  return { ...state, reload };
}
