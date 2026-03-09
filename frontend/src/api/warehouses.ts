/**
 * Warehouse API functions
 */

import client from "./client";

import type {
    Warehouse,
    WarehouseCreate,
    WarehouseUpdate,
    PaginatedResponse,
    PaginationParams,
} from "@/types";

export const warehouseApi = {
  /**
   * List all warehouses with pagination
   */
  list: (params?: PaginationParams) =>
    client.get<PaginatedResponse<Warehouse>>("/orders/warehouses", { params }),

  /**
   * Get single warehouse by ID
   */
  getById: (id: string) => client.get<Warehouse>(`/orders/warehouses/${id}`),

  /**
   * Create new vehicle
   */
  create: (data: WarehouseCreate) =>
    client.post<Warehouse>("/orders/warehouses", data),

  /**
   * Update existing warehouse
   */
  update: (id: string, data: WarehouseUpdate) =>
    client.patch<Warehouse>(`/warehouses/${id}`, data),

  /**
   * Delete warehouse
   */
  delete: (id: string) => client.delete(`/warehouses/${id}`),
};