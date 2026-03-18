import crypto from "crypto";

const DOWNLOAD_TOKEN_EXPIRY_SECONDS = 3600; // 1 hour

/**
 * Generate a signed download token for a verified purchaser.
 *
 * The token is an HMAC-SHA256 signature over `userId:expiresAt`,
 * combined with the expiry timestamp. The download endpoint
 * verifies the token before serving the APK.
 *
 * @param userId - Auth0 user ID (sub claim)
 * @returns Object with the signed URL query parameters
 */
export function generateDownloadToken(userId: string): {
  token: string;
  expires: number;
} {
  const secret = process.env.DOWNLOAD_SIGNING_SECRET;
  if (!secret) {
    throw new Error("DOWNLOAD_SIGNING_SECRET not configured");
  }

  const expires = Math.floor(Date.now() / 1000) + DOWNLOAD_TOKEN_EXPIRY_SECONDS;
  const payload = `${userId}:${expires}`;
  const token = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  return { token, expires };
}

/**
 * Verify a download token.
 *
 * @param userId - Auth0 user ID
 * @param token - HMAC token from the URL
 * @param expires - Expiry timestamp from the URL
 * @returns true if the token is valid and not expired
 */
export function verifyDownloadToken(
  userId: string,
  token: string,
  expires: number,
): boolean {
  const secret = process.env.DOWNLOAD_SIGNING_SECRET;
  if (!secret) return false;

  // Check expiry
  const now = Math.floor(Date.now() / 1000);
  if (now > expires) return false;

  // Verify HMAC
  const payload = `${userId}:${expires}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(payload)
    .digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(token, "hex"),
    Buffer.from(expected, "hex"),
  );
}
