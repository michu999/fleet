/**
 * API exports
 */

export { default as client } from "./client";
export { authApi } from "./auth";
export { vehiclesApi } from "./vehicles";
export { ordersApi } from "./orders";
export {warehouseApi} from "./warehouses";

export interface WarehouseCreate {
  name: string
  address?: string
  latitude?: number
  longitude?: number
  is_active?: boolean
}

export interface WarehouseUpdate {
  name?: string
  address?: string
  latitude?: number
  longitude?: number
  is_active?: boolean
}