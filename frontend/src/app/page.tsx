async function getBackendHealth() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${apiUrl}/api/v1/health`, { cache: "no-store" });
    if (!res.ok) return { status: "unreachable" as const };
    const data = (await res.json()) as { status: string };
    return { status: data.status as "ok" | "unreachable" };
  } catch {
    return { status: "unreachable" as const };
  }
}

export default async function Home() {
  const health = await getBackendHealth();
  const isUp = health.status === "ok";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">CRM Platform</h1>
      <p className="text-sm text-neutral-500">Phase 0 scaffolding — frontend and backend wired together.</p>
      <div className="flex items-center gap-2 rounded-full border px-4 py-2 text-sm">
        <span className={`h-2 w-2 rounded-full ${isUp ? "bg-emerald-500" : "bg-red-500"}`} />
        Backend API: {isUp ? "connected" : "not reachable"}
      </div>
    </main>
  );
}
