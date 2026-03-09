/**
 * Order detail page
 */

import {useParams, useNavigate} from "react-router-dom";
import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import {toast} from "sonner";
import {ordersApi} from "@/api";
import {ConfirmDialog} from "@/components/ui/confirm-dialog";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {ArrowLeft, Loader2, Package} from "lucide-react";
import {OrderStatus} from "@/types";
import {useState} from "react";

// ─── Config ───────────────────────────────────────────────────────────────────

const orderStatusConfig: Record<OrderStatus, {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
}> = {
    [OrderStatus.PENDING]: {label: "Oczekujące", variant: "warning"},
    [OrderStatus.ASSIGNED]: {label: "Przypisane", variant: "secondary"},
    [OrderStatus.IN_TRANSIT]: {label: "W trasie", variant: "default"},
    [OrderStatus.DELIVERED]: {label: "Dostarczone", variant: "success"},
    [OrderStatus.CANCELLED]: {label: "Anulowane", variant: "destructive"},
    [OrderStatus.FAILED]: {label: "Niepowodzenie", variant: "destructive"},
    [OrderStatus.RETURNED]: {label: "Zwrócone", variant: "outline"},
};

// ─── Helper ───────────────────────────────────────────────────────────────────

function DetailRow({label, value}: { label: string; value: React.ReactNode }) {
    return (
        <div className="flex flex-col gap-1 py-3 border-b last:border-0">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
            <span className="text-sm">{value ?? "-"}</span>
        </div>
    );
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function OrderDetailPage() {
    const {id} = useParams<{ id: string }>();
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [cancelDialog, setCancelDialog] = useState(false);

    const {data, isLoading, error} = useQuery({
        queryKey: ["orders", id],
        queryFn: () => ordersApi.getById(id!),
        enabled: !!id,
    });

    const cancelMutation = useMutation({
        mutationFn: () => ordersApi.cancel(id!),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["orders"]});
            toast.success("Zamówienie zostało anulowane");
            setCancelDialog(false);
        },
        onError: (error: { message: string }) => {
            toast.error(error.message || "Błąd podczas anulowania zamówienia");
        },
    });

    const order = data?.data;

    const canCancel = order &&
        (order.status === OrderStatus.PENDING || order.status === OrderStatus.ASSIGNED);

    if (isLoading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin"/>
            </div>
        );
    }

    if (error || !order) {
        return (
            <div className="flex h-64 flex-col items-center justify-center text-center">
                <Package className="mb-4 h-12 w-12 text-muted-foreground"/>
                <h3 className="text-lg font-semibold">Nie znaleziono zamówienia</h3>
                <Button className="mt-4" variant="outline" onClick={() => navigate("/orders")}>
                    <ArrowLeft className="mr-2 h-4 w-4"/>
                    Wróć do zamówień
                </Button>
            </div>
        );
    }

    const statusConfig = orderStatusConfig[order.status];

    return (
        <div className="space-y-6 max-w-2xl">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => navigate("/orders")}>
                    <ArrowLeft className="h-5 w-5"/>
                </Button>
                <div className="flex-1">
                    <h1 className="text-3xl font-bold">{order.order_number}</h1>
                    <p className="text-muted-foreground text-sm">
                        Utworzone {new Date(order.created_at).toLocaleDateString("pl-PL", {
                        day: "numeric", month: "long", year: "numeric",
                    })}
                    </p>
                </div>
                <Badge variant={statusConfig?.variant || "default"} className="text-sm px-3 py-1">
                    {statusConfig?.label || order.status}
                </Badge>
            </div>

            {/* Details */}
            <div className="rounded-md border px-4">
                <DetailRow label="Klient" value={order.client_name}/>
                <DetailRow
                    label="Kontakt"
                    value={order.client_contact}
                />
                <DetailRow
                    label="Magazyn nadania"
                    value={order.origin_warehouse_id}
                />
                <DetailRow
                    label="Magazyn docelowy"
                    value={order.destination_warehouse_id}
                />
                <DetailRow
                    label="Opis ładunku"
                    value={order.cargo_description}
                />
                <DetailRow
                    label="Waga"
                    value={order.weight_kg ? `${order.weight_kg} kg` : undefined}
                />
                <DetailRow
                    label="Objętość"
                    value={order.volume_m3 ? `${order.volume_m3} m³` : undefined}
                />
                <DetailRow
                    label="Termin dostawy"
                    value={order.deadline_at
                        ? new Date(order.deadline_at).toLocaleDateString("pl-PL", {
                            day: "numeric", month: "long", year: "numeric",
                            hour: "2-digit", minute: "2-digit",
                        })
                        : undefined}
                />
                <DetailRow label="Uwagi" value={order.notes}/>
            </div>

            {/* Actions */}
            {canCancel && (
                <div className="flex gap-2">
                    <Button
                        variant="destructive"
                        onClick={() => setCancelDialog(true)}
                    >
                        Anuluj zamówienie
                    </Button>
                </div>
            )}

            <ConfirmDialog
                open={cancelDialog}
                onOpenChange={setCancelDialog}
                title="Anulować zamówienie?"
                description={<>Czy na pewno chcesz anulować zamówienie <strong>{order.order_number}</strong>? Tej
                    operacji nie można cofnąć.</>}
                confirmLabel="Tak, anuluj"
                cancelLabel="Nie, zachowaj"
                isPending={cancelMutation.isPending}
                onConfirm={() => cancelMutation.mutate()}
            />
        </div>
    );
}