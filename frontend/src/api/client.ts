/**
 * Axios client configuration with interceptors
 */

import axios, { AxiosError, type AxiosInstance } from "axios";
import type { ApiError } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

/**
 * Create axios instance with default configuration
 */
const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // CRITICAL: required for httpOnly cookies
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Response interceptor for error handling
 */
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Handle 401 - redirect to login
    if (error.response?.status === 401) {
      // Don't redirect if already on login page
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }

    // Extract error message
    const message =
      error.response?.data?.detail ||
      error.message ||
      "Wystąpił nieoczekiwany błąd";

    // Return rejected promise with formatted error
    return Promise.reject({
      message,
      status: error.response?.status,
      data: error.response?.data,
    });
  }
);

export default client;
