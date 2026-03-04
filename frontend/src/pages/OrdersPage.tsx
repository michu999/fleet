/**
 * Orders management page
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ordersApi } from "@/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Plus, MoreHorizontal, Loader2, Package, Filter } from "lucide-react";
import { OrderStatus } from "@/types";
import type { Order } from "@/types";

// Status badge configuration
const orderStatusConfig: Record<OrderStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
  [OrderStatus.PENDING]: { label: "Oczekujące", variant: "warning" },
  [OrderStatus.ASSIGNED]: { label: "Przypisane", variant: "secondary" },
  [OrderStatus.IN_TRANSIT]: { label: "W trasie", variant: "default" },
  [OrderStatus.DELIVERED]: { label: "Dostarczone", variant: "success" },
  [OrderStatus.CANCELLED]: { label: "Anulowane", variant: "destructive" },
  [OrderStatus.FAILED]: { label: "Niepowodzenie", variant: "destructive" },
  [OrderStatus.RETURNED]: { label: "Zwrócone", variant: "outline" },
};

const statusFilterOptions = [
  { value: "", label: "Wszystkie" },
  { value: OrderStatus.PENDING, label: "Oczekujące" },
  { value: OrderStatus.ASSIGNED, label: "Przypisane" },
  { value: OrderStatus.IN_TRANSIT, label: "W trasie" },
  { value: OrderStatus.DELIVERED, label: "Dostarczone" },
  { value: OrderStatus.CANCELLED, label: "Anulowane" },
];

export default function OrdersPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [orderToCancel, setOrderToCancel] = useState<Order | null>(null);
  const queryClient = useQueryClient();

  // Fetch orders
  const { data, isLoading, error } = useQuery({
    queryKey: ["orders", statusFilter],
    queryFn: () =>
      ordersApi.list({
        per_page: 100,
        status: statusFilter ? (statusFilter as OrderStatus) : undefined,
      }),
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: (id: string) => ordersApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      toast.success("Zamówienie zostało anulowane");
      setCancelDialogOpen(false);
      setOrderToCancel(null);
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas anulowania zamówienia");
    },
  });

  const orders = data?.data?.items || [];

  const handleCancelClick = (order: Order) => {
    setOrderToCancel(order);
    setCancelDialogOpen(true);
  };

  const handleConfirmCancel = () => {
    if (orderToCancel) {
      cancelMutation.mutate(orderToCancel.id);
    }
  };

  const canCancel = (status: OrderStatus) => {
    return status === OrderStatus.PENDING || status === OrderStatus.ASSIGNED;
  };

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center text-destructive">
          Błąd podczas ładowania zamówień
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-3xl font-bold">Zamówienia</h1>
        <Button disabled>
          <Plus className="mr-2 h-4 w-4" />
          Nowe zamówienie
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {statusFilterOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : orders.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <Package className="mb-4 h-12 w-12 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Brak zamówień</h3>
          <p className="text-muted-foreground">
            {statusFilter
              ? "Nie znaleziono zamówień o wybranym statusie"
              : "Utwórz pierwsze zamówienie"}
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nr zamówienia</TableHead>
                <TableHead>Klient</TableHead>
                <TableHead>Ładunek</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Termin</TableHead>
                <TableHead>Data utworzenia</TableHead>
                <TableHead className="w-[70px]">Akcje</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.map((order: Order) => {
                const statusConfig = orderStatusConfig[order.status];
                return (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium">
                      {order.order_number}
                    </TableCell>
                    <TableCell>{order.client_name}</TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {order.cargo_description || "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusConfig?.variant || "default"}>
                        {statusConfig?.label || order.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {order.deadline_at
                        ? new Date(order.deadline_at).toLocaleDateString("pl-PL")
                        : "-"}
                    </TableCell>
                    <TableCell>
                      {new Date(order.created_at).toLocaleDateString("pl-PL")}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem disabled>
                            Szczegóły
                          </DropdownMenuItem>
                          {canCancel(order.status) && (
                            <DropdownMenuItem
                              onClick={() => handleCancelClick(order)}
                              className="text-destructive"
                            >
                              Anuluj
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Cancel Confirmation Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Anulować zamówienie?</DialogTitle>
            <DialogDescription>
              Czy na pewno chcesz anulować zamówienie{" "}
              <strong>{orderToCancel?.order_number}</strong>? Tej operacji nie można cofnąć.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCancelDialogOpen(false)}
            >
              Nie, zachowaj
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmCancel}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Tak, anuluj
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
