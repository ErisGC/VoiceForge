import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@auth0/nextjs-auth0";
import { generateDownloadToken } from "@/lib/download";

/**
 * GET /api/download
 *
 * Generates a signed, temporary download URL for a verified purchaser.
 * Requires an authenticated session and a completed purchase.
 */
export async function GET(request: NextRequest) {
  const session = await getSession();

  if (!session?.user?.sub) {
    return NextResponse.json({ error: "No autenticado" }, { status: 401 });
  }

  const userId = session.user.sub as string;

  // Verify purchase status
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  let hasPurchase = false;

  try {
    const purchaseCheck = await fetch(
      `${baseUrl}/api/payments/webhook?userId=${encodeURIComponent(userId)}`,
      { cache: "no-store" },
    );
    if (purchaseCheck.ok) {
      const data = await purchaseCheck.json();
      hasPurchase = data.hasPurchase === true;
    }
  } catch {
    // If verification fails, deny access
  }

  if (!hasPurchase) {
    return NextResponse.json({ error: "Compra no verificada" }, { status: 403 });
  }

  try {
    const { token, expires } = generateDownloadToken(userId);

    // In production, this would point to a CDN or signed S3 URL.
    // For now, we generate a signed local URL.
    const downloadUrl = `${baseUrl}/api/download/apk?token=${token}&expires=${expires}&userId=${encodeURIComponent(userId)}`;

    return NextResponse.json({ downloadUrl, expiresIn: 3600 });
  } catch (err) {
    console.error("[download] Failed to generate download token", err);
    return NextResponse.json({ error: "Error generating download link" }, { status: 500 });
  }
}
