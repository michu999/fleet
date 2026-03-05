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
   * List all vehicles with pagination
   */
  list: (params?: PaginationParams) =>
    client.get<PaginatedResponse<Warehouse>>("/warehouses", { params }),

  /**
   * Get single vehicle by ID
   */
  getById: (id: string) => client.get<Warehouse>(`/warehouses/${id}`),

  /**
   * Create new vehicle
   */
  create: (data: WarehouseCreate) =>
    client.post<Warehouse>("/warehouses", data),

  /**
   * Update existing vehicle
   */
  update: (id: string, data: WarehouseUpdate) =>
    client.patch<Warehouse>(`/warehouses/${id}`, data),

  /**
   * Delete vehicle
   */
  delete: (id: string) => client.delete(`/warehouses/${id}`),
};