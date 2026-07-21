export function PageSkeleton() {
  return (
    <div className="flex flex-col gap-6 animate-pulse p-8">
      <div className="h-8 w-64 rounded-lg bg-slate-800" />
      <div className="h-4 w-48 rounded bg-slate-800/60" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-36 rounded-xl bg-slate-800/50" />
        ))}
      </div>
      <div className="h-48 rounded-xl bg-slate-800/30" />
    </div>
  );
}
