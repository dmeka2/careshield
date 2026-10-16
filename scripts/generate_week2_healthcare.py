"""Create deterministic fictional healthcare examples for CareShield Week 2."""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "seed_corpus" / "processed"
FIELDS = ["id", "channel", "language", "text", "label", "family", "source"]

SCAM_TEMPLATES = {
    "insurance_enrollment": {
        "en": [
            "Your {plan} health plan was approved. Send your Social Security number {deadline} to activate it.",
            "Coverage alert: the {plan} enrollment desk needs your bank card at {site} to prevent cancellation {deadline}.",
            "Claim a zero-dollar {plan} policy. Enter your Medicare number at {site} {deadline}.",
            "Your Marketplace application was suspended. Reply with your one-time login code {deadline} to restore {plan} coverage.",
            "An agent will secure your {plan} benefits, but you must wire {amount} for mandatory enrollment {deadline}.",
        ],
        "es": [
            "Su plan de salud {plan} fue aprobado. Envíe su número de Seguro Social {deadline} para activarlo.",
            "Alerta de cobertura: la oficina de {plan} pide su tarjeta bancaria en {site} para evitar la cancelación {deadline}.",
            "Obtenga una póliza {plan} sin costo. Ingrese su número de Medicare en {site} {deadline}.",
            "Su solicitud de seguros fue suspendida. Envíe el código temporal de acceso {deadline} para restaurar el plan {plan}.",
            "Un agente promete sus beneficios {plan}, pero debe enviar {amount} por transferencia para inscribirse {deadline}.",
        ],
    },
    "medical_debt": {
        "en": [
            "Your medical balance of {amount} must be paid with gift cards {deadline}, or an arrest warrant will follow.",
            "A hospital collector demands {amount} by bank transfer {deadline} and refuses to send written debt verification.",
            "You owe {amount} for unknown treatment. Do not contact your clinic; pay at {site} {deadline}.",
            "Pay {amount} in cryptocurrency {deadline} to stop collectors from canceling your benefits.",
            "An unpaid medical bill for {amount} will be sent to law enforcement unless you use a payment app {deadline}.",
        ],
        "es": [
            "Debe pagar la deuda médica de {amount} con tarjetas de regalo {deadline} o emitiremos una orden de arresto.",
            "Un cobrador hospitalario exige {amount} por transferencia {deadline} y se niega a verificar la deuda por escrito.",
            "Debe {amount} por un tratamiento desconocido. No llame a la clínica; pague en {site} {deadline}.",
            "Pague {amount} en criptomonedas {deadline} para evitar que le quiten sus beneficios.",
            "Una factura médica de {amount} será enviada a la policía si no paga por una aplicación {deadline}.",
        ],
    },
    "pharmacy": {
        "en": [
            "Your prescription order is held. Enter your portal password at {site} {deadline} to release it.",
            "Buy prescription medicine without a doctor's prescription for {amount}. Pay using gift cards {deadline}.",
            "Your discount medication is reserved; share a credit-card verification code at {site} {deadline}.",
            "Limited pharmacy offer: prescription refills for {amount}, no doctor needed. Pay in cryptocurrency {deadline}.",
            "Your medication delivery is blocked. Upload an ID photo and payment card at {site} {deadline}.",
        ],
        "es": [
            "Su pedido de farmacia está retenido. Ingrese la contraseña de su portal en {site} {deadline} para liberarlo.",
            "Compre medicamentos recetados sin receta médica por {amount}. Pague con tarjetas de regalo {deadline}.",
            "Su medicamento con descuento está reservado; envíe su código de tarjeta en {site} {deadline}.",
            "Oferta limitada: resurtidos de recetas por {amount}, sin médico. Pague con criptomonedas {deadline}.",
            "La entrega de sus medicamentos está bloqueada. Suba foto de su identificación y tarjeta en {site} {deadline}.",
        ],
    },
    "phishing": {
        "en": [
            "New lab results are ready. Enter your patient portal password at {site} {deadline}.",
            "Your patient portal will close {deadline}; reply with the security code sent to your phone.",
            "Appointment payment failed. Submit your bank login details at {site} {deadline}.",
            "A health record was shared with you. Enter your email account password at {site} {deadline}.",
            "A clinic security team needs your one-time verification code {deadline} to prevent deletion of your records at {site}.",
        ],
        "es": [
            "Sus nuevos resultados médicos están listos. Ingrese la contraseña del portal en {site} {deadline}.",
            "Su portal de pacientes cerrara {deadline}; responda con el código de seguridad recibido por texto.",
            "Fallo el pago de una cita. Ingrese las credenciales bancarias en {site} {deadline}.",
            "Compartieron su expediente médico. Introduzca la contraseña de su correo en {site} {deadline}.",
            "El equipo de seguridad de su clínica exige un código temporal {deadline} para no borrar sus archivos en {site}.",
        ],
    },
    "impersonation": {
        "en": [
            "Medicare card replacement required. Send your Medicare number at {site} {deadline}.",
            "HHS benefits office offers a free {item}. Reply with your Medicare ID {deadline}.",
            "State Medicaid alert: you will lose coverage {deadline} unless you send your Social Security number.",
            "Your provider's billing office wants a photo of your ID and payment card at {site} {deadline}.",
            "A government health representative offers a free {item} if you confirm your Medicare number {deadline}.",
        ],
        "es": [
            "Se requiere reemplazar su tarjeta Medicare. Envíe su número de Medicare en {site} {deadline}.",
            "La oficina de beneficios de HHS ofrece gratis un {item}. Responda con su número de Medicare {deadline}.",
            "Alerta de Medicaid: perderá su cobertura {deadline} si no envia su número de Seguro Social.",
            "La oficina de cobros de su médico exige foto de su identificación y tarjeta en {site} {deadline}.",
            "Un representante de salud del gobierno ofrece un {item} gratis si confirma su número de Medicare {deadline}.",
        ],
    },
}

