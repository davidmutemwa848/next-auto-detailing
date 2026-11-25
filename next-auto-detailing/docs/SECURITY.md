# Security notes

Foundation includes Werkzeug scrypt password hashing, HttpOnly session cookies, configurable Secure flag, SameSite=Lax, bounded sessions, rate limits, SQLAlchemy parameterized ORM operations, role checks on protected staff endpoints, customer ownership filtering, request size limits, and basic security headers.

Production blockers: CSRF token handoff for cookie-authenticated mutations; complete one-time expiring password-reset and email-verification tokens; mail delivery; detailer assignment authorization; audit trail; upload validation/private storage; PDF document access controls; payroll review; backups; dependency/security audit and deployment penetration testing. Do not call this a completed security audit. Avoid raw SQL string interpolation. Configure exact CORS origins and HTTPS only.
