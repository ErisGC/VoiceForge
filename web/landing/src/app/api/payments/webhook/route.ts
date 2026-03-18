import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { PRICE_WOMPI_CENTS, PRODUCT_REFERENCE } from "@/lib/constants";

/**
 * Verified purchase record (in production this would write to a database).
 * For MVP we store in-memory; the production version will use the
 * VoiceForge PostgreSQL database via the existing API.
 */
const VERIFIED_PURCHASES = new Map<string, PurchaseRecord>();

interface PurchaseRecord {
  transactionId: string;
  reference: string;
  userId: string;
  email: string;
  amountInCents: number;
  currency: string;
  paymentMethod: string;
  status: string;
  createdAt: string;
}

/**
 * POST /api/payments/webhook
 *
 * Receives Wompi event notifications. Verifies the cryptographic
 * signature to ensure the event is authentic, then records the
 * purchase if the transaction is APPROVED.
 *
 * Wompi signs events with: SHA256(event.transaction.id + event.transaction.status + event.transaction.amount_in_cents + timestamp + events_secret)
 */
export async function POST(request: NextRequest) {
  const eventsSecret = process.env.WOMPI_EVENTS_SECRET;
  if (!eventsSecret) {
    console.error("[webhook] WOMPI_EVENTS_SECRET not configured");
    return NextResponse.json(
      { error: "Server misconfigured" },
      { status: 500 },
    );
  }

  let body: WompiEvent;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  // Verify signature
  const { signature, data, timestamp } = body;
  if (!signature?.checksum || !data?.transaction || !timestamp) {
    console.warn("[webhook] Missing required fields in event payload");
    return NextResponse.json({ error: "Malformed event" }, { status: 400 });
  }

  const tx = data.transaction;
  const signatureString = `${tx.id}${tx.status}${tx.amount_in_cents}${timestamp}${eventsSecret}`;
  const expectedChecksum = crypto
    .createHash("sha256")
    .update(signatureString)
    .digest("hex");

  if (signature.checksum !== expectedChecksum) {
    console.error(
      "[webhook] Signature verification FAILED",
      { transactionId: tx.id, expected: expectedChecksum, received: signature.checksum },
    );
    return NextResponse.json(
      { error: "Invalid signature" },
      { status: 403 },
    );
  }

  console.info("[webhook] Signature verified", { transactionId: tx.id, status: tx.status });

  // Idempotency: skip if already processed
  if (VERIFIED_PURCHASES.has(tx.id)) {
    console.info("[webhook] Transaction already processed (idempotent)", { transactionId: tx.id });
    return NextResponse.json({ status: "already_processed" });
  }

  // Only process APPROVED transactions
  if (tx.status !== "APPROVED") {
    console.info("[webhook] Transaction not approved", { transactionId: tx.id, status: tx.status });
    return NextResponse.json({ status: "noted", transactionStatus: tx.status });
  }

  // Validate amount and currency
  if (tx.amount_in_cents !== PRICE_WOMPI_CENTS || tx.currency !== "COP") {
    console.error("[webhook] Amount/currency mismatch", {
      expected: { amount: PRICE_WOMPI_CENTS, currency: "COP" },
      received: { amount: tx.amount_in_cents, currency: tx.currency },
    });
    return NextResponse.json(
      { error: "Amount mismatch" },
      { status: 400 },
    );
  }

  // Extract user ID from reference (format: voiceforge-app-v1-{auth0_sub}-{timestamp})
  const referenceParts = tx.reference?.split("-") ?? [];
  const userId = referenceParts.length >= 5
    ? referenceParts.slice(3, -1).join("-")
    : "unknown";

  const purchase: PurchaseRecord = {
    transactionId: tx.id,
    reference: tx.reference ?? "",
    userId,
    email: tx.customer_email ?? "",
    amountInCents: tx.amount_in_cents,
    currency: tx.currency,
    paymentMethod: tx.payment_method_type ?? "unknown",
    status: "completed",
    createdAt: new Date().toISOString(),
  };

  VERIFIED_PURCHASES.set(tx.id, purchase);

  console.info("[webhook] Purchase recorded", {
    transactionId: tx.id,
    userId,
    email: purchase.email,
  });

  return NextResponse.json({ status: "ok" });
}

/**
 * GET /api/payments/webhook
 *
 * Check purchase status for a user (called by download page).
 */
export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("userId");
  if (!userId) {
    return NextResponse.json({ hasPurchase: false });
  }

  const hasPurchase = Array.from(VERIFIED_PURCHASES.values()).some(
    (p) => p.userId === userId && p.status === "completed",
  );

  return NextResponse.json({ hasPurchase });
}

interface WompiEvent {
  event: string;
  data: {
    transaction: {
      id: string;
      status: string;
      amount_in_cents: number;
      currency: string;
      reference?: string;
      customer_email?: string;
      payment_method_type?: string;
    };
  };
  signature: {
    checksum: string;
    properties: string[];
  };
  timestamp: number;
  sent_at: string;
}
