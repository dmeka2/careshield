# CareShield Scam Taxonomy

## Purpose

This document defines the initial healthcare-scam taxonomy used by CareShield.

The taxonomy supports five scam families:

1. Fake insurance enrollment and Marketplace impersonation

2. Medical debt collection scams

3. Prescription and pharmacy scams

4. Phishing (credential and payment harvesting)

5. Impersonation of Medicare, Medicaid, HHS-OIG, or a healthcare provider

Each indicator has:

- a unique rule ID,

- a severity weight,

- a short description,

- a plain-language English explanation, and

- a plain-language Spanish explanation.

These indicators are intended to support the deterministic CareShield rules engine. A single indicator does not automatically prove that a message is fraudulent. CareShield should consider multiple signals together and later combine them with threat-intelligence and machine-learning evidence.

## Weighting Guide

| Weight | Meaning |

|---|---|

| Low | Weak supporting signal that should rarely raise risk substantially by itself. |

| Medium | Meaningful suspicious signal that increases risk when combined with other evidence. |

| High | Strong scam indicator involving sensitive information, deceptive identity claims, threats, unusual payments, or other high-risk behavior. |

## 1. Fake Insurance Enrollment and Marketplace Impersonation

### ENR-01 — Artificial enrollment urgency

- **Weight:** Medium

- **Indicator:** The message claims the recipient must enroll, renew, or confirm coverage immediately or within an unusually short deadline.

- **English explanation:** The message pressures you to make a health-insurance decision immediately. Scammers often create false deadlines so people act before checking whether the offer is real.

- **Spanish explanation:** El mensaje le presiona para tomar una decisión sobre su seguro médico inmediatamente. Los estafadores suelen crear fechas límite falsas para que las personas actúen antes de verificar si la oferta es real.

### ENR-02 — Request for highly sensitive identifiers

- **Weight:** High

- **Indicator:** An unsolicited insurance message asks for a Social Security number, Medicare or Medicaid number, bank account, card information, or login credentials.

- **English explanation:** The message unexpectedly asks for sensitive personal or financial information. Legitimate organizations should not request this information through an unverified message.

- **Spanish explanation:** El mensaje solicita inesperadamente información personal o financiera confidencial. Las organizaciones legítimas no deben pedir esta información mediante un mensaje no verificado.

### ENR-03 — Government program on a non-government or lookalike domain

- **Weight:** High

- **Indicator:** A message claims to represent HealthCare.gov, Medicare, Medicaid, or another government healthcare program but directs the user to an unrelated, misspelled, or non-government website.

- **English explanation:** The message claims to represent a government healthcare program, but the website does not match the official government domain.

- **Spanish explanation:** El mensaje afirma representar un programa gubernamental de salud, pero el sitio web no coincide con el dominio oficial del gobierno.

### ENR-04 — Unusual or irreversible payment method

- **Weight:** High

- **Indicator:** Enrollment or continued coverage requires payment by gift card, wire transfer, cryptocurrency, Zelle, Cash App, or another difficult-to-reverse method.

- **English explanation:** The message asks for a payment method commonly used by scammers because the payment can be difficult to recover.

- **Spanish explanation:** El mensaje solicita un método de pago utilizado frecuentemente por estafadores porque puede ser difícil recuperar el dinero.

### ENR-05 — Guaranteed or unrealistic coverage claim

- **Weight:** Medium

- **Indicator:** The message promises guaranteed approval, a "$0 plan," complete coverage, or unusually large savings without checking normal eligibility information.

- **English explanation:** The offer makes unusually broad promises about eligibility, price, or coverage before verifying whether you qualify.

- **Spanish explanation:** La oferta hace promesas poco realistas sobre elegibilidad, precio o cobertura antes de verificar si usted califica.

### ENR-06 — Refusal to provide plan details in writing

- **Weight:** Medium

- **Indicator:** A salesperson or message pressures the recipient to enroll or pay before providing written information about benefits, exclusions, deductibles, or the insurer.

- **English explanation:** The seller wants you to enroll before giving you clear written information about what the plan actually covers.

- **Spanish explanation:** El vendedor quiere que usted se inscriba antes de darle información escrita y clara sobre lo que realmente cubre el plan.

### ENR-07 — Insurance agent cannot be independently verified

- **Weight:** Medium

- **Indicator:** Someone claiming to be an insurance agent will not provide identifying or licensing information, such as a National Producer Number, or discourages independent verification.

- **English explanation:** The person selling the plan avoids giving information that would let you independently verify their identity or insurance license.

- **Spanish explanation:** La persona que vende el plan evita proporcionar información que le permitiría verificar de forma independiente su identidad o licencia de seguros.

