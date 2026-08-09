"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { apiClient } from "@/lib/api-client";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    apiClient
      .get("/users/me")
      .then(() => router.replace("/dashboard"))
      .catch(() => router.replace("/login"));
  }, [router]);

  return null;
}
