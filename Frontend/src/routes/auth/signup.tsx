import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/auth/signup")({
  head: () => ({
    meta: [
      { title: "Sign Up — LogiMind AI" },
      { name: "description", content: "Create your LogiMind AI Command Center account." },
    ],
  }),
});