### ENR-08 — Government-style paid advertisement or imitation branding

- **Weight:** Medium

- **Indicator:** A website, advertisement, or message uses official-looking government logos, wording, or branding while directing the user to a commercial or unrelated site.

- **English explanation:** The page looks like an official government service, but its website or organization does not match the real government program.

- **Spanish explanation:** La página parece un servicio oficial del gobierno, pero el sitio web o la organización no coincide con el programa gubernamental real.

## 2. Medical Debt Collection Scams

### DEBT-01 — Threat of arrest or criminal punishment

- **Weight:** High

- **Indicator:** A supposed collector threatens arrest, jail, police involvement, immigration consequences, or criminal prosecution for failure to pay a medical bill.

- **English explanation:** The message threatens serious punishment to pressure you into paying quickly. Threats like these are a strong warning sign.

- **Spanish explanation:** El mensaje amenaza con consecuencias graves para presionarle a pagar rápidamente. Este tipo de amenaza es una señal de advertencia importante.

### DEBT-02 — Refusal to provide debt-validation information

- **Weight:** High

- **Indicator:** The collector refuses or avoids providing written information identifying the creditor, amount owed, or other information needed to verify the debt.

- **English explanation:** The collector will not give you enough written information to confirm that the debt is actually yours.

- **Spanish explanation:** El cobrador no proporciona suficiente información por escrito para confirmar que la deuda realmente le pertenece.

### DEBT-03 — Same-day payment pressure

- **Weight:** Medium

- **Indicator:** The message demands payment immediately, today, or within hours and discourages the recipient from verifying the bill first.

- **English explanation:** The collector is pressuring you to pay before you have time to verify whether the medical debt is legitimate.

- **Spanish explanation:** El cobrador le presiona para pagar antes de que tenga tiempo de verificar si la deuda médica es legítima.

### DEBT-04 — Unrecognized medical debt

- **Weight:** Medium

- **Indicator:** The message demands payment for a hospital, clinic, provider, procedure, or service the recipient does not recognize.

- **English explanation:** The message refers to medical care or a bill you do not recognize. Verify the bill directly with the healthcare provider before paying.

- **Spanish explanation:** El mensaje se refiere a atención médica o a una factura que usted no reconoce. Verifique la factura directamente con el proveedor de atención médica antes de pagar.

### DEBT-05 — Callback information does not match the provider

- **Weight:** High

- **Indicator:** The message uses the name of a hospital, clinic, or provider but supplies a phone number, website, email address, or payment portal that does not match the organization's known contact information.

- **English explanation:** The message uses a real healthcare organization's name, but the contact or payment information does not match the organization.

- **Spanish explanation:** El mensaje utiliza el nombre de una organización de atención médica real, pero la información de contacto o de pago no coincide con la organización.

### DEBT-06 — Gift card, wire, cryptocurrency, or payment-app demand

- **Weight:** High

- **Indicator:** The collector requires payment through a gift card, wire transfer, cryptocurrency, Zelle, Venmo, Cash App, or another unusual payment channel.

- **English explanation:** The collector demands a payment method that is difficult to reverse and is commonly used in scams.

- **Spanish explanation:** El cobrador exige un método de pago difícil de revertir y utilizado frecuentemente en estafas.

### DEBT-07 — Collector will not identify the original creditor

- **Weight:** Medium

- **Indicator:** The sender claims a debt is owed but will not clearly identify the hospital, clinic, insurer, or other original creditor.

- **English explanation:** The collector is asking for money without clearly identifying who originally says you owe the debt.

- **Spanish explanation:** El cobrador solicita dinero sin identificar claramente quién afirma originalmente que usted debe la deuda.

### DEBT-08 — Discourages independent verification

- **Weight:** Medium

- **Indicator:** The message tells the recipient not to contact the hospital, insurer, provider, family members, or another trusted source before paying.

- **English explanation:** The sender is trying to stop you from independently checking whether the bill or debt is real.

- **Spanish explanation:** El remitente intenta impedir que usted verifique de forma independiente si la factura o la deuda es real.

## 3. Prescription and Pharmacy Scams

### RX-01 — Prescription medicine offered without a prescription

- **Weight:** High

- **Indicator:** An online pharmacy or seller offers prescription-only medication without requiring a valid prescription or consultation with an appropriate healthcare professional.

- **English explanation:** The seller offers prescription medicine without requiring a prescription. Legitimate pharmacies normally require a valid prescription for prescription-only medication.

