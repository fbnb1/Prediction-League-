import { useCallback, useEffect, useState } from 'react';

// Runs an async loader and tracks { data, loading, error }. `deps` controls
// when the loader re-runs; `reload` re-runs it on demand.
export function useFetch(loader, deps = []) {
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
  return { ...state, reload };
}
