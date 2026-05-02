import { apiFetch } from "./client";
import type { CommandRequest, CommandResponse } from "@/lib/types";

export const commandsApi = {
  run: (body: CommandRequest) =>
    apiFetch<CommandResponse>("/api/v1/command", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