LEGIT_TEMPLATES = {
    "appointment": {
        "en": [
            "Appointment reminder: your visit at {clinic} is on {day} at {time}. Call your usual number to reschedule.",
            "Your appointment for {day} at {time} is confirmed. Review details using your established patient portal.",
            "If the {day} visit no longer works, contact {clinic} through its regular phone number.",
        ],
        "es": [
            "Recordatorio: su cita en {clinic} es el {day} a las {time}. Llame al número habitual para cambiarla.",
            "Su cita del {day} a las {time} está confirmada. Revise los detalles en su portal habitual.",
            "Si no puede asistir el {day}, llame a {clinic} mediante su número telefonico habitual.",
        ],
    },
    "pharmacy": {
        "en": [
            "Your refill request at {clinic} was received for pickup on {day}. We will send an update when ready.",
            "Your prescription pickup is planned for {day} after {time}. Contact your usual pharmacy with questions.",
            "A routine medication review is booked for {day} at {time}. No payment or password is requested in this reminder.",
        ],
        "es": [
            "Recibimos su solicitud de receta en {clinic} para el {day}. Enviaremos otro aviso cuando esté lista.",
            "Su receta estara disponible el {day} despues de las {time}. Consulte a su farmacia habitual.",
            "Tiene una revisión rutinaria de medicamentos el {day} a las {time}. Este aviso no pide dinero ni contraseñas.",
        ],
    },
    "insurance": {
        "en": [
            "Your Explanation of Benefits for {day} is available through your usual insurance account. This is not a bill.",
            "Your {day} coverage summary has been mailed. Call the number printed on your member card with questions.",
            "Your routine insurance review is scheduled for {day}. Consult your existing policy documents for details.",
        ],
        "es": [
            "Su explicación de beneficios del {day} está en su cuenta de seguro habitual. Esto no es una factura.",
            "Su resumen de cobertura del {day} fue enviado por correo. Llame al número impreso en su tarjeta.",
            "Su revisión habitual del seguro es el {day}. Consulte los documentos de su póliza actual.",
        ],
    },
    "billing": {
        "en": [
            "A billing statement for your {day} visit is available in your established patient portal.",
            "Your clinic payment receipt dated {day} was posted. No additional payment is requested in this notice.",
            "Questions about the bill from {day}? Call the number shown on your original clinic statement.",
        ],
        "es": [
            "El estado de cuenta de su cita del {day} está en su portal habitual de pacientes.",
            "Se registró su recibo de pago de la clínica del {day}. Este aviso no solicita otro pago.",
            "¿Tiene preguntas sobre la factura del {day}? Llame al número de su factura original.",
        ],
    },
    "lab_results": {
        "en": [
            "Your lab results from {day} are available in your normal patient portal at portal-care.example.",
            "A routine lab follow-up at {clinic} is set for {day} at {time}. Use your regular phone number for changes.",
            "Your clinician posted a record update for {day}. Use your usual portal or contact {clinic} directly.",
        ],
        "es": [
            "Sus resultados de laboratorio del {day} están en su portal habitual portal-care.example.",
            "Tiene seguimiento de laboratorio en {clinic} el {day} a las {time}. Llame al número habitual para cambios.",
            "Su profesional de salud actualizo el expediente del {day}. Use su portal habitual o llame a {clinic}.",
        ],
    },
}

