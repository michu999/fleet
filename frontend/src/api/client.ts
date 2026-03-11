/**
 * Axios client configuration with interceptors
 */

import axios, {AxiosError, type AxiosInstance} from "axios";
import type {ApiError} from "@/types";

/**
 * Create axios instance with default configuration
 * Using relative path - Vite proxy handles routing to backend
 */
const client: AxiosInstance = axios.create({
    baseURL: "/api/v1",  // relative - goes through Vite proxy
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
            const detail = error.response.data.detail;
            if (detail === "User account is has been deactivated") {
                alert("Twoje konto zostało dezaktywowane. Skontaktuj się z administratorem.");
                return Promise.reject({
                    message: "Konto dezaktywowane",
                    status: 403,
                    data: error.response.data,
                });
            }
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
