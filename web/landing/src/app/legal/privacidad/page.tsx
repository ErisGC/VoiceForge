import type { Metadata } from "next";
import { CONTACT_EMAIL, APP_NAME } from "@/lib/constants";

export const metadata: Metadata = {
  title: `Política de Privacidad — ${APP_NAME}`,
};

export default function PrivacyPage() {
  return (
    <>
      <h1>Política de Privacidad y Tratamiento de Datos Personales</h1>
      <p><strong>Última actualización:</strong> marzo de 2026</p>

      <p>
        En cumplimiento de la Ley 1581 de 2012 y el Decreto 1377 de 2013 de la
        República de Colombia, {APP_NAME} informa a los usuarios sobre el
        tratamiento que se da a los datos personales recolectados a través de
        esta plataforma.
      </p>

      <h2>1. Responsable del tratamiento</h2>
      <p>
        <strong>Nombre:</strong> {APP_NAME}<br />
        <strong>Correo de contacto:</strong>{" "}
        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a><br />
        <strong>País:</strong> Colombia
      </p>

      <h2>2. Datos que recolectamos</h2>
      <ul>
        <li>Nombre o alias proporcionado al registrarse</li>
        <li>Dirección de correo electrónico</li>
        <li>Información de autenticación gestionada por Auth0 (proveedor externo)</li>
        <li>Datos de pago (procesados exclusivamente por Wompi; nunca almacenamos datos de tarjeta)</li>
        <li>Muestras de audio y perfiles de voz creados voluntariamente por el usuario</li>
        <li>Registros de uso de la plataforma (auditoría interna)</li>
      </ul>

      <h2>3. Finalidad de la recolección</h2>
      <ul>
        <li>Proveer el servicio de clonación y transformación de voz</li>
        <li>Procesar pagos y verificar compras</li>
        <li>Generar enlaces de descarga personalizados</li>
        <li>Comunicar actualizaciones relevantes del servicio</li>
        <li>Cumplir obligaciones legales y requerimientos de autoridades competentes</li>
      </ul>

      <h2>4. Derechos del titular</h2>
      <p>
        De acuerdo con la Ley 1581 de 2012, usted tiene derecho a:
      </p>
      <ul>
        <li>Conocer, actualizar y rectificar sus datos personales</li>
        <li>Solicitar prueba de la autorización otorgada</li>
        <li>Ser informado sobre el uso que se le da a sus datos</li>
        <li>Revocar la autorización y/o solicitar la supresión de sus datos cuando considere que no se respetan los principios y derechos constitucionales y legales</li>
        <li>Acceder de forma gratuita a sus datos personales</li>
      </ul>

      <h2>5. Procedimiento para ejercer sus derechos</h2>
      <p>
        Puede ejercer sus derechos enviando una solicitud escrita a{" "}
        <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> indicando:
      </p>
      <ol>
        <li>Nombre completo y datos de contacto</li>
        <li>Descripción clara de los hechos y del derecho que desea ejercer</li>
        <li>Documentos que soporten la solicitud (si aplica)</li>
      </ol>
      <p>
        {APP_NAME} responderá dentro de los 10 días hábiles siguientes a la
        recepción de la solicitud. Si no fuera posible atenderla en dicho plazo,
        se informará al titular los motivos y la fecha en que será atendida,
        la cual no excederá los 5 días hábiles adicionales.
      </p>

      <h2>6. Transferencia y transmisión de datos</h2>
      <p>
        Sus datos pueden ser transmitidos a los siguientes proveedores para la
        prestación del servicio:
      </p>
      <ul>
        <li><strong>Auth0 (Okta):</strong> autenticación y gestión de identidad</li>
        <li><strong>Wompi (Bancolombia):</strong> procesamiento de pagos</li>
      </ul>
      <p>
        Estos proveedores cuentan con políticas de protección de datos
        equivalentes o superiores a las exigidas por la legislación colombiana.
      </p>

      <h2>7. Muestras de audio y consentimiento</h2>
      <p>
        La creación de perfiles de voz requiere consentimiento explícito. Al
        crear un perfil, usted confirma que cuenta con la autorización de la
        persona cuya voz se está clonando. {APP_NAME} no se hace responsable
        del uso indebido de la herramienta por parte de los usuarios.
      </p>

      <h2>8. Vigencia</h2>
      <p>
        Esta política es efectiva desde su fecha de publicación y permanecerá
        vigente mientras {APP_NAME} opere el servicio. Los datos personales
        serán conservados por el tiempo necesario para cumplir las finalidades
        descritas o según lo exija la ley aplicable.
      </p>
    </>
  );
}
