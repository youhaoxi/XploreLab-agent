import { drizzle } from "drizzle-orm/postgres-js";
import { migrate } from "drizzle-orm/postgres-js/migrator";
import postgres from "postgres";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../.env" });

if (!process.env.UTU_DB_URL) {
  throw new Error("UTU_DB_URL is not set");
}

const main = async () => {
  const connection = postgres(process.env.UTU_DB_URL!, { max: 1 });
  const db = drizzle(connection);
  await migrate(db, { migrationsFolder: "drizzle" });
  console.log("Migrations applied successfully");
  process.exit(0);
};

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