- **Spanish explanation:** El vendedor ofrece medicamentos con receta sin exigir una receta. Las farmacias legítimas normalmente requieren una receta válida para estos medicamentos.

### RX-02 — Price appears unrealistically low

- **Weight:** Medium

- **Indicator:** A brand-name, high-demand, or expensive drug is advertised at a price dramatically below normal market prices.

- **English explanation:** The medicine is offered at a price that appears too good to be true. Extremely low prices can be a warning sign of an unsafe or fraudulent pharmacy.

- **Spanish explanation:** El medicamento se ofrece a un precio que parece demasiado bueno para ser verdad. Los precios extremadamente bajos pueden ser una señal de una farmacia insegura o fraudulenta.

### RX-03 — Pharmacy cannot be verified as licensed

- **Weight:** High

- **Indicator:** The seller provides no verifiable pharmacy license, state registration, U.S. physical address, or licensed pharmacist contact.

- **English explanation:** The pharmacy does not provide information that lets you verify that it is licensed and operating legitimately.

- **Spanish explanation:** La farmacia no proporciona información que permita verificar que tiene licencia y opera legalmente.

### RX-04 — Unsolicited medication advertisement

- **Weight:** Medium

- **Indicator:** The recipient receives an unexpected email, text, social-media message, or other solicitation advertising prescription medicine.

- **English explanation:** You received an unexpected offer for prescription medicine. Unsolicited drug advertisements are commonly used by unsafe online pharmacies.

- **Spanish explanation:** Usted recibió una oferta inesperada de medicamentos con receta. Las farmacias en línea inseguras utilizan con frecuencia anuncios de medicamentos no solicitados.

### RX-05 — Foreign or unclear drug source

- **Weight:** Medium

- **Indicator:** The seller says the medication will ship from another country or does not clearly explain where the medicine is produced, dispensed, or shipped from.

- **English explanation:** The source of the medicine is unclear or outside the normal licensed U.S. pharmacy system, making its safety difficult to verify.

- **Spanish explanation:** El origen del medicamento no está claro o está fuera del sistema normal de farmacias autorizadas de Estados Unidos, lo que dificulta verificar su seguridad.

### RX-06 — Unusual payment method

- **Weight:** High

- **Indicator:** The pharmacy requires cryptocurrency, wire transfer, gift cards, peer-to-peer payment, or another difficult-to-reverse method.

- **English explanation:** The seller requires an unusual payment method that may make it difficult to recover your money if the offer is fraudulent.

- **Spanish explanation:** El vendedor exige un método de pago inusual que puede dificultar la recuperación de su dinero si la oferta es fraudulenta.

### RX-07 — Misleading high-demand or GLP-1 drug claim

- **Weight:** Medium

- **Indicator:** The seller promotes a high-demand drug such as a GLP-1 product using claims of guaranteed availability, guaranteed results, or equivalence to an FDA-approved brand without clear supporting information.

- **English explanation:** The seller makes unusually strong claims about a high-demand medication that should be independently verified before purchase.

- **Spanish explanation:** El vendedor hace afirmaciones inusualmente fuertes sobre un medicamento de alta demanda que deben verificarse de forma independiente antes de comprarlo.

### RX-08 — Countdown timer or extreme scarcity pressure

- **Weight:** Medium

- **Indicator:** The pharmacy website or message uses countdown timers, "only a few left," limited-time offers, or similar pressure to make the recipient buy medication immediately.

- **English explanation:** The seller is using urgency or scarcity to push you into buying medicine before checking whether the pharmacy is legitimate.

- **Spanish explanation:** El vendedor utiliza urgencia o escasez para presionarle a comprar medicamentos antes de verificar si la farmacia es legítima.

## 4. Phishing — Credential and Payment Harvesting

### PHISH-01 — Lookalike or unrelated portal domain

- **Weight:** High

- **Indicator:** A link claims to open a patient portal, insurer, pharmacy, hospital, or government healthcare service but points to an unrelated or deceptively similar domain.

- **English explanation:** The link looks connected to a healthcare organization, but the actual website address does not match the organization's official domain.

- **Spanish explanation:** El enlace parece estar relacionado con una organización de atención médica, pero la dirección real del sitio web no coincide con el dominio oficial de la organización.

### PHISH-02 — URL shortener or raw IP address

- **Weight:** Medium

- **Indicator:** A healthcare login or payment message uses a shortened URL or an IP address instead of the organization's normal domain.

- **English explanation:** The message hides or replaces the normal website address, making it harder to see where the link really goes.

- **Spanish explanation:** El mensaje oculta o reemplaza la dirección normal del sitio web, lo que dificulta saber a dónde dirige realmente el enlace.

