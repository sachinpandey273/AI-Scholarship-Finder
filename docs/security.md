# Security and privacy controls

The API verifies signed RS256 OIDC tokens and scopes every profile, workflow and
event lookup to the authenticated subject. Production startup refuses to run
without issuer, audience and public-key configuration.

The API's development upload endpoint stores PDF/DOCX files outside public
directories under generated IDs, signature-checks its allowlist, imposes a size
limit, and records a SHA-256 digest. Production must replace local volume storage
with private object storage, malware scanning, signed downloads, and a scheduled
retention deletion job; the legacy Streamlit upload path remains development-only.

Web retrieval is treated as untrusted input. The existing source verifier sanitizes
retrieved content; production retrieval still needs a redirect-aware private-IP
and localhost block before public deployment. Never place academic documents,
bearer tokens, raw prompts, or credentials in application logs.
