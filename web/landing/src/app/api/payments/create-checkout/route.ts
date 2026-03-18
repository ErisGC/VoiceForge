import { getSession } from "@auth0/nextjs-auth0";
import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { PLANS, PRODUCT_REFERENCE, type PlanId } from "@/lib/constants";

/**
 * POST /api/payments/create-checkout
 *
 * Creates a Wompi checkout session for the authenticated user.
 * Accepts { planId } in the request body to determine the plan.
 *
 * The integrity hash uses WOMPI_INTEGRITY_SECRET (from the "Integridad"
 * section of the Wompi dashboard), which is distinct from the
 * WOMPI_EVENTS_SECRET used for webhook signature verification.
 */
export async function POST(request: NextRequest) {
  const session = await getSession();

  if (!session?.user) {
    return NextResponse.json(
      { error: "No autenticado" },
      { status: 401 },
    );
  }

  const publicKey = process.env.NEXT_PUBLIC_WOMPI_PUBLIC_KEY;
  if (!publicKey) {
    console.error("[create-checkout] NEXT_PUBLIC_WOMPI_PUBLIC_KEY not configured");
    return NextResponse.json({ error: "Server misconfigured" }, { status: 500 });
  }

  const integritySecret = process.env.WOMPI_INTEGRITY_SECRET;
  if (!integritySecret) {
    console.error("[create-checkout] WOMPI_INTEGRITY_SECRET not configured");
    return NextResponse.json({ error: "Server misconfigured" }, { status: 500 });
  }

  // Parse plan from body
  let planId: PlanId = "pro";
  try {
    const body = await request.json();
    if (body.planId && body.planId in PLANS && body.planId !== "free") {
      planId = body.planId as PlanId;
    }
  } catch {
    // Default to pro if body parsing fails
  }

  const plan = PLANS[planId];
  if (plan.priceWompiCents === 0) {
    return NextResponse.json(
      { error: "El plan gratuito no requiere pago" },
      { status: 400 },
    );
  }

  const currency = "COP";
  const safeSub = (session.user.sub as string).replace(/\|/g, "__");
  const reference = `${PRODUCT_REFERENCE}-${planId}-${safeSub}-${Date.now()}`;

  // Wompi integrity hash: SHA256(reference + amountInCents + currency + integritySecret)
  const integrityString = `${reference}${plan.priceWompiCents}${currency}${integritySecret}`;
  const integrityHash = crypto
    .createHash("sha256")
    .update(integrityString)
    .digest("hex");

  const redirectUrl = `${process.env.NEXT_PUBLIC_APP_URL}/checkout/resultado`;

  return NextResponse.json({
    publicKey,
    currency,
    amountInCents: plan.priceWompiCents,
    reference,
    integrityHash,
    redirectUrl,
    customerEmail: session.user.email,
  });
}
