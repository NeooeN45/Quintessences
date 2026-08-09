interface Props {
  className?: string;
}

/**
 * Bloc de chargement "fantôme" — pulsation douce, comme sur les
 * interfaces professionnelles, pour tout contenu asynchrone dont le
 * chargement peut dépasser ~300ms (indicateurs live, captures d'écran
 * à venir). Respecte prefers-reduced-motion via le CSS global.
 */
export default function Skeleton({ className = "" }: Props) {
  return (
    <div
      role="status"
      aria-label="Chargement en cours"
      className={`animate-pulse rounded-md bg-[var(--color-bg-300)] ${className}`}
    />
  );
}
