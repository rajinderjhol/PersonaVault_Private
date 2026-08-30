/**
 * Redactor Utility for PersonaVault
 * Automatically redacts PII (Personally Identifiable Information) 
 * and PHI (Protected Health Information) from strings.
 */

const PII_PATTERNS = {
  email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
  phone: /(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g,
  ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
  creditCard: /\b(?:\d[ -]*?){13,16}\b/g,
  ipv4: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
};

const PHI_PATTERNS = {
  mrn: /\bMRN\d{6,10}\b/gi, // Medical Record Number
  dob: /\b\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}\b/g, // Date of Birth
};

export const redact = (text: string, options: { pii?: boolean, phi?: boolean } = { pii: true, phi: true }): string => {
  let redacted = text;

  if (options.pii) {
    Object.entries(PII_PATTERNS).forEach(([type, pattern]) => {
      redacted = redacted.replace(pattern, `[REDACTED ${type.toUpperCase()}]`);
    });
  }

  if (options.phi) {
    Object.entries(PHI_PATTERNS).forEach(([type, pattern]) => {
      redacted = redacted.replace(pattern, `[REDACTED ${type.toUpperCase()}]`);
    });
  }

  return redacted;
};
