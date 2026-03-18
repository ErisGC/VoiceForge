"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionWrapper } from "@/components/ui/SectionWrapper";

interface FAQItem {
  question: string;
  answer: string;
}

const ITEMS: FAQItem[] = [
  {
    question: "¿Qué necesito para usar VoiceForge?",
    answer:
      "Solo un dispositivo Android o un navegador web moderno. Para la grabación de muestras de voz necesitas un micrófono (el de tu celular funciona). Para las transformaciones no necesitas hardware especial — el procesamiento corre en nuestros servidores.",
  },
  {
    question: "¿Funciona en mi dispositivo?",
    answer:
      "VoiceForge funciona en cualquier celular Android 8+ y en navegadores modernos (Chrome, Firefox, Edge, Safari) en computador. La versión de iOS está en desarrollo.",
  },
  {
    question: "¿Cuántas muestras de voz necesito?",
    answer:
      "Con 3 a 5 muestras claras de 10-30 segundos ya puedes obtener buenos resultados. Mientras más muestras variadas subas, más fiel será la transformación. El sistema te muestra un indicador de calidad que sube a medida que añades material.",
  },
  {
    question: "¿Cómo descargo la app después de pagar?",
    answer:
      "Inmediatamente después del pago exitoso accedes a tu página de descarga. Desde ahí bajas el APK de Android directamente. Solo necesitas habilitar la instalación desde orígenes desconocidos en tu celular.",
  },
  {
    question: "¿Puedo clonar cualquier voz?",
    answer:
      "VoiceForge exige consentimiento explícito para cada perfil de voz creado. Solo debes clonar voces de personas que te hayan autorizado expresamente. El uso sin consentimiento viola nuestros términos de servicio y puede tener consecuencias legales.",
  },
  {
    question: "¿Cuál es la política de reembolso?",
    answer:
      "Ofrecemos reembolso completo dentro de los 7 días posteriores a la compra si no has realizado más de 3 conversiones. Después de ese plazo o con más de 3 conversiones, no se otorgan reembolsos. Consulta nuestra Política de Reembolso para más detalles.",
  },
  {
    question: "¿Mis datos de pago están seguros?",
    answer:
      "Sí. Usamos Wompi como pasarela de pago, certificada PCI DSS. Los datos de tu tarjeta nunca pasan por nuestros servidores — son procesados directamente por Wompi de forma tokenizada y segura.",
  },
];

function AccordionItem({ item }: { item: FAQItem }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-border-soft">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between py-5 text-left transition-colors hover:text-primary-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-400"
        aria-expanded={open}
      >
        <span className="pr-4 text-sm font-semibold sm:text-base">
          {item.question}
        </span>
        <svg
          className={`h-5 w-5 shrink-0 text-text-500 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="2"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-sm leading-relaxed text-text-300">
              {item.answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function FAQ() {
  return (
    <SectionWrapper id="faq">
      <div className="text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Preguntas frecuentes
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-text-300">
          Todo lo que necesitas saber antes de empezar.
        </p>
      </div>

      <div className="mx-auto mt-12 max-w-3xl">
        {ITEMS.map((item) => (
          <AccordionItem key={item.question} item={item} />
        ))}
      </div>
    </SectionWrapper>
  );
}
