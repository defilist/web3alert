import { AlertMeta } from './datatypes';

interface PaginatedRequest {
  page_index: number;
  page_size: number;
}

interface SortableRequest<T> {
  sort_field: keyof T;
  sort_direction: 'asc' | 'desc';
}

export interface GetAlertMetasRequest extends PaginatedRequest, SortableRequest<AlertMeta> {}

export interface GetAlertMetasResponse {
  total_item_count: number;
  items: AlertMeta[];
}
