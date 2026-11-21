# Running Spendly on Replit

## Start the app

Use the Replit **Run** button. It builds the web app and API, then starts the server on port 5000. The server binds to `0.0.0.0` and serves the built landing page and `GET /health`.

To run the same steps from a shell:

```sh
npm ci
npm run build
npm start
```

For a local check on a different port:

```sh
npm run build
PORT=3000 npm start
```

## Runtime

The repository pins Node.js `26.13.0` in `.nvmrc`. Replit's available Node.js modules were checked during setup; the newest supported module was Node.js `24.22.3`, so `.replit` selects `nodejs-24` without changing the repository pin.

The current landing page is static. Account creation, login, database access, and gameplay services are not implemented by this setup.
