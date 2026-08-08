import { InviteForm } from "@/components/auth/invite-form";
import { getOrgMembers } from "@/lib/auth/get-org-members";
import { getServerUser } from "@/lib/auth/get-server-user";

export default async function DashboardPage() {
  const [user, members] = await Promise.all([getServerUser(), getOrgMembers()]);
  if (!user) return null; // layout already redirects; keeps TypeScript happy

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
          Welcome, {user.full_name.split(" ")[0]}
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Signed in as <span className="font-medium">{user.email}</span> — role
          {user.roles.length > 1 ? "s" : ""}: {user.roles.join(", ")}
        </p>
      </div>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Team ({members.length})</h2>
        <table className="mt-4 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800">
              <th className="pb-2 font-medium">Name</th>
              <th className="pb-2 font-medium">Email</th>
              <th className="pb-2 font-medium">Role</th>
              <th className="pb-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => (
              <tr key={member.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                <td className="py-2 text-neutral-900 dark:text-neutral-50">{member.full_name}</td>
                <td className="py-2 text-neutral-500">{member.email}</td>
                <td className="py-2 text-neutral-500">{member.roles.join(", ")}</td>
                <td className="py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      member.is_active
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400"
                        : "bg-neutral-100 text-neutral-500 dark:bg-neutral-800"
                    }`}
                  >
                    {member.is_active ? "Active" : "Deactivated"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {user.permissions.includes("user.invite") && (
        <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Invite a teammate</h2>
          <div className="mt-4">
            <InviteForm />
          </div>
        </section>
      )}
    </div>
  );
}
