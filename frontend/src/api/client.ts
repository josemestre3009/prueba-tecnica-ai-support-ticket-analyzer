import axios from "axios";
import type { AskResponse, StatusResponse, SummaryResponse, TicketFilters, TicketListResponse } from "../types/ticket";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 30000,
});

export const getTickets = (filters: Partial<TicketFilters>) =>
  api.get<TicketListResponse>("/tickets", { params: filters }).then((r) => r.data);

export const getSummary = () =>
  api.get<SummaryResponse>("/summary").then((r) => r.data);

export const getStatus = () =>
  api.get<StatusResponse>("/status").then((r) => r.data);

export const askQuestion = (question: string) =>
  api.post<AskResponse>("/ask", { question }).then((r) => r.data);

export const triggerIngest = () =>
  api.post("/ingest").then((r) => r.data);

export const triggerProcess = () =>
  api.post("/process").then((r) => r.data);