### PHISH-03 — Display-name and sender-domain mismatch

- **Weight:** High

- **Indicator:** The sender's display name claims to be a known healthcare organization, but the underlying email domain is unrelated.

- **English explanation:** The visible sender name looks legitimate, but the actual email address does not belong to the organization it claims to represent.

- **Spanish explanation:** El nombre visible del remitente parece legítimo, pero la dirección de correo electrónico real no pertenece a la organización que dice representar.

### PHISH-04 — Credential or one-time-code request

- **Weight:** High

- **Indicator:** An unsolicited message asks the recipient to enter or send a password, patient-portal credential, MFA code, PIN, or other authentication information.

- **English explanation:** The message asks for information that could let someone access your account. Passwords and verification codes should not be shared through unexpected messages.

- **Spanish explanation:** El mensaje solicita información que podría permitir que otra persona acceda a su cuenta. Las contraseñas y los códigos de verificación no deben compartirse mediante mensajes inesperados.

### PHISH-05 — Generic greeting combined with urgency

- **Weight:** Medium

- **Indicator:** A healthcare message uses a generic greeting and claims that immediate action is required to avoid account closure, lost coverage, delayed results, or another negative consequence.

- **English explanation:** The message combines a generic greeting with urgent pressure, which is a common phishing technique.

- **Spanish explanation:** El mensaje combina un saludo genérico con presión urgente, una técnica común de phishing.

### PHISH-06 — Unexpected attachment

- **Weight:** Medium

- **Indicator:** An unexpected healthcare message includes an attachment described as a bill, lab result, insurance document, claim, or other sensitive record.

- **English explanation:** The message includes a file you were not expecting. Unexpected attachments can contain malicious software or lead to credential theft.

- **Spanish explanation:** El mensaje incluye un archivo que usted no esperaba. Los archivos adjuntos inesperados pueden contener software malicioso o utilizarse para robar credenciales.

### PHISH-07 — Unexpected QR code

- **Weight:** Medium

- **Indicator:** An email, text, or document asks the recipient to scan a QR code to view results, verify an account, make a payment, or continue coverage.

- **English explanation:** The message uses a QR code to hide the destination website. Unexpected QR codes can send you to a fake login or payment page.

- **Spanish explanation:** El mensaje utiliza un código QR para ocultar el sitio web de destino. Los códigos QR inesperados pueden dirigirle a una página falsa de inicio de sesión o pago.

### PHISH-08 — Sensitive payment information entered through message link

- **Weight:** High

- **Indicator:** The message directs the recipient to a linked page and asks for card information, bank details, or other financial credentials.

- **English explanation:** The message directs you to provide financial information through a link that has not been independently verified.

- **Spanish explanation:** El mensaje le dirige a proporcionar información financiera mediante un enlace que no ha sido verificado de forma independiente.

## 5. Impersonation of Medicare, Medicaid, HHS-OIG, or a Healthcare Provider

### IMP-01 — "New" or "updated" Medicare card request

- **Weight:** High

- **Indicator:** Someone unexpectedly contacts the recipient claiming that a new or updated Medicare card is required and asks them to verify their Medicare number or other personal information.

- **English explanation:** The message says you need a new Medicare card and asks you to verify personal information. Unexpected requests like this are a common impersonation tactic.

- **Spanish explanation:** El mensaje dice que necesita una nueva tarjeta de Medicare y le pide verificar información personal. Las solicitudes inesperadas de este tipo son una táctica común de suplantación.

### IMP-02 — Unsolicited Medicare-number verification

- **Weight:** High

- **Indicator:** An unexpected caller, text, or email claiming to represent Medicare asks the recipient to confirm or provide their Medicare number.

- **English explanation:** Someone claiming to represent Medicare contacted you unexpectedly and asked for your Medicare number.

- **Spanish explanation:** Alguien que afirma representar a Medicare le contactó inesperadamente y le pidió su número de Medicare.

### IMP-03 — Free medical equipment or testing offer

- **Weight:** High

- **Indicator:** The message offers a "free" brace, genetic test, medical device, remote-monitoring equipment, or similar service and asks for Medicare information.

- **English explanation:** The message offers free medical equipment or testing while requesting your Medicare information. Fraudsters may use that information to bill for services or equipment you did not need.

- **Spanish explanation:** El mensaje ofrece equipos médicos o pruebas gratuitas mientras solicita su información de Medicare. Los estafadores pueden utilizar esa información para facturar servicios o equipos que usted no necesitaba.

### IMP-04 — Medicaid coverage-loss message with suspicious link

- **Weight:** High

