import { NextResponse, type NextRequest } from "next/server";
import { getSession } from "@auth0/nextjs-auth0/edge";

/**
 * Next.js middleware for route protection and rate limiting.
 *
 * - /descargar: requires authenticated session (redirects to login)
 * - /checkout: requires authenticated session (redirects to login)
 * - /api/payments/*: rate limiting via simple IP-based counter
 */

/** Simple in-memory rate limiter for payment endpoints. */
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 30;
const ipRequestCounts = new Map<string, { count: number; resetAt: number }>();

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const entry = ipRequestCounts.get(ip);

  if (!entry || now > entry.resetAt) {
    ipRequestCounts.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return false;
  }

  entry.count++;
  return entry.count > RATE_LIMIT_MAX_REQUESTS;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Rate limiting for payment API endpoints
  if (pathname.startsWith("/api/payments/")) {
    const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
      ?? request.headers.get("x-real-ip")
      ?? "unknown";

    if (isRateLimited(ip)) {
      return NextResponse.json(
        { error: "Demasiadas solicitudes. Intenta de nuevo en un momento." },
        { status: 429 },
      );
    }

    // Webhook endpoint must be publicly accessible (no auth check)
    if (pathname === "/api/payments/webhook") {
      return NextResponse.next();
    }
  }

  // Protected routes: require authentication
  const protectedPaths = ["/descargar", "/checkout"];
  const isProtected = protectedPaths.some((p) => pathname.startsWith(p));

  if (isProtected) {
    const response = NextResponse.next();
    const session = await getSession(request, response);

    if (!session?.user) {
      const loginUrl = new URL("/api/auth/login", request.url);
      loginUrl.searchParams.set("returnTo", pathname);
      return NextResponse.redirect(loginUrl);
    }

    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/descargar/:path*",
    "/checkout/:path*",
    "/api/payments/:path*",
  ],
};
