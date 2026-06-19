export interface Ticket {
  id: number;
  ticket_id: number;
  customer_name: string | null;
  customer_email: string | null;
  customer_age: number | null;
  customer_gender: string | null;
  product_purchased: string | null;
  date_of_purchase: string | null;
  ticket_type: string | null;
  ticket_subject: string | null;
  ticket_description: string | null;
  ticket_status: string | null;
  ticket_priority: string | null;
  ticket_channel: string | null;
  first_response_time: string | null;
  time_to_resolution: string | null;
  satisfaction_rating: number | null;
  has_template_placeholders: boolean;
  ai_category: string | null;
  ai_priority: string | null;
  ai_summary: string | null;
  ai_sentiment: string | null;
  ai_responsible_team: string | null;
  ai_processed: boolean;
  ai_processed_at: string | null;
  ai_error: string | null;
}

export interface TicketListResponse {
  total: number;
  page: number;
  page_size: number;
  data: Ticket[];
}

export interface SummaryResponse {
  total_tickets: number;
  tickets_analizados: number;
  tickets_criticos_abiertos: number;
  rating_promedio: number | null;
  por_prioridad: Record<string, number>;
  por_categoria_ia: Record<string, number>;
  por_sentimiento_ia: Record<string, number>;
  top_productos: { producto: string; count: number }[];
}

export interface StatusResponse {
  total: number;
  procesados_ok: number;
  con_error: number;
  pendientes: number;
  en_curso: boolean;
  progreso_pct: number;
}

export interface AskResponse {
  question: string;
  answer: string;
}

export interface TicketFilters {
  status?: string;
  priority?: string;
  ai_category?: string;
  ai_sentiment?: string;
  product?: string;
  search?: string;
  page: number;
  page_size: number;
}
