"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClient } from "@/lib/api-client";

export function LogoutButton({ className }: { className?: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const onClick = async () => {
    setLoading(true);
    try {
      await apiClient.post("/auth/logout");
    } finally {
      router.push("/login");
      router.refresh();
    }
  };

  return (
    <button type="button" onClick={onClick} disabled={loading} className={className}>
      {loading ? "Signing out…" : "Sign out"}
    </button>
  );
}
