import { InviteForm } from "@/components/auth/invite-form";
import { getOrgMembers } from "@/lib/auth/get-org-members";

export default async function AdminUsersPage() {
  const members = await getOrgMembers();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
          Organization users
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {members.length} member{members.length === 1 ? "" : "s"}. Full user management (deactivate, role changes)
          lands in a later phase — this is the Phase 1 admin-portal placeholder.
        </p>
      </div>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="overflow-x-auto">
        <table className="w-full min-w-[500px] text-left text-sm">
          <thead>
            <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800">
              <th className="px-2 pb-2 font-medium">Name</th>
              <th className="px-2 pb-2 font-medium">Email</th>
              <th className="px-2 pb-2 font-medium">Role</th>
              <th className="px-2 pb-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => (
              <tr key={member.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                <td className="px-2 py-2 text-neutral-900 dark:text-neutral-50">{member.full_name}</td>
                <td className="px-2 py-2 text-neutral-500">{member.email}</td>
                <td className="px-2 py-2 text-neutral-500">{member.roles.join(", ")}</td>
                <td className="px-2 py-2">
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
        </div>
      </section>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Invite a teammate</h2>
        <div className="mt-4">
          <InviteForm />
        </div>
      </section>
    </div>
  );
}
