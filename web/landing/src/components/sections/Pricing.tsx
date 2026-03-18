"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { SectionWrapper } from "@/components/ui/SectionWrapper";
import { PRICE_DISPLAY } from "@/lib/constants";

const INCLUDES = [
  "Acceso completo a la app (Android + Web)",
  "Perfiles de voz ilimitados",
  "Conversiones ilimitadas",
  "Grabación directa por micrófono",
  "Descarga de resultados en WAV",
  "Todas las actualizaciones incluidas",
  "Soporte por correo electrónico",
];

export function Pricing() {
  return (
    <SectionWrapper id="precio">
      <div className="text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Un solo pago, acceso completo
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-text-300">
          Sin suscripciones, sin costos ocultos. Paga una vez y usa VoiceForge
          para siempre.
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="mx-auto mt-12 max-w-md"
      >
        <div className="relative overflow-hidden rounded-3xl border border-primary-500/30 bg-surface-800/60 p-8 shadow-[0_0_40px_rgba(109,124,255,0.12)]">
          {/* Glow */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -top-20 -right-20 h-40 w-40 rounded-full opacity-30"
            style={{
              background:
                "radial-gradient(circle, rgba(109,124,255,0.5) 0%, transparent 70%)",
            }}
          />

          <div className="relative">
            <span className="inline-block rounded-full border border-primary-500/30 bg-primary-500/10 px-4 py-1 text-xs font-semibold text-primary-300">
              Pago único
            </span>

            <div className="mt-6 flex items-baseline gap-2">
              <span className="text-5xl font-extrabold tracking-tight">
                $5.000
              </span>
              <span className="text-lg text-text-300">COP</span>
            </div>
            <p className="mt-2 text-sm text-text-500">
              Aproximadamente $1.20 USD
            </p>

            <ul className="mt-8 space-y-3" role="list">
              {INCLUDES.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm">
                  <svg
                    className="mt-0.5 h-5 w-5 shrink-0 text-success-500"
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
                  <span className="text-text-300">{item}</span>
                </li>
              ))}
            </ul>

            <Button size="lg" href="/api/auth/login" className="mt-8 w-full">
              Comprar ahora
            </Button>

            <div className="mt-4 flex items-center justify-center gap-2 text-xs text-text-500">
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
                />
              </svg>
              Pago seguro con Wompi. Tus datos están protegidos.
            </div>
          </div>
        </div>
      </motion.div>
    </SectionWrapper>
  );
}
