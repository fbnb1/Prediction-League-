import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const ToastContext = createContext(null);
let nextId = 1;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (message, kind = 'success') => {
      const id = nextId++;
      setToasts((list) => [...list, { id, message, kind }]);
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss],
  );

  const toast = useMemo(
    () => ({
      success: (m) => push(m, 'success'),
      error: (m) => push(m, 'error'),
      warn: (m) => push(m, 'warn'),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="toasts">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`} onClick={() => dismiss(t.id)}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
