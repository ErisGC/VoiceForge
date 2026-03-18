"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { PLANS } from "@/lib/constants";

export function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pt-32 pb-20 sm:px-6 md:pt-40 md:pb-28 lg:px-8">
      {/* Background glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-40 right-0 h-[600px] w-[600px] rounded-full opacity-20"
        style={{
          background:
            "radial-gradient(circle, rgba(109,124,255,0.4) 0%, transparent 70%)",
        }}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-32 -left-32 h-[400px] w-[400px] rounded-full opacity-15"
        style={{
          background:
            "radial-gradient(circle, rgba(79,209,255,0.35) 0%, transparent 70%)",
        }}
      />

      <div className="relative mx-auto max-w-6xl">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Copy */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-border-strong bg-surface-800/60 px-4 py-1.5 text-xs font-medium text-primary-300 backdrop-blur-sm">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 rounded-full bg-success-500 animate-pulse"
              />
              Disponible para Android y Web
            </span>

            <h1 className="mt-6 text-4xl leading-tight font-extrabold tracking-tight sm:text-5xl md:text-6xl">
              Transforma{" "}
              <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
                cualquier voz
              </span>
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-relaxed text-text-300">
              Guarda perfiles de voz, sube tu audio y obtén el resultado con la
              identidad vocal que elijas. Mismo contenido, nueva voz.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Button size="lg" href="#precio">
                Empezar gratis
              </Button>
              <Button variant="secondary" size="lg" href="#como-funciona">
                Ver c&oacute;mo funciona
              </Button>
            </div>

            <p className="mt-4 text-xs text-text-500">
              Plan gratuito disponible. Pro desde {PLANS.pro.priceDisplay}/mes.
            </p>
          </motion.div>

          {/* Visual mockup */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="relative hidden lg:block"
          >
            <div className="relative rounded-2xl border border-border-soft bg-surface-800/50 p-6 shadow-2xl backdrop-blur-sm">
              <div className="mb-4 flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-danger-500/60" />
                <div className="h-3 w-3 rounded-full bg-warning-500/60" />
                <div className="h-3 w-3 rounded-full bg-success-500/60" />
                <span className="ml-2 text-xs text-text-500">VoiceForge</span>
              </div>
              {/* Waveform visualization */}
              <div className="flex h-32 items-end justify-center gap-1 rounded-lg bg-bg-900/60 p-4">
                {[0.3, 0.6, 0.9, 0.5, 0.8, 0.4, 0.95, 0.55, 0.75, 0.35, 0.85, 0.5, 0.7, 0.4].map(
                  (h, i) => (
                    <motion.div
                      key={i}
                      className="w-3 rounded-full"
                      style={{
                        background:
                          i % 3 === 0
                            ? "linear-gradient(to top, #6D7CFF, #4FD1FF)"
                            : "linear-gradient(to top, rgba(109,124,255,0.4), rgba(158,123,255,0.6))",
                      }}
                      initial={{ height: 8 }}
                      animate={{ height: h * 100 }}
                      transition={{
                        duration: 0.8,
                        delay: i * 0.05,
                        repeat: Infinity,
                        repeatType: "reverse",
                        ease: "easeInOut",
                      }}
                    />
                  ),
                )}
              </div>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm font-medium text-primary-400">
                  Voz transformada
                </span>
                <span className="rounded-full bg-success-500/15 px-3 py-1 text-xs font-medium text-success-500 border border-success-500/30">
                  Completado
                </span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
