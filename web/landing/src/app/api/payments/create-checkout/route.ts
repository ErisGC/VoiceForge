import { getSession } from "@auth0/nextjs-auth0";
import { NextResponse } from "next/server";
import crypto from "crypto";
import { PRICE_WOMPI_CENTS, PRODUCT_REFERENCE } from "@/lib/constants";

/**
 * POST /api/payments/create-checkout
 *
 * Creates a Wompi payment link for the authenticated user.
 * Returns the checkout URL and transaction reference.
 */
export async function POST() {
  const session = await getSession();

  if (!session?.user) {
    return NextResponse.json(
      { error: "No autenticado" },
      { status: 401 },
    );
  }

  const publicKey = process.env.NEXT_PUBLIC_WOMPI_PUBLIC_KEY;
  const currency = "COP";
  const reference = `${PRODUCT_REFERENCE}-${session.user.sub}-${Date.now()}`;

  // Generate integrity hash for Wompi
  // Format: reference + amount_in_cents + currency + integrity_secret
  const integritySecret = process.env.WOMPI_EVENTS_SECRET ?? "";
  const integrityString = `${reference}${PRICE_WOMPI_CENTS}${currency}${integritySecret}`;
  const integrityHash = crypto
    .createHash("sha256")
    .update(integrityString)
    .digest("hex");

  const redirectUrl = `${process.env.NEXT_PUBLIC_APP_URL}/checkout/resultado`;

  return NextResponse.json({
    publicKey,
    currency,
    amountInCents: PRICE_WOMPI_CENTS,
    reference,
    integrityHash,
    redirectUrl,
    customerEmail: session.user.email,
  });
}
