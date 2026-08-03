import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { AnimatePresence } from "framer-motion";
import { Toast } from "./ui";
import { DELAYS } from "../lib/constants";

interface ToastItem {
  id: number;
  message: string;
  type: "error" | "success" | "info";
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastItem["type"]) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let toastId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback(
    (message: string, type: ToastItem["type"] = "error") => {
      const id = ++toastId;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, DELAYS.toastDismiss);
    },
    [],
  );

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="fixed bottom-6 right-6 z-50 flex flex-col gap-2"
      >
        <AnimatePresence>
          {toasts.map((t) => (
            <Toast
              key={t.id}
              message={t.message}
              type={t.type}
              onClose={() => removeToast(t.id)}
            />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Fallback silencieux si pas de provider (ne crash pas)
    return { showToast: (msg: string) => console.warn("[toast]", msg) };
  }
  return ctx;
}
