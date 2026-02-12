"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signUp } from "@/lib/auth.client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";

/**
 * Signup form component with validation.
 * Per spec US1: User Registration with email/password.
 */
export function SignupForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [generalError, setGeneralError] = useState("");

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Email validation
    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation (min 8 chars per FR-029)
    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    // Confirm password
    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError("");

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const result = await signUp.email({
        email,
        password,
        name: email.split("@")[0], // Use email prefix as default name
      });

      if (result.error) {
        // Handle specific errors
        if (result.error.message?.includes("already exists")) {
          setErrors({ email: "An account with this email already exists" });
        } else {
          setGeneralError(result.error.message || "Signup failed");
        }
        return;
      }

      // T036: Auto-redirect to dashboard after successful signup
      // Use window.location for a full page navigation to ensure cookies
      // from the sign-up response are included in the dashboard request
      window.location.href = "/dashboard";
    } catch (error) {
      setGeneralError("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <h2 className="text-2xl font-bold text-center text-gray-900">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Start managing your tasks today
        </p>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {generalError && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md">
              {generalError}
            </div>
          )}

          <Input
            label="Email address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            required
          />

          <Input
            label="Confirm password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            placeholder="Confirm your password"
            autoComplete="new-password"
            required
          />
        </CardContent>

        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            isLoading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? "Creating account..." : "Create account"}
          </Button>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{" "}
            <Link
              href="/signin"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
