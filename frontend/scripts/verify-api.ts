import { verifyApiConnection } from "../src/lib/verifyApiConnection";

const baseUrl = process.env.VITE_API_BASE_URL ?? "http://localhost:8000";

console.log(`Checking TraVerse backend at ${baseUrl} ...`);

verifyApiConnection(baseUrl)
  .then((result) => {
    console.log("Health check: OK");
    console.log(`  status: ${result.status}`);
    console.log(`  database: ${result.services.database}`);
    console.log(`  redis: ${result.services.redis}`);
    console.log(`  django: ${result.services.django}`);
    console.log("API contract verification passed.");
  })
  .catch((error: unknown) => {
    console.error("API contract verification FAILED.");
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
