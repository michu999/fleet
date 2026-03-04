/**
 * Vehicles API functions
 */

import client from "./client";
import type {
  Vehicle,
  VehicleCreate,
  VehicleUpdate,
  PaginatedResponse,
  PaginationParams,
} from "@/types";

export const vehiclesApi = {
  /**
   * List all vehicles with pagination
   */
  list: (params?: PaginationParams) =>
    client.get<PaginatedResponse<Vehicle>>("/fleet/vehicles", { params }),

  /**
   * Get single vehicle by ID
   */
  getById: (id: string) => client.get<Vehicle>(`/fleet/vehicles/${id}`),

  /**
   * Create new vehicle
   */
  create: (data: VehicleCreate) =>
    client.post<Vehicle>("/fleet/vehicles", data),

  /**
   * Update existing vehicle
   */
  update: (id: string, data: VehicleUpdate) =>
    client.patch<Vehicle>(`/fleet/vehicles/${id}`, data),

  /**
   * Delete vehicle
   */
  delete: (id: string) => client.delete(`/fleet/vehicles/${id}`),
};
