/**
 * Banner shown when Super Admin is impersonating a tenant user.
 */

import {useMutation, useQueryClient} from "@tanstack/react-query";
import {toast} from "sonner";
import {adminApi} from "@/api/admin.ts";
import {useAuth} from "@/hooks/useAuth.ts";
import {Button} from "@/components/ui/button.tsx";
import {ShieldAlert, LogOut} from "lucide-react";

export function ImpersonationBanner() {
    const {user} = useAuth();
    const queryClient = useQueryClient();
    const stopMutation = useMutation({
        mutationFn: () => adminApi.stopImpersonation(),
        onSuccess: async (res) => {
            const restoredUser = res.data?.user ?? res.data;
            queryClient.setQueryData(["auth", "me"], restoredUser); // ← zamiast setUser
            await queryClient.invalidateQueries();
            toast.success("Powrócono do konta Super Admin");
        },
        onError: () => {
            toast.error("Błąd podczas przywracania sesji — zaloguj się ponownie");
        },
    });

    if (!user?.impersonated_by) return null;

    return (
        <div className="flex items-center justify-between bg-yellow-500 px-4 py-2 text-sm font-medium text-yellow-950">
            <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 shrink-0"/>
                <span>
          Tryb podglądu: jesteś zalogowany jako{" "}
                    <strong>{user.name}</strong> ({user.email})
        </span>
            </div>
            <Button
                size="sm"
                variant="outline"
                className="border-yellow-800 bg-transparent text-yellow-950 hover:bg-yellow-600"
                onClick={() => stopMutation.mutate()}
                disabled={stopMutation.isPending}
            >
                <LogOut className="mr-2 h-3 w-3"/>
                Wróć do Super Admin
            </Button>
        </div>
    );
}