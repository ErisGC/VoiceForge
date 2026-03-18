"use client";

import { motion } from "framer-motion";
import { SectionWrapper } from "@/components/ui/SectionWrapper";

const SAMPLES = [
  { label: "Voz original", subtitle: "Audio fuente sin transformar" },
  { label: "Voz transformada", subtitle: "Resultado con perfil aplicado" },
];

export function Demo() {
  return (
    <SectionWrapper id="demo" className="bg-bg-900/50">
      <div className="text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Escucha la diferencia
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-text-300">
          Mismo contenido hablado, identidad vocal completamente distinta.
        </p>
      </div>

      <div className="mt-12 grid gap-6 md:grid-cols-2">
        {SAMPLES.map((sample, i) => (
          <motion.div
            key={sample.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.15 }}
            className="rounded-2xl border border-border-soft bg-surface-800/50 p-6"
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-semibold">{sample.label}</span>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium border ${
                  i === 0
                    ? "border-text-500/30 bg-text-500/10 text-text-300"
                    : "border-primary-500/30 bg-primary-500/10 text-primary-300"
                }`}
              >
                {i === 0 ? "Original" : "VoiceForge"}
              </span>
            </div>
            <p className="mb-4 text-xs text-text-500">{sample.subtitle}</p>

            {/* Audio player placeholder */}
            <div className="flex items-center gap-3 rounded-xl bg-bg-900/60 p-4">
              <button
                aria-label={`Reproducir ${sample.label.toLowerCase()}`}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-500/20 text-primary-400 transition-colors hover:bg-primary-500/30 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-400"
              >
                <svg
                  className="h-5 w-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
              </button>
              <div className="flex-1">
                <div className="flex h-8 items-end gap-0.5">
                  {Array.from({ length: 32 }).map((_, j) => {
                    const height = Math.max(
                      4,
                      Math.sin(j * 0.4 + i * 2) * 20 + Math.random() * 12,
                    );
                    return (
                      <div
                        key={j}
                        className="flex-1 rounded-full"
                        style={{
                          height: `${height}px`,
                          backgroundColor:
                            i === 1
                              ? `rgba(109, 124, 255, ${0.3 + height / 60})`
                              : `rgba(255, 255, 255, ${0.1 + height / 80})`,
                        }}
                      />
                    );
                  })}
                </div>
              </div>
              <span className="text-xs text-text-500">0:00</span>
            </div>

            <p className="mt-3 text-center text-xs text-text-500 italic">
              Disponible próximamente
            </p>
          </motion.div>
        ))}
      </div>

      {/* Transformation visual */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="mx-auto mt-12 flex max-w-md items-center justify-center gap-4 text-center"
      >
        <div className="rounded-xl border border-border-soft bg-surface-800/40 px-5 py-3">
          <span className="text-2xl" role="img" aria-label="audio fuente">🗣️</span>
          <p className="mt-1 text-xs text-text-300">Tu audio</p>
        </div>
        <div className="flex flex-col items-center">
          <svg
            className="h-6 w-12 text-primary-400"
            fill="none"
            viewBox="0 0 48 24"
            aria-hidden="true"
          >
            <path
              d="M0 12h40m0 0l-6-6m6 6l-6 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="mt-1 text-xs font-medium text-primary-400">
            VoiceForge AI
          </span>
        </div>
        <div className="rounded-xl border border-primary-500/30 bg-primary-500/5 px-5 py-3">
          <span className="text-2xl" role="img" aria-label="resultado">✨</span>
          <p className="mt-1 text-xs text-primary-300">Voz transformada</p>
        </div>
      </motion.div>
    </SectionWrapper>
  );
}