- **Indicator:** A text or email claims the recipient will lose Medicaid coverage unless they immediately click a link, provide information, or make a payment.

- **English explanation:** The message threatens loss of Medicaid coverage and pressures you to use an unverified link or provide information immediately.

- **Spanish explanation:** El mensaje amenaza con la pérdida de cobertura de Medicaid y le presiona para utilizar un enlace no verificado o proporcionar información inmediatamente.

### IMP-05 — Payment required to keep government health coverage

- **Weight:** High

- **Indicator:** Someone claiming to represent Medicare, Medicaid, or another government health program demands payment to keep coverage active, issue a card, or unlock benefits.

- **English explanation:** The sender claims you must pay money to keep government health coverage or receive benefits. Unexpected payment demands should be independently verified.

- **Spanish explanation:** El remitente afirma que debe pagar dinero para mantener la cobertura médica del gobierno o recibir beneficios. Las solicitudes de pago inesperadas deben verificarse de forma independiente.

### IMP-06 — Government badge, employee ID, or caller-ID proof

- **Weight:** Medium

- **Indicator:** The sender attempts to prove legitimacy by showing a badge number, employee ID, photograph of credentials, or caller ID instead of allowing independent verification.

- **English explanation:** The person uses an official-looking identifier as proof that they are legitimate. Caller ID and identification images can be faked.

- **Spanish explanation:** La persona utiliza una identificación de apariencia oficial como prueba de legitimidad. El identificador de llamadas y las imágenes de identificación pueden falsificarse.

### IMP-07 — Provider impersonation with mismatched contact information

- **Weight:** High

- **Indicator:** A message claims to come from the recipient's doctor, clinic, hospital, pharmacy, or insurer but directs them to a phone number, email address, or website that does not match the organization's known information.

- **English explanation:** The message uses the name of a healthcare organization you may recognize, but its contact information does not match the real organization.

- **Spanish explanation:** El mensaje utiliza el nombre de una organización de atención médica que usted puede reconocer, pero la información de contacto no coincide con la organización real.

### IMP-08 — Unsolicited government or provider contact requesting sensitive information

- **Weight:** High

- **Indicator:** Someone claiming to represent a government health agency or healthcare provider unexpectedly asks for a Social Security number, Medicare or Medicaid number, date of birth, bank information, password, or other sensitive data.

- **English explanation:** The sender unexpectedly asks for sensitive information while claiming to represent a trusted healthcare or government organization.

- **Spanish explanation:** El remitente solicita inesperadamente información confidencial mientras afirma representar a una organización médica o gubernamental de confianza.

## Taxonomy Summary

CareShield currently defines **40 detection indicators** across five healthcare scam families:

- **Fake Insurance Enrollment / Marketplace Impersonation**

   - Indicator IDs: `ENR-01` through `ENR-08`

   - Total indicators: **8**

- **Medical Debt Collection Scams**

   - Indicator IDs: `DEBT-01` through `DEBT-08`

   - Total indicators: **8**

- **Prescription and Pharmacy Scams**

   - Indicator IDs: `RX-01` through `RX-08`

   - Total indicators: **8**

- **Phishing — Credential and Payment Harvesting**

   - Indicator IDs: `PHISH-01` through `PHISH-08`

   - Total indicators: **8**

- **Medicare / Medicaid / HHS-OIG / Provider Impersonation**

   - Indicator IDs: `IMP-01` through `IMP-08`

   - Total indicators: **8**

**Total Detection Indicators: 40**

## Design Notes

The rules engine should treat these indicators as evidence rather than final determinations.

Multiple indicators may fire on the same message. For example, a message could simultaneously trigger:

- IMP-02 for requesting a Medicare number,

- PHISH-01 for using a lookalike Medicare domain, and

- PHISH-05 for urgent account-pressure language.

The rules engine should preserve all fired rule IDs so CareShield can later rank the strongest evidence and show the user the most useful explanations.

The Low, Medium, and High values in this document are initial qualitative weights. Numeric weights will be assigned and tuned during development of the Week 2 rules engine using the healthcare seed corpus and false-positive testing.

## Source Basis

This initial taxonomy was developed from:

- the CareShield ChiEAC Fellow Project Brief,

- Federal Trade Commission consumer guidance on healthcare, insurance, Medicare, phishing, and debt-collection scams,

- U.S. Department of Health and Human Services Office of Inspector General consumer fraud alerts,

- Medicare fraud-prevention guidance, and

- U.S. Food and Drug Administration guidance on unsafe online pharmacies and counterfeit or improperly marketed prescription medicines.

Source links and verification dates will be maintained separately in `docs/sources.md` as the project progresses.
