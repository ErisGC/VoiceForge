"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { PLANS, APP_NAME, type PlanId } from "@/lib/constants";

interface CheckoutData {
  publicKey: string;
  currency: string;
  amountInCents: number;
  reference: string;
  integrityHash: string;
  redirectUrl: string;
  customerEmail: string;
}

function CheckoutContent() {
  const { user, isLoading } = useUser();
  const searchParams = useSearchParams();
  const planParam = searchParams.get("plan") as PlanId | null;

  // Default to "pro" if no plan or invalid plan specified
  const planId: PlanId = planParam && planParam in PLANS && planParam !== "free"
    ? planParam
    : "pro";
  const plan = PLANS[planId];

  const [termsAccepted, setTermsAccepted] = useState(false);
  const [dataAccepted, setDataAccepted] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-text-300">Cargando...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Inicia sesi&oacute;n para comprar</h1>
          <p className="mt-2 text-text-300">
            Necesitas una cuenta para completar la compra.
          </p>
          {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- Auth0 handler is a raw API route, not a Next.js page */}
          <a
            href="/api/auth/login"
            className="mt-6 inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-primary-500 to-accent-violet px-8 py-4 text-base font-semibold text-white shadow-[0_0_24px_rgba(109,124,255,0.3)] transition-all duration-200 hover:shadow-[0_0_32px_rgba(109,124,255,0.45)] hover:brightness-110"
            role="button"
          >
            Iniciar sesi&oacute;n
          </a>
        </div>
      </div>
    );
  }

  const canProceed = termsAccepted && dataAccepted;

  async function handleCheckout() {
    if (!canProceed) return;
    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch("/api/payments/create-checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ planId }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error ?? "Error al crear la sesi\u00f3n de pago");
      }

      const data: CheckoutData = await response.json();

      // Open Wompi checkout widget
      const wompiWidget = (window as WompiWindow).WidgetCheckout;
      if (wompiWidget) {
        const checkout = new wompiWidget({
          currency: data.currency,
          amountInCents: data.amountInCents,
          reference: data.reference,
          publicKey: data.publicKey,
          redirectUrl: data.redirectUrl,
          customerData: { email: data.customerEmail },
          "signature:integrity": data.integrityHash,
        });
        checkout.open((result: { transaction?: { status: string } }) => {
          if (result.transaction?.status === "APPROVED") {
            window.location.href = "/descargar";
          }
        });
      } else {
        // Fallback: redirect to Wompi hosted checkout
        const params = new URLSearchParams({
          "public-key": data.publicKey,
          currency: data.currency,
          "amount-in-cents": String(data.amountInCents),
          reference: data.reference,
          "redirect-url": data.redirectUrl,
          "signature:integrity": data.integrityHash,
          "customer-data:email": data.customerEmail,
        });
        window.location.href = `https://checkout.wompi.co/p/?${params.toString()}`;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-20">
      {/* Wompi widget script */}
      <script src="https://checkout.wompi.co/widget.js" async />

      <h1 className="text-2xl font-bold">Completar compra</h1>
      <p className="mt-2 text-text-300">
        Hola, {user.name ?? user.email}. Est&aacute;s a un paso de acceder a {APP_NAME}.
      </p>

      {/* Order summary */}
      <div className="mt-8 rounded-2xl border border-border-soft bg-surface-800/50 p-6">
        <h2 className="text-lg font-semibold">Resumen del pedido</h2>
        <div className="mt-4 flex items-center justify-between border-b border-border-soft pb-4">
          <div>
            <span className="text-text-300">{APP_NAME} — Plan {plan.name}</span>
            <p className="mt-1 text-xs text-text-500">
              {plan.conversionsPerMonth === -1
                ? "Conversiones ilimitadas"
                : `${plan.conversionsPerMonth} conversiones/mes`}
              {" \u00b7 "}
              {plan.voiceProfiles === -1
                ? "Perfiles ilimitados"
                : `${plan.voiceProfiles} perfil${plan.voiceProfiles > 1 ? "es" : ""}`}
            </p>
          </div>
          <span className="font-bold">{plan.priceDisplay}</span>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <span className="font-semibold">Total mensual</span>
          <span className="text-xl font-bold">{plan.priceDisplay}</span>
        </div>
        <p className="mt-2 text-xs text-text-500">
          {plan.priceUsdApprox}/mes &middot; Cancela en cualquier momento
        </p>
      </div>

      {/* Plan switcher */}
      {planId !== "unlimited" && (
        <div className="mt-4 rounded-xl border border-border-soft bg-bg-900/40 p-4">
          <p className="text-sm text-text-300">
            {planId === "pro"
              ? "\u00bfNecesitas conversiones ilimitadas?"
              : "\u00bfQuieres m\u00e1s conversiones?"}
            {" "}
            <a
              href={`/checkout?plan=${planId === "pro" ? "unlimited" : "pro"}`}
              className="text-primary-400 underline"
            >
              Cambiar a {planId === "pro" ? "Unlimited" : "Pro"}
            </a>
          </p>
        </div>
      )}

      {/* Legal checkboxes */}
      <div className="mt-6 space-y-3">
        <label className="flex items-start gap-3 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={termsAccepted}
            onChange={(e) => setTermsAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-border-strong bg-surface-800 text-primary-500 focus:ring-primary-400"
          />
          <span className="text-text-300">
            He le&iacute;do y acepto los{" "}
            <a
              href="/legal/terminos"
              target="_blank"
              className="text-primary-400 underline"
            >
              T&eacute;rminos y Condiciones
            </a>
          </span>
        </label>

        <label className="flex items-start gap-3 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={dataAccepted}
            onChange={(e) => setDataAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-border-strong bg-surface-800 text-primary-500 focus:ring-primary-400"
          />
          <span className="text-text-300">
            Autorizo el{" "}
            <a
              href="/legal/privacidad"
              target="_blank"
              className="text-primary-400 underline"
            >
              tratamiento de mis datos personales
            </a>{" "}
            conforme a la Ley 1581 de 2012
          </span>
        </label>
      </div>

      {error && (
        <p className="mt-4 text-sm text-danger-500">{error}</p>
      )}

      <button
        className="mt-8 w-full inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-primary-500 to-accent-violet px-8 py-4 text-base font-semibold text-white shadow-[0_0_24px_rgba(109,124,255,0.3)] transition-all duration-200 hover:shadow-[0_0_32px_rgba(109,124,255,0.45)] hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-400 disabled:opacity-40 disabled:cursor-not-allowed"
        disabled={!canProceed || isCreating}
        onClick={handleCheckout}
      >
        {isCreating ? "Preparando pago..." : `Suscribirse — ${plan.priceDisplay}/mes`}
      </button>

      <p className="mt-4 text-center text-xs text-text-500">
        Pago procesado por Wompi (Bancolombia). Tus datos de tarjeta nunca
        pasan por nuestros servidores.
      </p>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-text-300">Cargando checkout...</p>
        </div>
      }
    >
      <CheckoutContent />
    </Suspense>
  );
}

interface WompiWindow extends Window {
  WidgetCheckout?: new (config: Record<string, unknown>) => {
    open: (callback: (result: { transaction?: { status: string } }) => void) => void;
  };
}
