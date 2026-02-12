import { redirect } from "next/navigation";
import { cookies } from "next/headers";

/**
 * Layout for protected pages with session check.
 * Per FR-004: Redirect unauthenticated users to signin page.
 *
 * Uses cookie-presence check instead of full DB validation.
 * Full session validation happens client-side via useSession() hook,
 * which is more resilient to transient DB/crypto errors that would
 * otherwise cause false "session expired" redirects.
 */
export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const hasSessionCookie = cookieStore
    .getAll()
    .some((c) => c.name.includes("session"));

  if (!hasSessionCookie) {
    redirect("/signin");
  }

  return <>{children}</>;
}
