import { Suspense } from "react";
import { SigninForm } from "@/components/auth/signin-form";

/**
 * Signin page.
 * Per FR-002: System MUST provide a signin page accessible at /signin path.
 */
export default function SigninPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SigninForm />
    </Suspense>
  );
}
