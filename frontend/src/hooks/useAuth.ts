/**
 * Authentication hook using React Query
 */

import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import {authApi} from "@/api";
import type {User} from "@/types";

export function useAuth() {
    const queryClient = useQueryClient();

    // Fetch current user - runs on app load
    const {
        data: user,
        isLoading,
        error,
    } = useQuery<User>({
        queryKey: ["auth", "me"],
        queryFn: async () => {
            const response = await authApi.getMe();
            return response.data;
        },
        retry: false, // don't retry on 401
        staleTime: 5 * 60 * 1000, // consider fresh for 5 minutes
    });

    // Logout mutation
    const logoutMutation = useMutation({
        mutationFn: () => authApi.logout(),
        onSuccess: () => {
            // Clear all cached data
            queryClient.clear();
            // Redirect to login
            window.location.href = "/login";
        },
    });

    return {
        user,
        isLoading,
        error,
        isAuthenticated: !!user,
        logout: logoutMutation.mutate,
        isLoggingOut: logoutMutation.isPending,
    };
}
