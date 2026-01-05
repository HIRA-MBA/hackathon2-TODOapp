import { redirect } from "next/navigation";
import { requireAuth } from "@/lib/auth.server";

/**
 * Layout for protected pages with session check.
 * Per FR-004: Redirect unauthenticated users to signin page.
 */
export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await requireAuth();

  if (!session) {
    redirect("/signin");
  }

  return <>{children}</>;
}
