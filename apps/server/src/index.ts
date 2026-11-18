import { existsSync } from "node:fs";
import path from "node:path";
import express from "express";

const app = express();
const webDistPath = path.resolve(__dirname, "../../web/dist");

app.get("/health", (_request, response) => {
  response.status(200).json({
    status: "ok",
    service: "api",
    checkedAt: new Date().toISOString(),
    databaseChecked: false,
  });
});

app.get("/favicon.ico", (_request, response) => {
  response.status(204).end();
});

if (!existsSync(webDistPath)) {
  throw new Error(`Built web app not found at ${webDistPath}; run npm run build first.`);
}

app.use(express.static(webDistPath));

const port = process.env.PORT ? Number(process.env.PORT) : 5000;
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error(`PORT must be an integer from 1 to 65535; received "${process.env.PORT}".`);
}

app.listen(port, "0.0.0.0", () => {
  console.log(`Spendly is listening on port ${port}.`);
});
