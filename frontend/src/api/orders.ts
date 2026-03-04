/**
 * Orders API functions
 */

import client from "./client";
import type {
  Order,
  OrderCreate,
  OrderUpdate,
  PaginatedResponse,
  PaginationParams,
  OrderStatus,
} from "@/types";

interface OrderListParams extends PaginationParams {
  status?: OrderStatus;
}

export const ordersApi = {
  /**
   * List all orders with pagination and filtering
   */
  list: (params?: OrderListParams) =>
    client.get<PaginatedResponse<Order>>("/orders", { params }),

  /**
   * Get single order by ID
   */
  getById: (id: string) => client.get<Order>(`/orders/${id}`),

  /**
   * Create new order
   */
  create: (data: OrderCreate) => client.post<Order>("/orders", data),

  /**
   * Update existing order
   */
  update: (id: string, data: OrderUpdate) =>
    client.patch<Order>(`/orders/${id}`, data),

  /**
   * Cancel order
   */
  cancel: (id: string) =>
    client.patch<Order>(`/orders/${id}`, { status: "cancelled" }),

  /**
   * Delete order
   */
  delete: (id: string) => client.delete(`/orders/${id}`),
};
