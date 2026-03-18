import type { Metadata } from "next";
import { UserProvider } from "@auth0/nextjs-auth0/client";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoiceForge — Transforma cualquier voz",
  description:
    "Clona y transforma voces con inteligencia artificial. Guarda perfiles de voz, sube audio y obtén resultados con la identidad vocal que elijas. Disponible para Android y Web.",
  keywords: [
    "clonación de voz",
    "transformación de voz",
    "voice cloning",
    "IA de voz",
    "VoiceForge",
    "cambiar voz",
    "inteligencia artificial",
    "audio",
    "Colombia",
  ],
  authors: [{ name: "VoiceForge" }],
  openGraph: {
    title: "VoiceForge — Transforma cualquier voz",
    description:
      "Clona y transforma voces con IA. Guarda perfiles vocales, sube audio y genera resultados profesionales.",
    type: "website",
    locale: "es_CO",
    siteName: "VoiceForge",
  },
  twitter: {
    card: "summary_large_image",
    title: "VoiceForge — Transforma cualquier voz",
    description:
      "Clona y transforma voces con IA. Disponible para Android y Web.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-CO">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "VoiceForge",
              applicationCategory: "MultimediaApplication",
              operatingSystem: "Android, Web",
              offers: {
                "@type": "Offer",
                price: "5000",
                priceCurrency: "COP",
              },
              description:
                "Aplicación de clonación y transformación de voz con inteligencia artificial.",
            }),
          }}
        />
      </head>
      <body className="min-h-screen antialiased">
          <UserProvider>{children}</UserProvider>
        </body>
    </html>
  );
}
