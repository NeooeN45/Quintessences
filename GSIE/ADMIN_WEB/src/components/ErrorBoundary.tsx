import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary — capture les erreurs runtime React et affiche
 * un fallback élégant au lieu d'un écran blanc.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[GSIE Dashboard] ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const isNetworkError = this.state.error?.message?.includes("Failed to fetch") ||
        this.state.error?.message?.includes("NetworkError") ||
        this.state.error?.message?.includes("load failed");
      return (
        <div className="flex min-h-[40vh] flex-col items-center justify-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full border border-error/30 bg-error-bg">
            <svg className="h-6 w-6 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="mt-4 text-lg font-semibold text-fg-100">
            {isNetworkError ? "API indisponible" : "Une erreur est survenue"}
          </h2>
          <p className="mt-1 max-w-md text-[13px] text-fg-400">
            {isNetworkError
              ? "Le serveur API GSIE ne répond pas. Vérifiez qu'il est démarré (port 8000) puis réessayez."
              : this.state.error?.message ?? "Erreur inattendue dans le composant."}
          </p>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="rounded-md border border-border bg-bg-100 px-4 py-2 text-[13px] text-fg-200 transition-colors hover:border-border-strong hover:text-fg-100"
            >
              Réessayer
            </button>
            <button
              onClick={() => window.location.reload()}
              className="rounded-md border border-border bg-bg-200 px-4 py-2 text-[13px] text-fg-300 transition-colors hover:border-border-strong hover:text-fg-100"
            >
              Recharger la page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
