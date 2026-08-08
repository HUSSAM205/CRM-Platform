"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { apiClient, ApiError } from "@/lib/api-client";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  role_name: z.enum(["manager", "member", "viewer"]),
});

type FormValues = z.infer<typeof schema>;

export function InviteForm() {
  const [result, setResult] = useState<{ url: string } | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { role_name: "member" } });

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    setResult(null);
    try {
      const res = await apiClient.post<{ invite_url: string }>("/auth/invitations", values);
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      setResult({ url: `${origin}${res.invite_url}` });
      reset();
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-wrap items-end gap-3" noValidate>
      <div>
        <label htmlFor="invite-email" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
          Email
        </label>
        <input
          id="invite-email"
          type="email"
          placeholder="teammate@company.com"
          {...register("email")}
          className="mt-1 w-64 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        />
        {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
      </div>
      <div>
        <label htmlFor="invite-role" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
          Role
        </label>
        <select
          id="invite-role"
          {...register("role_name")}
          className="mt-1 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        >
          <option value="manager">Manager</option>
          <option value="member">Member</option>
          <option value="viewer">Viewer</option>
        </select>
      </div>
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-700 disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900 dark:hover:bg-neutral-200"
      >
        {isSubmitting ? "Inviting…" : "Send invite"}
      </button>

      {serverError && <p className="w-full text-sm text-red-600">{serverError}</p>}
      {result && (
        <p className="w-full break-all text-sm text-emerald-700 dark:text-emerald-400">
          Invite link (no email service configured yet — share this manually): {result.url}
        </p>
      )}
    </form>
  );
}
