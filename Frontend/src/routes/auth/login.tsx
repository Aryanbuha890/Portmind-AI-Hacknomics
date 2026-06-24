import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/auth/login")({
  head: () => ({
    meta: [
      { title: "Sign In — LogiMind AI" },
      { name: "description", content: "Access your LogiMind AI Command Center." },
    ],
  }),
});
