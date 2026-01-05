import { redirect } from "next/navigation";

/**
 * Root page - redirects to dashboard.
 * Per T089: Add root page redirect to dashboard.
 */
export default function Home() {
  redirect("/dashboard");
}
