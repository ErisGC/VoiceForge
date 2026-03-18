"use client";

import { motion } from "framer-motion";
import { SectionWrapper } from "@/components/ui/SectionWrapper";
import { PLANS, type PlanId } from "@/lib/constants";

const PLAN_ORDER: PlanId[] = ["free", "pro", "unlimited"];

const CHECK_ICON = (
  <svg
    className="mt-0.5 h-5 w-5 shrink-0 text-success-500"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth="2"
    stroke="currentColor"
    aria-hidden="true"
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
);

const LOCK_ICON = (
  <svg
    className="mt-0.5 h-5 w-5 shrink-0 text-text-500"
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
);

function PlanCard({ planId, index }: { planId: PlanId; index: number }) {
  const plan = PLANS[planId];
  const isHighlighted = planId === "pro";
  const isFree = planId === "free";

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className={`relative flex flex-col overflow-hidden rounded-3xl border p-8 ${
        isHighlighted
          ? "border-primary-500/40 bg-surface-800/70 shadow-[0_0_50px_rgba(109,124,255,0.15)]"
          : "border-border-soft bg-surface-800/40"
      }`}
    >
      {/* Badge */}
      {plan.badge && (
        <span
          className={`absolute top-0 right-0 rounded-bl-2xl px-4 py-1.5 text-xs font-bold ${
            isHighlighted
              ? "bg-primary-500 text-white"
              : "bg-accent-violet/20 text-accent-violet"
          }`}
        >
          {plan.badge}
        </span>
      )}

      {/* Glow for highlighted plan */}
      {isHighlighted && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-20 -right-20 h-40 w-40 rounded-full opacity-25"
          style={{
            background:
              "radial-gradient(circle, rgba(109,124,255,0.5) 0%, transparent 70%)",
          }}
        />
      )}

      <div className="relative flex flex-1 flex-col">
        <h3 className="text-xl font-bold">{plan.name}</h3>

        <div className="mt-4 flex items-baseline gap-2">
          {isFree ? (
            <span className="text-4xl font-extrabold tracking-tight">Gratis</span>
          ) : (
            <>
              <span className="text-4xl font-extrabold tracking-tight">
                ${plan.priceCop.toLocaleString("es-CO")}
              </span>
              <span className="text-text-300">COP/{plan.period}</span>
            </>
          )}
        </div>
        {!isFree && (
          <p className="mt-1 text-sm text-text-500">
            {plan.priceUsdApprox}/mes
          </p>
        )}

        {/* Features */}
        <ul className="mt-8 flex-1 space-y-3" role="list">
          {plan.features.map((feature) => (
            <li key={feature} className="flex items-start gap-3 text-sm">
              {CHECK_ICON}
              <span className="text-text-300">{feature}</span>
            </li>
          ))}
          {plan.limitations.map((limitation) => (
            <li key={limitation} className="flex items-start gap-3 text-sm">
              {LOCK_ICON}
              <span className="text-text-500">{limitation}</span>
            </li>
          ))}
        </ul>

        {/* CTA */}
        <a
          href={isFree ? "/api/auth/login" : `/checkout?plan=${planId}`}
          className={`mt-8 inline-flex w-full items-center justify-center rounded-full px-8 py-4 text-base font-semibold transition-all duration-200 ${
            isHighlighted
              ? "bg-gradient-to-r from-primary-500 to-accent-violet text-white shadow-[0_0_24px_rgba(109,124,255,0.3)] hover:shadow-[0_0_32px_rgba(109,124,255,0.45)] hover:brightness-110"
              : isFree
                ? "border border-border-strong bg-surface-800 text-text-100 hover:border-primary-400 hover:bg-surface-700"
                : "border border-primary-500/30 bg-primary-500/10 text-primary-300 hover:bg-primary-500/20"
          }`}
          role="button"
        >
          {isFree ? "Empezar gratis" : `Suscribirse — ${plan.priceDisplay}`}
        </a>
      </div>
    </motion.div>
  );
}

export function Pricing() {
  return (
    <SectionWrapper id="precio">
      <div className="text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Elige tu plan
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-text-300">
          Empieza gratis y escala cuando lo necesites. Cancela en cualquier momento.
        </p>
      </div>

      <div className="mx-auto mt-12 grid max-w-5xl gap-6 lg:grid-cols-3">
        {PLAN_ORDER.map((planId, i) => (
          <PlanCard key={planId} planId={planId} index={i} />
        ))}
      </div>

      <div className="mt-8 flex items-center justify-center gap-2 text-xs text-text-500">
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
        Pago seguro con Wompi (Bancolombia). Tus datos de tarjeta nunca pasan por nuestros servidores.
      </div>
    </SectionWrapper>
  );
}
