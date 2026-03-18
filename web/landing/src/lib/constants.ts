export const APP_NAME = "VoiceForge";
export const CONTACT_EMAIL = "soporte@voiceforge.app";

/** Product reference prefix for payment tracking. */
export const PRODUCT_REFERENCE = "voiceforge";

/**
 * Pricing plans — single source of truth.
 *
 * Amounts in COP (Colombian pesos). Wompi expects centavos (amount * 100).
 *
 * Pricing decision rationale (documented in CLAUDE.md):
 * - Competitor range: $5-$25 USD/month for similar services
 * - At $29,900 COP (~$7 USD), Pro is significantly cheaper than ElevenLabs ($5+),
 *   Kits.AI ($10+), making it competitive globally while accessible in LatAm
 * - Monthly subscription ensures recurring revenue to cover GPU costs
 * - Free tier drives adoption; conversion limits incentivize upgrade
 * - Wompi fees at $29,900 COP: ~2.99% + $900 = ~$1,794 COP (6%) — sustainable
 */
export const PLANS = {
  free: {
    id: "free",
    name: "Gratis",
    priceCop: 0,
    priceDisplay: "Gratis",
    priceWompiCents: 0,
    priceUsdApprox: "$0",
    period: null,
    badge: null,
    conversionsPerMonth: 3,
    voiceProfiles: 1,
    features: [
      "3 conversiones por mes",
      "1 perfil de voz",
      "Grabaci\u00f3n por micr\u00f3fono",
      "Marca de agua en audio",
      "Calidad est\u00e1ndar",
    ],
    limitations: [
      "Marca de agua en resultados",
      "Cola de procesamiento est\u00e1ndar",
    ],
  },
  pro: {
    id: "pro",
    name: "Pro",
    priceCop: 29_900,
    priceDisplay: "$29.900 COP",
    priceWompiCents: 29_900 * 100,
    priceUsdApprox: "~$7 USD",
    period: "mes",
    badge: "Popular",
    conversionsPerMonth: 50,
    voiceProfiles: 5,
    features: [
      "50 conversiones por mes",
      "5 perfiles de voz",
      "Sin marca de agua",
      "Descarga en WAV de alta calidad",
      "Grabaci\u00f3n por micr\u00f3fono",
      "Soporte por correo prioritario",
    ],
    limitations: [],
  },
  unlimited: {
    id: "unlimited",
    name: "Unlimited",
    priceCop: 79_900,
    priceDisplay: "$79.900 COP",
    priceWompiCents: 79_900 * 100,
    priceUsdApprox: "~$19 USD",
    period: "mes",
    badge: "M\u00e1ximo rendimiento",
    conversionsPerMonth: -1, // unlimited
    voiceProfiles: -1, // unlimited
    features: [
      "Conversiones ilimitadas",
      "Perfiles de voz ilimitados",
      "Sin marca de agua",
      "Procesamiento prioritario",
      "Descarga en WAV de alta calidad",
      "Soporte prioritario",
      "Acceso anticipado a nuevas funciones",
    ],
    limitations: [],
  },
} as const;

export type PlanId = keyof typeof PLANS;

/** Default plan for the CTA button. */
export const DEFAULT_PAID_PLAN: PlanId = "pro";

/** Helper to get Wompi cents for a plan. */
export function getPlanWompiCents(planId: PlanId): number {
  return PLANS[planId].priceWompiCents;
}

/**
 * Validate that a Wompi amount matches a known plan.
 * Used in webhook verification.
 */
export function findPlanByWompiCents(amountInCents: number): PlanId | null {
  for (const [id, plan] of Object.entries(PLANS)) {
    if (plan.priceWompiCents === amountInCents && amountInCents > 0) {
      return id as PlanId;
    }
  }
  return null;
}

// Legacy exports for backward compatibility during transition
export const PRICE_COP = PLANS.pro.priceCop;
export const PRICE_DISPLAY = PLANS.pro.priceDisplay;
export const PRICE_WOMPI_CENTS = PLANS.pro.priceWompiCents;
