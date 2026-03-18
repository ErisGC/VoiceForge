"use client";

import { useUser } from "@auth0/nextjs-auth0/client";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { PRICE_DISPLAY, APP_NAME } from "@/lib/constants";

interface CheckoutData {
  publicKey: string;
  currency: string;
  amountInCents: number;
  reference: string;
  integrityHash: string;
  redirectUrl: string;
  customerEmail: string;
}

export default function CheckoutPage() {
  const { user, isLoading } = useUser();
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [dataAccepted, setDataAccepted] = useState(false);
  const [checkoutData, setCheckoutData] = useState<CheckoutData | null>(null);
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
          <h1 className="text-2xl font-bold">Inicia sesión para comprar</h1>
          <p className="mt-2 text-text-300">
            Necesitas una cuenta para completar la compra.
          </p>
          <Button href="/api/auth/login" className="mt-6">
            Iniciar sesión
          </Button>
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
      });

      if (!response.ok) {
        throw new Error("Error al crear la sesión de pago");
      }

      const data: CheckoutData = await response.json();
      setCheckoutData(data);

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
        Hola, {user.name ?? user.email}. Estás a un paso de acceder a {APP_NAME}.
      </p>

      {/* Order summary */}
      <div className="mt-8 rounded-2xl border border-border-soft bg-surface-800/50 p-6">
        <h2 className="text-lg font-semibold">Resumen del pedido</h2>
        <div className="mt-4 flex items-center justify-between border-b border-border-soft pb-4">
          <span className="text-text-300">{APP_NAME} — Licencia completa</span>
          <span className="font-bold">{PRICE_DISPLAY}</span>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <span className="font-semibold">Total</span>
          <span className="text-xl font-bold">{PRICE_DISPLAY}</span>
        </div>
      </div>

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
            He leído y acepto los{" "}
            <a
              href="/legal/terminos"
              target="_blank"
              className="text-primary-400 underline"
            >
              Términos y Condiciones
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

      <Button
        size="lg"
        className="mt-8 w-full"
        disabled={!canProceed || isCreating}
        onClick={handleCheckout}
      >
        {isCreating ? "Preparando pago..." : `Pagar ${PRICE_DISPLAY}`}
      </Button>

      <p className="mt-4 text-center text-xs text-text-500">
        Pago procesado por Wompi (Bancolombia). Tus datos de tarjeta nunca
        pasan por nuestros servidores.
      </p>
    </div>
  );
}

interface WompiWindow extends Window {
  WidgetCheckout?: new (config: Record<string, unknown>) => {
    open: (callback: (result: { transaction?: { status: string } }) => void) => void;
  };
}
