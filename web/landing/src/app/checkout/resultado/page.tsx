"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Button } from "@/components/ui/Button";
import { APP_NAME } from "@/lib/constants";

function ResultContent() {
  const searchParams = useSearchParams();
  const transactionId = searchParams.get("id");

  return (
    <div className="mx-auto max-w-lg px-4 py-20 text-center">
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-success-500/15">
        <svg
          className="h-8 w-8 text-success-500"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="2"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      <h1 className="text-2xl font-bold">¡Compra exitosa!</h1>
      <p className="mt-3 text-text-300">
        Tu acceso a {APP_NAME} ya está activo. Puedes descargar la app
        inmediatamente.
      </p>

      {transactionId && (
        <p className="mt-2 text-xs text-text-500">
          Referencia: {transactionId}
        </p>
      )}

      <div className="mt-8 space-y-3">
        <Button size="lg" href="/descargar" className="w-full">
          Ir a la descarga
        </Button>
        <Button variant="ghost" href="/" className="w-full">
          Volver al inicio
        </Button>
      </div>
    </div>
  );
}

export default function ResultPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-text-300">Verificando pago...</p>
        </div>
      }
    >
      <ResultContent />
    </Suspense>
  );
}
