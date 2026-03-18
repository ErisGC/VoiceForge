import { CONTACT_EMAIL, APP_NAME } from "@/lib/constants";

const LEGAL_LINKS = [
  { label: "Términos y Condiciones", href: "/legal/terminos" },
  { label: "Política de Privacidad", href: "/legal/privacidad" },
  { label: "Política de Reembolso", href: "/legal/reembolso" },
];

const NAV_LINKS = [
  { label: "Cómo funciona", href: "#como-funciona" },
  { label: "Demo", href: "#demo" },
  { label: "Precio", href: "#precio" },
  { label: "FAQ", href: "#faq" },
];

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border-soft bg-bg-900/50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div>
            <span className="text-lg font-bold">{APP_NAME}</span>
            <p className="mt-2 text-sm text-text-300">
              Clonación y transformación de voz con inteligencia artificial.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="text-sm font-semibold text-text-300 uppercase tracking-wider">
              Navegación
            </h3>
            <ul className="mt-3 space-y-2">
              {NAV_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-text-500 transition-colors hover:text-text-100"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-sm font-semibold text-text-300 uppercase tracking-wider">
              Legal
            </h3>
            <ul className="mt-3 space-y-2">
              {LEGAL_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-text-500 transition-colors hover:text-text-100"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-sm font-semibold text-text-300 uppercase tracking-wider">
              Contacto
            </h3>
            <p className="mt-3 text-sm text-text-500">
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="transition-colors hover:text-text-100"
              >
                {CONTACT_EMAIL}
              </a>
            </p>
          </div>
        </div>

        <div className="mt-12 border-t border-border-soft pt-6 text-center text-xs text-text-500">
          <p>
            &copy; {year} {APP_NAME}. Todos los derechos reservados. Colombia.
          </p>
          <p className="mt-1">
            El uso de esta herramienta para clonar voces sin consentimiento del
            titular está prohibido.
          </p>
        </div>
      </div>
    </footer>
  );
}
