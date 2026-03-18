"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { APP_NAME } from "@/lib/constants";

type TransactionStatus = "APPROVED" | "DECLINED" | "VOIDED" | "ERROR" | "PENDING" | "loading" | "unknown";

const STATUS_CONFIG: Record<string, {
  icon: "success" | "error" | "pending";
  title: string;
  description: string;
  showDownload: boolean;
}> = {
  APPROVED: {
    icon: "success",
    title: "Compra exitosa",
    description: `Tu acceso a ${APP_NAME} ya est\u00e1 activo. Puedes descargar la app inmediatamente.`,
    showDownload: true,
  },
  DECLINED: {
    icon: "error",
    title: "Pago rechazado",
    description: "Tu pago no fue aprobado. Verifica los datos de tu medio de pago e int\u00e9ntalo de nuevo.",
    showDownload: false,
  },
  VOIDED: {
    icon: "error",
    title: "Transacci\u00f3n anulada",
    description: "Esta transacci\u00f3n fue anulada. No se realiz\u00f3 ning\u00fan cargo.",
    showDownload: false,
  },
  ERROR: {
    icon: "error",
    title: "Error en el pago",
    description: "Ocurri\u00f3 un error procesando tu pago. Int\u00e9ntalo de nuevo o usa un medio de pago diferente.",
    showDownload: false,
  },
  PENDING: {
    icon: "pending",
    title: "Pago pendiente",
    description: "Tu pago est\u00e1 siendo procesado. Recibir\u00e1s una confirmaci\u00f3n por correo cuando se complete.",
    showDownload: false,
  },
};

const ICONS = {
  success: (
    <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-success-500/15">
      <svg className="h-8 w-8 text-success-500" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </div>
  ),
  error: (
    <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-danger-500/15">
      <svg className="h-8 w-8 text-danger-500" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </div>
  ),
  pending: (
    <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-warning-500/15">
      <svg className="h-8 w-8 text-warning-500 animate-spin" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  ),
};

function ResultContent() {
  const searchParams = useSearchParams();
  const transactionId = searchParams.get("id");
  const [status, setStatus] = useState<TransactionStatus>("loading");

  useEffect(() => {
    if (!transactionId) {
      setStatus("unknown");
      return;
    }

    // Verify the actual transaction status from Wompi
    const wompiEnv = process.env.NEXT_PUBLIC_WOMPI_ENVIRONMENT === "production"
      ? "production"
      : "sandbox";
    const baseUrl = `https://${wompiEnv}.wompi.co/v1`;

    fetch(`${baseUrl}/transactions/${transactionId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        const txStatus = data?.data?.status as string;
        if (txStatus && txStatus in STATUS_CONFIG) {
          setStatus(txStatus as TransactionStatus);
        } else {
          setStatus("unknown");
        }
      })
      .catch(() => {
        // If we can't verify, show a cautious pending state
        setStatus("PENDING");
      });
  }, [transactionId]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-text-300">Verificando pago...</p>
      </div>
    );
  }

  const config = STATUS_CONFIG[status] ?? {
    icon: "pending" as const,
    title: "Estado desconocido",
    description: "No pudimos determinar el estado de tu pago. Revisa tu correo para confirmaci\u00f3n.",
    showDownload: false,
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-20 text-center">
      {ICONS[config.icon]}

      <h1 className="text-2xl font-bold">{config.title}</h1>
      <p className="mt-3 text-text-300">{config.description}</p>

      {transactionId && (
        <p className="mt-2 text-xs text-text-500">
          Referencia: {transactionId}
        </p>
      )}

      <div className="mt-8 space-y-3">
        {config.showDownload && (
          <Button size="lg" href="/descargar" className="w-full">
            Ir a la descarga
          </Button>
        )}
        {!config.showDownload && status !== "PENDING" && (
          <Button size="lg" href="/checkout" className="w-full">
            Intentar de nuevo
          </Button>
        )}
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
