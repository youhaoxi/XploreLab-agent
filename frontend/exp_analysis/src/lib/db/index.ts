import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";
import * as dotenv from "dotenv";

dotenv.config({ path: "../../.env" });

if (!process.env.UTU_DB_URL) {
  throw new Error("UTU_DB_URL is not set");
}

const client = postgres(process.env.UTU_DB_URL);
export const db = drizzle(client, { schema });
