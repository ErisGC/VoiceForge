import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { findPlanByWompiCents } from "@/lib/constants";

/**
 * Verified purchase record.
 *
 * MVP: stored in-memory. In production this will persist to the
 * VoiceForge PostgreSQL database via the existing API or a direct
 * database connection. Purchases survive only within the lifetime
 * of the server process.
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
  plan: string;
  createdAt: string;
}

/**
 * Extract the Auth0 user ID from a payment reference.
 *
 * Reference format: `voiceforge-{plan}-{safeSub}-{timestamp}`
 * where safeSub has `|` replaced with `__` (e.g. `auth0__abc123`).
 *
 * We restore the original Auth0 sub format by converting `__` back to `|`.
 */
function extractUserIdFromReference(reference: string): string {
  // Expected format: voiceforge-{plan}-{safeSub}-{timestamp}
  // The plan may contain hyphens, safeSub may contain hyphens and double underscores.
  // The timestamp is always the last segment (all digits).
  const parts = reference.split("-");
  if (parts.length < 4) return "unknown";

  // Remove "voiceforge" prefix and timestamp suffix
  // Rejoin the middle as the plan+sub identifier
  const timestamp = parts[parts.length - 1];
  if (!/^\d+$/.test(timestamp)) return "unknown";

  // The structure is: voiceforge - plan - safeSub - timestamp
  // plan = parts[1], safeSub = parts.slice(2, -1).join("-")
  const safeSub = parts.slice(2, -1).join("-");

  // Restore the Auth0 sub format: auth0__abc123 → auth0|abc123
  return safeSub.replace(/__/g, "|");
}

/**
 * Extract the plan identifier from a payment reference.
 *
 * Reference format: `voiceforge-{plan}-{safeSub}-{timestamp}`
 */
function extractPlanFromReference(reference: string): string {
  const parts = reference.split("-");
  return parts.length >= 2 ? parts[1] : "unknown";
}

/**
 * POST /api/payments/webhook
 *
 * Receives Wompi event notifications. Verifies the cryptographic
 * signature to ensure the event is authentic, then records the
 * purchase if the transaction is APPROVED.
 *
 * Wompi webhook signature: SHA256(concat of properties listed in
 * signature.properties, in order, plus the events secret).
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

  // Validate required fields
  const { signature, data, timestamp } = body;
  if (!signature?.checksum || !data?.transaction || timestamp === undefined) {
    console.warn("[webhook] Missing required fields in event payload");
    return NextResponse.json({ error: "Malformed event" }, { status: 400 });
  }

  const tx = data.transaction;

  // Build the signature string dynamically from the properties array.
  // Wompi's signature.properties tells us which transaction fields were
  // used (in order) to compute the checksum.
  // Fallback to the known default: id + status + amount_in_cents
  const properties = signature.properties ?? [
    "transaction.id",
    "transaction.status",
    "transaction.amount_in_cents",
  ];

  const fieldMap: Record<string, unknown> = {
    "transaction.id": tx.id,
    "transaction.status": tx.status,
    "transaction.amount_in_cents": tx.amount_in_cents,
    "transaction.reference": tx.reference,
    "transaction.currency": tx.currency,
    "transaction.customer_email": tx.customer_email,
    "transaction.payment_method_type": tx.payment_method_type,
  };

  const signatureParts = properties.map((prop) => String(fieldMap[prop] ?? ""));
  const signatureString = signatureParts.join("") + String(timestamp) + eventsSecret;
  const expectedChecksum = crypto
    .createHash("sha256")
    .update(signatureString)
    .digest("hex");

  if (signature.checksum !== expectedChecksum) {
    console.error("[webhook] Signature verification FAILED", {
      transactionId: tx.id,
      properties,
    });
    return NextResponse.json(
      { error: "Invalid signature" },
      { status: 401 },
    );
  }

  console.info("[webhook] Signature verified", { transactionId: tx.id, status: tx.status });

  // Idempotency: skip if already processed
  if (VERIFIED_PURCHASES.has(tx.id)) {
    console.info("[webhook] Transaction already processed (idempotent)", { transactionId: tx.id });
    return NextResponse.json({ status: "already_processed" });
  }

  // Only record APPROVED transactions as completed purchases
  if (tx.status !== "APPROVED") {
    console.info("[webhook] Transaction not approved", { transactionId: tx.id, status: tx.status });
    return NextResponse.json({ status: "noted", transactionStatus: tx.status });
  }

  // Validate amount matches a known plan and currency is COP
  const matchedPlan = findPlanByWompiCents(tx.amount_in_cents);
  if (!matchedPlan || tx.currency !== "COP") {
    console.error("[webhook] Amount/currency mismatch — no matching plan", {
      received: { amount: tx.amount_in_cents, currency: tx.currency },
    });
    return NextResponse.json(
      { error: "Amount mismatch" },
      { status: 400 },
    );
  }

  const reference = tx.reference ?? "";
  const userId = extractUserIdFromReference(reference);
  const plan = extractPlanFromReference(reference) || matchedPlan;

  const purchase: PurchaseRecord = {
    transactionId: tx.id,
    reference,
    userId,
    email: tx.customer_email ?? "",
    amountInCents: tx.amount_in_cents,
    currency: tx.currency,
    paymentMethod: tx.payment_method_type ?? "unknown",
    status: "completed",
    plan,
    createdAt: new Date().toISOString(),
  };

  VERIFIED_PURCHASES.set(tx.id, purchase);

  console.info("[webhook] Purchase recorded", {
    transactionId: tx.id,
    userId,
    plan,
    email: purchase.email,
  });

  return NextResponse.json({ status: "ok" });
}

/**
 * GET /api/payments/webhook
 *
 * Check purchase status for a user (called by download page).
 * Returns whether the user has at least one completed purchase.
 */
export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("userId");
  if (!userId) {
    return NextResponse.json({ hasPurchase: false });
  }

  const userPurchase = Array.from(VERIFIED_PURCHASES.values()).find(
    (p) => p.userId === userId && p.status === "completed",
  );

  return NextResponse.json({
    hasPurchase: !!userPurchase,
    plan: userPurchase?.plan ?? null,
  });
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
