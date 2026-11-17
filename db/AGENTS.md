# Folder rules: db/ — owner Ethan

- Plain PostgreSQL migrations only (no Neon-only features) so CI can run them on a temporary Postgres container.
- Every schema change PR lists the migration, rollback plan and backup impact.
- Not your agent's folder? Stop and ask Ethan. Changes here need Ethan's review (CODEOWNERS).
