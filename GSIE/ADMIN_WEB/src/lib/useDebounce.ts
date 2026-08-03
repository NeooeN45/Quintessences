import { useEffect, useState } from "react";

/**
 * Hook de debounce — retarde la mise à jour d'une valeur jusqu'à ce
 * qu'elle soit stable pendant le délai spécifié.
 *
 * Usage :
 *   const debouncedQuery = useDebounce(searchQuery, 300);
 *   useEffect(() => { fetch(debouncedQuery); }, [debouncedQuery]);
 */
export function useDebounce<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
