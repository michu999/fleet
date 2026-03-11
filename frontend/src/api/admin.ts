/**
 * Admin API client — Ops Panel endpoints (SUPER_ADMIN only)
 */

import client from "./client";
import type { Tenant, User, TenantPlan, UserRole } from "@/types";

// ─── Request types ─────────────────────────────────────────────────────────

export interface TenantCreatePayload {
  name: string;
  slug: string;
  domain?: string;
  plan?: TenantPlan;
  max_users?: number;
}

export interface TenantUpdatePayload {
  name?: string;
  domain?: string;
  plan?: TenantPlan;
  max_users?: number;
  is_active?: boolean;
}

export interface UserCreatePayload {
  email: string;
  name: string;
  role: UserRole;
}

export interface UserUpdatePayload {
  role?: UserRole;
  is_active?: boolean;
  name?: string;
}

export interface TenantStats {
  tenant_id: string;
  users_count: number;
  vehicles_count: number;
  orders_count: number;
  active_trips_count: number;
}

// ─── API ───────────────────────────────────────────────────────────────────

export const adminApi = {
  // Tenants
  listTenants: (params?: { skip?: number; limit?: number; active_only?: boolean }) =>
    client.get<Tenant[]>("/admin/tenants", { params }),

  createTenant: (data: TenantCreatePayload) =>
    client.post<Tenant>("/admin/tenants", data),

  getTenant: (id: string) =>
    client.get<Tenant>(`/admin/tenants/${id}`),

  updateTenant: (id: string, data: TenantUpdatePayload) =>
    client.patch<Tenant>(`/admin/tenants/${id}`, data),

  getTenantStats: (id: string) =>
    client.get<TenantStats>(`/admin/tenants/${id}/stats`),

  // Users per tenant
  listUsers: (tenantId: string) =>
    client.get<User[]>(`/admin/tenants/${tenantId}/users`),

  createUser: (tenantId: string, data: UserCreatePayload) =>
    client.post<User>(`/admin/tenants/${tenantId}/users`, data),

  updateUser: (userId: string, data: UserUpdatePayload) =>
    client.patch<User>(`/admin/users/${userId}`, data),
};