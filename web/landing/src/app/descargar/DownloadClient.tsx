"use client";

import { useState } from "react";

/**
 * Client component for the download page.
 * Fetches a signed, temporary download URL from /api/download
 * and triggers the download.
 */
export function DownloadClient() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDownload() {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch("/api/download");
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error ?? "Error al generar el enlace de descarga");
      }

      const { downloadUrl } = await response.json();
      if (!downloadUrl) {
        throw new Error("No se recibi\u00f3 enlace de descarga");
      }

      // Open the signed download URL
      window.location.href = downloadUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="mt-10 rounded-2xl border border-primary-500/30 bg-surface-800/50 p-8 text-center">
      <h2 className="text-lg font-semibold">VoiceForge para Android</h2>
      <p className="mt-1 text-sm text-text-500">Versi\u00f3n 1.0.0 &middot; APK &middot; ~25 MB</p>

      <button
        onClick={handleDownload}
        disabled={isGenerating}
        className="mt-6 inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-primary-500 to-accent-violet px-8 py-4 text-base font-semibold text-white shadow-[0_0_24px_rgba(109,124,255,0.3)] transition-all duration-200 hover:shadow-[0_0_32px_rgba(109,124,255,0.45)] hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-400 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <svg
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="2"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
          />
        </svg>
        {isGenerating ? "Generando enlace..." : "Descargar APK"}
      </button>

      {error && (
        <p className="mt-3 text-sm text-danger-500">{error}</p>
      )}

      <p className="mt-3 text-xs text-text-500">
        El enlace de descarga es personal y expira en 1 hora.
      </p>
    </div>
  );
}
