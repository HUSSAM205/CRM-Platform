import { redirect } from "next/navigation";

import { getServerUser } from "@/lib/auth/get-server-user";

export default async function Home() {
  const user = await getServerUser();
  redirect(user ? "/dashboard" : "/login");
}
