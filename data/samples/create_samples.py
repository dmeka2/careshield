
import csv
import json
from pathlib import Path

from careshield.ingest import BatchInput

# All messages below are fictional.
# No actual patient or victim information is used.

messages = [
    # Fake insurance enrollment
    ("m001", "sms",
     ("You qualify for a guaranteed $0 health plan. "
     "Send your Social Security number before midnight.")),

    ("m002", "email",
     ("URGENT: Your health insurance enrollment expires today. "
     "Complete verification at enrollment-help.example.")),

    ("m003", "sms",
     ("Su seguro medico gratuito esta aprobado. "
     "Envie su numero de Seguro Social para activar el plan.")),

    # Medical debt collection scams
    ("m004", "sms",
     ("You owe $850 for hospital services. Pay today using "
     "gift cards or legal action will begin.")),

    ("m005", "email",
     ("FINAL NOTICE: Your medical debt requires immediate "
     "payment. We cannot provide written verification.")),

    ("m006", "sms",
     ("Tiene una deuda medica pendiente. "
     "Pague hoy por transferencia o enfrentara acciones legales.")),

    # Prescription and pharmacy scams
    ("m007", "email",
     ("Buy prescription weight-loss medication without a "
     "prescription. Pay with cryptocurrency today.")),

    ("m008", "sms",
     ("LIMITED OFFER: Brand-name prescription drugs at "
     "90 percent off. Only 10 minutes remaining.")),

    ("m009", "sms",
     ("Compre medicamentos sin receta a mitad de precio. "
     "Solo aceptamos pagos con criptomonedas.")),

    # Phishing scams
    ("m010", "email",
     ("Your lab results are ready. Enter your patient portal "
     "password at patient-results.example to view them.")),

    ("m011", "sms",
     ("Your healthcare account will be suspended in one hour. "
     "Confirm your login code at secure-login.example.")),

    ("m012", "email",
     ("Sus resultados medicos estan disponibles. "
     "Ingrese su contrasena en portal-salud.example.")),

    # Medicare / Medicaid impersonation
    ("m013", "sms",
     ("MEDICARE ALERT: Your new Medicare card is ready. "
     "Reply with your Medicare number to activate it.")),

    ("m014", "email",
     ("Government health benefits notice: Receive free "
     "medical equipment by confirming your Medicare ID.")),

    ("m015", "sms",
     ("AVISO DE MEDICAID: Perdera su cobertura hoy. "
     "Verifique sus datos en cobertura-ayuda.example.")),

    # Legitimate healthcare examples
    ("m016", "sms",
     ("Appointment reminder: Your clinic visit is scheduled "
     "for Monday at 2 PM. Contact your clinic to reschedule.")),

    ("m017", "email",
     ("Your monthly Explanation of Benefits is available "
     "through your usual insurance account.")),

    ("m018", "sms",
     ("Your prescription is ready for pickup. "
     "Please bring identification to the pharmacy.")),

    ("m019", "email",
     ("Your appointment was successfully canceled. "
     "Contact your clinic if you would like to reschedule.")),

    ("m020", "sms",
     ("Recordatorio: Tiene una cita medica el martes. "
     "Llame directamente a su clinica si necesita cambiarla.")),
]

rows = [
    {"id": message_id, "channel": channel, "text": text}
    for message_id, channel, text in messages
]

# Confirm the rows satisfy the CareShield input schema.
BatchInput.model_validate(rows)

output_dir = Path(__file__).resolve().parent

# Generate CSV
csv_path = output_dir / "sample.csv"

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file, fieldnames=["id", "channel", "text"]
    )
    writer.writeheader()
    writer.writerows(rows)

# Generate JSON
json_path = output_dir / "sample.json"

with json_path.open("w", encoding="utf-8") as file:
    json.dump(rows, file, indent=2, ensure_ascii=False)

print(f"Created {len(rows)} synthetic messages.")
print(f"CSV: {csv_path}")
print(f"JSON: {json_path}")
print("Pydantic validation passed.")
