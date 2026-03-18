import type { Metadata } from "next";
import { CONTACT_EMAIL, APP_NAME } from "@/lib/constants";

export const metadata: Metadata = {
  title: `Política de Reembolso — ${APP_NAME}`,
};

export default function RefundPage() {
  return (
    <>
      <h1>Política de Reembolso</h1>
      <p><strong>Última actualización:</strong> marzo de 2026</p>

      <h2>1. Cancelaci&oacute;n de suscripci&oacute;n</h2>
      <p>
        El usuario puede cancelar su suscripci&oacute;n en cualquier momento.
        La cancelaci&oacute;n surte efecto al final del per&iacute;odo de
        facturaci&oacute;n vigente. No se realizan cobros adicionales despu&eacute;s
        de la cancelaci&oacute;n. El plan gratuito permanece disponible.
      </p>

      <h2>2. Condiciones para reembolso</h2>
      <p>
        {APP_NAME} otorga reembolso completo del primer pago de suscripci&oacute;n
        bajo las siguientes condiciones:
      </p>
      <ul>
        <li>
          La solicitud se realice dentro de los <strong>7 d&iacute;as calendario</strong>{" "}
          posteriores a la fecha del primer pago.
        </li>
        <li>
          El usuario no haya realizado m&aacute;s de <strong>3 conversiones de voz</strong>{" "}
          exitosas en la plataforma.
        </li>
      </ul>
      <p>
        Si ambas condiciones se cumplen, el reembolso ser&aacute; total. Si alguna
        no se cumple, no se otorgar&aacute; reembolso, pero el usuario puede
        cancelar la suscripci&oacute;n para evitar futuros cobros.
      </p>

      <h2>2. Procedimiento</h2>
      <ol>
        <li>
          Envíe un correo a{" "}
          <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> con el
          asunto &quot;Solicitud de reembolso&quot;.
        </li>
        <li>
          Incluya en el correo: el correo electrónico de su cuenta, la fecha
          de compra, y el motivo de la solicitud.
        </li>
        <li>
          Nuestro equipo revisará la solicitud y responderá en un plazo máximo
          de 5 días hábiles.
        </li>
        <li>
          Si la solicitud es aprobada, el reembolso se procesará por el mismo
          medio de pago utilizado en la compra, dentro de los 10 días hábiles
          siguientes a la aprobación.
        </li>
      </ol>

      <h2>4. Excepciones</h2>
      <p>No se otorgar&aacute; reembolso en los siguientes casos:</p>
      <ul>
        <li>La solicitud se presente despu&eacute;s de los 7 d&iacute;as calendario del primer pago</li>
        <li>El usuario haya realizado m&aacute;s de 3 conversiones exitosas</li>
        <li>La cuenta haya sido suspendida por violaci&oacute;n de los T&eacute;rminos y Condiciones</li>
        <li>Se detecte uso fraudulento o abusivo del servicio</li>
        <li>Se trate de una renovaci&oacute;n mensual (no del primer pago)</li>
      </ul>

      <h2>5. Contacto</h2>
      <p>
        Para solicitudes de reembolso o preguntas sobre esta política,
        comuníquese con nosotros en{" "}
        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
      </p>
    </>
  );
}
