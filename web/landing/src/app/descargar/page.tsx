import { getSession } from "@auth0/nextjs-auth0";
import { redirect } from "next/navigation";
import type { Metadata } from "next";
import { APP_NAME, CONTACT_EMAIL } from "@/lib/constants";
import { DownloadClient } from "./DownloadClient";

export const metadata: Metadata = {
  title: `Descargar \u2014 ${APP_NAME}`,
  robots: { index: false, follow: false },
};

const INSTALL_STEPS = [
  {
    step: "1",
    title: "Descarga el APK",
    detail: "Haz clic en el bot\u00f3n de descarga. El archivo se guardar\u00e1 en tu carpeta de descargas.",
  },
  {
    step: "2",
    title: "Habilita or\u00edgenes desconocidos",
    detail:
      "Ve a Configuraci\u00f3n > Seguridad > Or\u00edgenes desconocidos (o Instalar apps desconocidas) y activa el permiso para tu navegador.",
  },
  {
    step: "3",
    title: "Instala la app",
    detail:
      "Abre el archivo APK descargado. Tu dispositivo te pedir\u00e1 confirmar la instalaci\u00f3n. Acepta y espera a que termine.",
  },
  {
    step: "4",
    title: "Abre VoiceForge",
    detail:
      "Busca VoiceForge en tu lista de aplicaciones y \u00e1brela. Inicia sesi\u00f3n con la misma cuenta que usaste para comprar.",
  },
];

export default async function DownloadPage() {
  const session = await getSession();

  if (!session?.user) {
    redirect("/api/auth/login");
  }

  // Check purchase status via internal API fetch
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  let hasPurchase = false;

  try {
    const response = await fetch(
      `${baseUrl}/api/payments/webhook?userId=${encodeURIComponent(session.user.sub as string)}`,
      { cache: "no-store" },
    );
    if (response.ok) {
      const data = await response.json();
      hasPurchase = data.hasPurchase === true;
    }
  } catch {
    // If check fails, show purchase-required state
  }

  if (!hasPurchase) {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-warning-500/15">
          <svg
            className="h-8 w-8 text-warning-500"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold">Compra necesaria</h1>
        <p className="mt-3 text-text-300">
          Para acceder a la descarga necesitas comprar {APP_NAME} primero.
        </p>
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- hash link to anchor on home page */}
        <a
          href="/#precio"
          className="mt-8 inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-primary-500 to-accent-violet px-8 py-4 text-base font-semibold text-white shadow-[0_0_24px_rgba(109,124,255,0.3)] transition-all duration-200 hover:shadow-[0_0_32px_rgba(109,124,255,0.45)] hover:brightness-110"
          role="button"
        >
          Ver precio y comprar
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-20">
      <div className="text-center">
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
              d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold">Tu descarga est\u00e1 lista</h1>
        <p className="mt-2 text-text-300">
          Hola, {session.user.name ?? session.user.email}. Gracias por comprar {APP_NAME}.
        </p>
      </div>

      {/* Download button — client component for signed URL generation */}
      <DownloadClient />

      {/* Play Store badge */}
      <div className="mt-6 rounded-xl border border-border-soft bg-bg-900/60 p-4 text-center">
        <span className="inline-flex items-center gap-2 text-sm text-text-300">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M3.609 1.814L13.792 12 3.61 22.186a.996.996 0 01-.61-.92V2.734a1 1 0 01.609-.92zm10.89 10.893l2.302 2.302-10.937 6.333 8.635-8.635zm3.199-3.199l2.243 1.3a1 1 0 010 1.733l-2.243 1.299L15.207 12l2.49-2.492zM5.864 2.658L16.8 8.99l-2.302 2.302-8.635-8.635z" />
          </svg>
          Pr\u00f3ximamente en Google Play
        </span>
      </div>

      {/* Installation instructions */}
      <div className="mt-12">
        <h2 className="text-xl font-bold">Instrucciones de instalaci\u00f3n</h2>
        <div className="mt-6 space-y-6">
          {INSTALL_STEPS.map((item) => (
            <div key={item.step} className="flex gap-4">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-500/15 text-sm font-bold text-primary-400">
                {item.step}
              </span>
              <div>
                <h3 className="font-semibold">{item.title}</h3>
                <p className="mt-1 text-sm text-text-300">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Changelog */}
      <div className="mt-12 rounded-xl border border-border-soft bg-surface-800/30 p-6">
        <h2 className="text-lg font-semibold">Changelog</h2>
        <div className="mt-3">
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-success-500/15 px-2 py-0.5 text-xs font-medium text-success-500">
              v1.0.0
            </span>
            <span className="text-xs text-text-500">Marzo 2026</span>
          </div>
          <ul className="mt-2 space-y-1 text-sm text-text-300">
            <li>Creaci\u00f3n de perfiles de voz con m\u00faltiples muestras</li>
            <li>Conversi\u00f3n de voz con Seed-VC (alta calidad)</li>
            <li>Grabaci\u00f3n directa por micr\u00f3fono</li>
            <li>Reproductor de resultados integrado</li>
            <li>Soporte para Android y Web</li>
          </ul>
        </div>
      </div>

      {/* Support */}
      <div className="mt-8 text-center text-sm text-text-500">
        \u00bfProblemas con la instalaci\u00f3n?{" "}
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className="text-primary-400 underline"
        >
          Cont\u00e1ctanos
        </a>
      </div>
    </div>
  );
}
