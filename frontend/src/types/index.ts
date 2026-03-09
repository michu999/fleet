/**
 * TypeScript types mirroring backend Pydantic schemas
 */

// =============================================================================
// Enums
// =============================================================================

export enum UserRole {
  SUPER_ADMIN = "super_admin",
  ADMIN = "admin",
  MANAGER = "manager",
  DISPATCHER = "dispatcher",
  DRIVER = "driver",
}

export enum VehicleStatus {
  AVAILABLE = "available",
  ON_ROUTE = "on_route",
  MAINTENANCE = "maintenance",
  INACTIVE = "inactive",
  RESERVED = "reserved",
}

export enum VehicleType {
  TRUCK = "truck",
  VAN = "van",
  OTHER = "other",
}

export enum OrderStatus {
  PENDING = "pending",
  ASSIGNED = "assigned",
  IN_TRANSIT = "in_transit",
  DELIVERED = "delivered",
  CANCELLED = "cancelled",
  FAILED = "failed",
  RETURNED = "returned",
}

export enum TripStatus {
  PLANNED = "planned",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
}

export enum TenantPlan {
  TRIAL = "trial",
  BASIC = "basic",
  PROFESSIONAL = "professional",
  ENTERPRISE = "enterprise",
}
export enum WarehouseStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
}

// =============================================================================
// User & Auth
// =============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
  picture: string | null;
  role: UserRole;
  tenant_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  is_new_user: boolean;
}

// =============================================================================
// Tenant
// =============================================================================

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  plan: TenantPlan;
  is_active: boolean;
  max_users: number;
  created_at: string;
}

// =============================================================================
// Vehicle
// =============================================================================

export interface Vehicle {
  id: string;
  plate_number: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  vehicle_type: VehicleType;
  status: VehicleStatus;
  current_latitude: number | null;
  current_longitude: number | null;
  last_position_update: string | null;
  created_at: string;
}

export interface VehicleCreate {
  plate_number: string;
  brand?: string;
  model?: string;
  year?: number;
  vehicle_type?: VehicleType;
  status?: VehicleStatus;
}

export interface VehicleUpdate {
  plate_number?: string;
  brand?: string;
  model?: string;
  year?: number;
  vehicle_type?: VehicleType;
  status?: VehicleStatus;
  current_latitude?: number;
  current_longitude?: number;
}

// =============================================================================
// Warehouse
// =============================================================================

export interface Warehouse {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  warehouse_type: string;
  is_active: boolean;
  created_at: string;
}

// =============================================================================
// Order
// =============================================================================

export interface Order {
  id: string;
  order_number: string;
  client_name: string;
  client_contact: string | null;
  cargo_description: string | null;
  weight_kg: number | null;
  volume_m3: number | null;
  status: OrderStatus;
  origin_warehouse_id: string;
  destination_warehouse_id: string;
  deadline_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface OrderCreate {
  order_number: string;
  client_name: string;
  client_contact?: string;
  cargo_description?: string;
  weight_kg?: number;
  volume_m3?: number;
  origin_warehouse_id: string;
  destination_warehouse_id: string;
  deadline_at?: string;
  notes?: string;
}

export interface OrderUpdate {
  client_name?: string;
  client_contact?: string;
  cargo_description?: string;
  weight_kg?: number;
  volume_m3?: number;
  status?: OrderStatus;
  deadline_at?: string;
  notes?: string;
}

// =============================================================================
// Trip
// =============================================================================

export interface Trip {
  id: string;
  order_id: string;
  driver_id: string;
  vehicle_id: string;
  trailer_id: string | null;
  planned_departure: string;
  planned_arrival: string;
  actual_departure: string | null;
  actual_arrival: string | null;
  status: TripStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// Pagination
// =============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
}

// =============================================================================
// API Error
// =============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
}
