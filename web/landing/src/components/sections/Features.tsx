"use client";

import { motion } from "framer-motion";
import { SectionWrapper } from "@/components/ui/SectionWrapper";

interface Feature {
  icon: string;
  title: string;
  description: string;
}

const FEATURES: Feature[] = [
  {
    icon: "🎙️",
    title: "Graba y guarda voces",
    description:
      "Crea perfiles de voz desde micrófono o archivos de audio. Cada perfil representa una identidad vocal única que puedes reutilizar.",
  },
  {
    icon: "🔄",
    title: "Transforma cualquier audio",
    description:
      "Sube un audio con cualquier voz y VoiceForge lo transforma para que suene con la identidad vocal del perfil que elijas.",
  },
  {
    icon: "📈",
    title: "Más muestras, mejor calidad",
    description:
      "El sistema mide la calidad de cada perfil. Mientras más muestras claras y variadas subas, más fiel y natural será la transformación.",
  },
  {
    icon: "📱",
    title: "Android y Web",
    description:
      "Una sola cuenta para usar desde tu celular Android o desde el navegador. Tus perfiles y resultados se sincronizan automáticamente.",
  },
];

const STEPS = [
  { step: "01", label: "Crea un perfil de voz", detail: "Graba o sube muestras de la voz que quieres clonar." },
  { step: "02", label: "Sube el audio fuente", detail: "El audio con el contenido que deseas transformar." },
  { step: "03", label: "Recibe tu resultado", detail: "Descarga el audio con la voz del perfil y el contenido del audio fuente." },
];

export function Features() {
  return (
    <SectionWrapper id="como-funciona">
      <div className="text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          ¿Qué es{" "}
          <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
            VoiceForge
          </span>
          ?
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-text-300">
          Una herramienta de clonación y transformación de voz impulsada por
          inteligencia artificial, diseñada para resultados profesionales.
        </p>
      </div>

      {/* Feature cards */}
      <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((feature, i) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: i * 0.1 }}
            className="group rounded-2xl border border-border-soft bg-surface-800/50 p-6 transition-all duration-300 hover:border-primary-500/30 hover:bg-surface-800/80 hover:-translate-y-1"
          >
            <span className="text-3xl" role="img" aria-label={feature.title}>
              {feature.icon}
            </span>
            <h3 className="mt-4 text-lg font-bold">{feature.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-text-300">
              {feature.description}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Step-by-step flow */}
      <div className="mt-20">
        <h3 className="text-center text-2xl font-bold">Cómo funciona</h3>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {STEPS.map((item, i) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className="relative text-center"
            >
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-accent-violet text-lg font-bold text-white shadow-[0_0_20px_rgba(109,124,255,0.25)]">
                {item.step}
              </span>
              {i < STEPS.length - 1 && (
                <div
                  aria-hidden="true"
                  className="absolute top-7 left-[calc(50%+2rem)] hidden h-px w-[calc(100%-4rem)] bg-gradient-to-r from-primary-500/40 to-transparent md:block"
                />
              )}
              <h4 className="mt-4 text-lg font-semibold">{item.label}</h4>
              <p className="mt-2 text-sm text-text-300">{item.detail}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </SectionWrapper>
  );
}
