import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "LogiMind AI — Autonomous Intelligence for Modern Ports & Rails" },
      {
        name: "description",
        content:
          "Unified AI command center combining computer vision, railway wagon telemetry, predictive maintenance, multi-agent AI, vessel intelligence and operational analytics.",
      },
      {
        property: "og:title",
        content: "LogiMind AI — Autonomous Intelligence for Modern Ports & Rails",
      },
      {
        property: "og:description",
        content: "The operating system for smart ports and rail terminals.",
      },
    ],
    links: [{ rel: "preconnect", href: "https://images.unsplash.com" }],
  }),
});
