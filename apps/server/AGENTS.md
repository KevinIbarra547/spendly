# Folder rules: apps/server/ — owner Ethan

- Routes and shapes follow SPEC.md A.12 and A.22 exactly; validate with the Zod schemas in `packages/contracts/`.
- Secrets only from environment config (Replit Secrets); never log keys, passwords or request bodies.
- No Replit-only services. AI model IDs from env. AI never writes money or simulation state.
- Not your agent's folder? Stop and ask Ethan. Changes here need Ethan's review (CODEOWNERS).
