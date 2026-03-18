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

      <h2>1. Condiciones para reembolso</h2>
      <p>
        {APP_NAME} otorga reembolso completo del valor pagado bajo las
        siguientes condiciones:
      </p>
      <ul>
        <li>
          La solicitud se realice dentro de los <strong>7 días calendario</strong>{" "}
          posteriores a la fecha de compra.
        </li>
        <li>
          El usuario no haya realizado más de <strong>3 conversiones de voz</strong>{" "}
          exitosas en la plataforma.
        </li>
      </ul>
      <p>
        Si ambas condiciones se cumplen, el reembolso será total. Si alguna
        no se cumple, no se otorgará reembolso.
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

      <h2>3. Excepciones</h2>
      <p>No se otorgará reembolso en los siguientes casos:</p>
      <ul>
        <li>La solicitud se presente después de los 7 días calendario</li>
        <li>El usuario haya realizado más de 3 conversiones exitosas</li>
        <li>La cuenta haya sido suspendida por violación de los Términos y Condiciones</li>
        <li>Se detecte uso fraudulento o abusivo del servicio</li>
      </ul>

      <h2>4. Contacto</h2>
      <p>
        Para solicitudes de reembolso o preguntas sobre esta política,
        comuníquese con nosotros en{" "}
        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
      </p>
    </>
  );
}
