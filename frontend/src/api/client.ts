import { client } from "./generated/client.gen";

// OpenAPI paths already include /api/v1 (FastAPI router prefix).
client.setConfig({
  baseUrl: "",
});

export { client };