SCAM_VARS = {
    "en": [
        {"plan": "Community Basic", "amount": "$175", "deadline": "within one hour", "site": "member-review.example", "item": "screening kit"},
        {"plan": "Preferred Choice", "amount": "$430", "deadline": "by tonight", "site": "benefit-confirm.example", "item": "medical test"},
        {"plan": "Select Plus", "amount": "$960", "deadline": "before tomorrow morning", "site": "claims-check.example", "item": "medical device"},
    ],
    "es": [
        {"plan": "Community Basic", "amount": "$175", "deadline": "en una hora", "site": "member-review.example", "item": "kit de prueba"},
        {"plan": "Preferred Choice", "amount": "$430", "deadline": "esta noche", "site": "benefit-confirm.example", "item": "examen médico"},
        {"plan": "Select Plus", "amount": "$960", "deadline": "antes de mañana", "site": "claims-check.example", "item": "dispositivo médico"},
    ],
}

LEGIT_VARS = {
    "en": [
        {"day": "Monday", "time": "2:00 PM", "clinic": "your regular clinic"},
        {"day": "Thursday", "time": "9:30 AM", "clinic": "your usual care office"},
    ],
    "es": [
        {"day": "lunes", "time": "14:00", "clinic": "su clínica habitual"},
        {"day": "jueves", "time": "09:30", "clinic": "su consultorio habitual"},
    ],
}

SUBJECTS = {
    "insurance_enrollment": ("Coverage action requested", "Acción de cobertura"),
    "medical_debt": ("Medical balance notice", "Aviso de deuda médica"),
    "pharmacy": ("Pharmacy update", "Aviso de farmacia"),
    "phishing": ("Patient account notice", "Aviso de cuenta de paciente"),
    "impersonation": ("Benefits notification", "Notificación de beneficios"),
    "appointment": ("Appointment information", "Información de cita"),
    "insurance": ("Insurance information", "Información de seguro"),
    "billing": ("Billing update", "Actualización de facturacion"),
    "lab_results": ("Lab update", "Actualización de laboratorio"),
}


def build_rows():
    """Build stable rows; IDs encode family, language, channel and template."""
    rows = []

    for family, translations in SCAM_TEMPLATES.items():
        for lang, templates in translations.items():
            for channel in ("sms", "email"):
                for template_no, template in enumerate(templates, 1):
                    for variation_no, args in enumerate(SCAM_VARS[lang], 1):
                        text = template.format(**args)
                        if channel == "email":
                            subject = SUBJECTS[family][lang == "es"]
                            prefix = "Asunto" if lang == "es" else "Subject"
                            text = f"{prefix}: {subject}\n\n{text}"
                        rows.append({
                            "id": f"syn-scam-{family}-{lang}-{channel}-t{template_no:02d}-v{variation_no:02d}",
                            "channel": channel,
                            "language": lang,
                            "text": text,
                            "label": "scam",
                            "family": family,
                            "source": "careshield_synthetic_week2",
                        })

    for theme, translations in LEGIT_TEMPLATES.items():
        for lang, templates in translations.items():
            for channel in ("sms", "email"):
                for template_no, template in enumerate(templates, 1):
                    for variation_no, args in enumerate(LEGIT_VARS[lang], 1):
                        text = template.format(**args)
                        if channel == "email":
                            subject = SUBJECTS[theme][lang == "es"]
                            prefix = "Asunto" if lang == "es" else "Subject"
                            text = f"{prefix}: {subject}\n\n{text}"
                        rows.append({
                            "id": f"syn-legit-{theme}-{lang}-{channel}-t{template_no:02d}-v{variation_no:02d}",
                            "channel": channel,
                            "language": lang,
                            "text": text,
                            "label": "legitimate",
                            "family": "none",
                            "source": "careshield_synthetic_week2",
                        })

    ids = [row["id"] for row in rows]
    texts = [(row["channel"], row["text"]) for row in rows]
    counts = Counter(row["label"] for row in rows)

    if len(rows) != 420 or counts != {"scam": 300, "legitimate": 120}:
        raise ValueError("Unexpected synthetic corpus size or label balance.")
    if len(set(ids)) != len(rows) or len(set(texts)) != len(rows):
        raise ValueError("Duplicate IDs or messages found.")
    if any(not 1 <= len(row["text"]) <= 10000 for row in rows):
        raise ValueError("Message length outside supported bounds.")

    return rows


def main():
    rows = build_rows()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT / "healthcare_synthetic_week2.csv"
    json_path = OUTPUT / "healthcare_synthetic_week2.json"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Generated 420 fictional healthcare messages:")
    print("  Scam: 300 (60 in each of five families)")
    print("  Legitimate: 120")
    print("  English: 210 | Spanish: 210")
    print("  Channel: 210 SMS | 210 email")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")
    print("Review template diversity and Spanish phrasing before model evaluation.")


if __name__ == "__main__":
    main()
