import type { Metadata } from "next";
import { CONTACT_EMAIL, APP_NAME } from "@/lib/constants";

export const metadata: Metadata = {
  title: `Términos y Condiciones — ${APP_NAME}`,
};

export default function TermsPage() {
  return (
    <>
      <h1>Términos y Condiciones de Uso</h1>
      <p><strong>Última actualización:</strong> marzo de 2026</p>

      <h2>1. Descripción del servicio</h2>
      <p>
        {APP_NAME} es una plataforma de clonación y transformación de voz
        mediante inteligencia artificial. Permite a los usuarios crear perfiles
        de voz a partir de muestras de audio y transformar cualquier grabación
        para que adopte la identidad vocal del perfil seleccionado. El servicio
        está disponible como aplicación para Android y como aplicación web.
      </p>

      <h2>2. Aceptación de los términos</h2>
      <p>
        Al registrarse, realizar una compra o utilizar la plataforma, usted
        acepta estos Términos y Condiciones en su totalidad. Si no está de
        acuerdo con alguno de ellos, no utilice el servicio.
      </p>

      <h2>3. Requisitos de uso</h2>
      <ul>
        <li>Ser mayor de 18 años o contar con autorización del representante legal</li>
        <li>Proporcionar información veraz y actualizada durante el registro</li>
        <li>Contar con un dispositivo compatible (Android 8+ o navegador web moderno)</li>
        <li>Aceptar la Política de Privacidad y Tratamiento de Datos Personales</li>
      </ul>

      <h2>4. Consentimiento obligatorio para clonación de voz</h2>
      <p>
        <strong>
          El usuario se compromete a utilizar {APP_NAME} únicamente con voces
          para las cuales cuente con consentimiento explícito, libre e informado
          del titular de la voz.
        </strong>
      </p>
      <p>
        Queda terminantemente prohibido clonar, reproducir o transformar la voz
        de cualquier persona sin su autorización expresa y verificable. El
        incumplimiento de esta obligación constituye una violación grave de
        estos términos y puede acarrear:
      </p>
      <ul>
        <li>Suspensión inmediata de la cuenta sin derecho a reembolso</li>
        <li>Responsabilidad legal ante el titular de la voz afectada</li>
        <li>Acciones legales por parte de {APP_NAME} según la legislación colombiana aplicable</li>
      </ul>

      <h2>5. Propiedad intelectual</h2>
      <p>
        El software, diseño, código fuente, algoritmos, modelos de inteligencia
        artificial y demás elementos de {APP_NAME} son propiedad exclusiva de
        sus desarrolladores. La compra otorga una licencia de uso personal,
        no exclusiva, intransferible y no sublicenciable.
      </p>
      <p>
        Los audios generados por el usuario mediante la herramienta son
        propiedad del usuario, sujeto a que cuente con los derechos y
        consentimientos necesarios sobre el contenido fuente y la voz utilizada.
      </p>

      <h2>6. Limitación de responsabilidad</h2>
      <p>{APP_NAME} no se hace responsable de:</p>
      <ul>
        <li>El uso indebido de la herramienta por parte de los usuarios</li>
        <li>Daños derivados de la clonación de voz sin consentimiento</li>
        <li>Interrupciones temporales del servicio por mantenimiento o fuerza mayor</li>
        <li>La calidad de los resultados, que depende de la calidad de las muestras proporcionadas</li>
        <li>Pérdida de datos por causas ajenas al control de la plataforma</li>
      </ul>

      <h2>7. Uso aceptable</h2>
      <p>El usuario se compromete a no:</p>
      <ul>
        <li>Crear contenido fraudulento, difamatorio o engañoso con voces clonadas</li>
        <li>Suplantar la identidad de otra persona mediante voces sintéticas</li>
        <li>Distribuir, revender o sublicenciar el acceso a la aplicación</li>
        <li>Intentar realizar ingeniería inversa del software o los modelos</li>
        <li>Sobrecargar intencionalmente los servidores o la infraestructura</li>
      </ul>

      <h2>8. Pagos, suscripciones y facturaci&oacute;n</h2>
      <p>
        {APP_NAME} ofrece planes de suscripci&oacute;n mensual (Gratis, Pro, Unlimited).
        Los pagos se procesan a trav&eacute;s de Wompi (Bancolombia), pasarela
        certificada PCI DSS. Los datos de tarjeta nunca son almacenados ni
        procesados por {APP_NAME}. La confirmaci&oacute;n de pago se realiza
        exclusivamente mediante webhook verificado criptogr&aacute;ficamente.
      </p>
      <p>
        Las suscripciones se renuevan autom&aacute;ticamente cada mes. El usuario
        puede cancelar en cualquier momento desde su cuenta. La cancelaci&oacute;n
        surte efecto al final del per&iacute;odo de facturaci&oacute;n vigente.
        El plan gratuito est&aacute; siempre disponible sin necesidad de pago.
      </p>

      <h2>9. Modificaciones a los términos</h2>
      <p>
        {APP_NAME} se reserva el derecho de modificar estos términos en
        cualquier momento. Los cambios serán publicados en esta página con la
        fecha de actualización. El uso continuado del servicio después de la
        publicación de los cambios constituye aceptación de los nuevos términos.
      </p>

      <h2>10. Ley aplicable y jurisdicción</h2>
      <p>
        Estos términos se rigen por las leyes de la República de Colombia.
        Cualquier controversia se someterá a la jurisdicción de los tribunales
        competentes de Colombia.
      </p>

      <h2>11. Contacto</h2>
      <p>
        Para consultas sobre estos términos, escríbanos a{" "}
        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
      </p>
    </>
  );
}
