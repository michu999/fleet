/**
 * Orders management page
 */

import {useState} from "react";
import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import {useNavigate} from "react-router-dom";
import {toast} from "sonner";
import {ordersApi, warehouseApi} from "@/api";
import {useTableFilters} from "@/hooks/useTableFilters";
import {TableToolbar} from "@/components/ui/table-toolbar";
import {ConfirmDialog} from "@/components/ui/confirm-dialog";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Input} from "@/components/ui/input";
import {Label} from "@/components/ui/label";
import {Textarea} from "@/components/ui/textarea";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
    Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {Plus, MoreHorizontal, Loader2, Package, Filter} from "lucide-react";
import {OrderStatus} from "@/types";
import type {Order, Warehouse} from "@/types";

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

const statusFilterOptions = [
    {value: "", label: "Wszystkie"},
    {value: OrderStatus.PENDING, label: "Oczekujące"},
    {value: OrderStatus.ASSIGNED, label: "Przypisane"},
    {value: OrderStatus.IN_TRANSIT, label: "W trasie"},
    {value: OrderStatus.DELIVERED, label: "Dostarczone"},
    {value: OrderStatus.CANCELLED, label: "Anulowane"},
];

const emptyForm = {
    order_number: "",
    origin_warehouse_id: "",
    destination_warehouse_id: "",
    client_name: "",
    client_contact: "",
    cargo_description: "",
    weight_kg: "",
    volume_m3: "",
    deadline_at: "",
    notes: "",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

const decimalOnChange = (val: string, setter: (v: string) => void) => {
    if (val === "" || /^\d*\.?\d*$/.test(val)) setter(val);
};

// Polish phone: 9 digits, optionally with +48 prefix and spaces/dashes
const PHONE_REGEX = /^(\+48[\s-]?)?\d{3}[\s-]?\d{3}[\s-]?\d{3}$/;
// Email regex
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const validateContact = (contact: string): boolean => {
    if (!contact) return true; // optional field
    const trimmed = contact.trim();
    return PHONE_REGEX.test(trimmed) || EMAIL_REGEX.test(trimmed);
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function OrdersPage() {
    const [statusFilter, setStatusFilter] = useState<string>("");
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [createForm, setCreateForm] = useState(emptyForm);
    const [cancelDialog, setCancelDialog] = useState({open: false, id: "", label: ""});
    const queryClient = useQueryClient();
    const navigate = useNavigate();

    const {data, isLoading, error} = useQuery({
        queryKey: ["orders", statusFilter],
        queryFn: () =>
            ordersApi.list({
                per_page: 100,
                status: statusFilter ? (statusFilter as OrderStatus) : undefined,
            }),
    });

    const {data: warehousesData} = useQuery({
        queryKey: ["warehouses"],
        queryFn: () => warehouseApi.list({per_page: 100}),
    });

    const orders = data?.data?.items || [];
    const warehouses: Warehouse[] = warehousesData?.data?.items || [];

    const {search, setSearch, filtered} = useTableFilters(orders, {
        searchFields: ["order_number", "client_name"],
    });

    const validateForm = (): boolean => {
        if (createForm.client_contact && !validateContact(createForm.client_contact)) {
            toast.error("Kontakt musi być poprawnym numerem telefonu (np. 123 456 789) lub adresem email");
            return false;
        }
        if (createForm.weight_kg !== "") {
            const w = parseFloat(createForm.weight_kg);
            if (isNaN(w) || w <= 0 || w > 99999) {
                toast.error("Waga musi być liczbą między 0 a 99 999 kg");
                return false;
            }
        }
        if (createForm.volume_m3 !== "") {
            const v = parseFloat(createForm.volume_m3);
            if (isNaN(v) || v <= 0 || v > 999) {
                toast.error("Objętość musi być liczbą między 0 a 999 m³");
                return false;
            }
        }
        return true;
    };

    const createMutation = useMutation({
        mutationFn: () =>
            ordersApi.create({
                order_number: createForm.order_number,
                client_name: createForm.client_name,
                origin_warehouse_id: createForm.origin_warehouse_id,
                destination_warehouse_id: createForm.destination_warehouse_id,
                client_contact: createForm.client_contact || undefined,
                cargo_description: createForm.cargo_description || undefined,
                weight_kg: createForm.weight_kg ? parseFloat(createForm.weight_kg) : undefined,
                volume_m3: createForm.volume_m3 ? parseFloat(createForm.volume_m3) : undefined,
                deadline_at: createForm.deadline_at
                    ? new Date(createForm.deadline_at).toISOString()
                    : undefined,
                notes: createForm.notes || undefined,
            }),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["orders"]});
            toast.success("Zamówienie zostało utworzone");
            setCreateDialogOpen(false);
            setCreateForm(emptyForm);
        },
        onError: (error: { message: string }) => {
            toast.error(error.message || "Błąd podczas tworzenia zamówienia");
        },
    });

    const cancelMutation = useMutation({
        mutationFn: (id: string) => ordersApi.cancel(id),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["orders"]});
            toast.success("Zamówienie zostało anulowane");
            setCancelDialog({open: false, id: "", label: ""});
        },
        onError: (error: { message: string }) => {
            toast.error(error.message || "Błąd podczas anulowania zamówienia");
        },
    });

    const canCancel = (status: OrderStatus) =>
        status === OrderStatus.PENDING || status === OrderStatus.ASSIGNED;

    if (error) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="text-center text-destructive">Błąd podczas ładowania zamówień</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <h1 className="text-3xl font-bold">Zamówienia</h1>
                <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="mr-2 h-4 w-4"/>
                    Nowe zamówienie
                </Button>
            </div>

            <TableToolbar
                search={search}
                onSearchChange={setSearch}
                placeholder="Szukaj po numerze zamówienia, kliencie..."
                extra={
                    <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-muted-foreground"/>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                            {statusFilterOptions.map((option) => (
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                    </div>
                }
            />

            {isLoading ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin"/>
                </div>
            ) : filtered.length === 0 ? (
                <div className="flex h-64 flex-col items-center justify-center text-center">
                    <Package className="mb-4 h-12 w-12 text-muted-foreground"/>
                    <h3 className="text-lg font-semibold">Brak zamówień</h3>
                    <p className="text-muted-foreground">
                        {statusFilter || search
                            ? "Nie znaleziono zamówień o podanych kryteriach"
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
                            {filtered.map((order: Order) => {
                                const statusConfig = orderStatusConfig[order.status];
                                return (
                                    <TableRow
                                        key={order.id}
                                        className="cursor-pointer hover:bg-muted/50"
                                        onClick={() => navigate(`/orders/${order.id}`)}
                                    >
                                        <TableCell className="font-medium">{order.order_number}</TableCell>
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
                                        <TableCell onClick={(e) => e.stopPropagation()}>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon">
                                                        <MoreHorizontal className="h-4 w-4"/>
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem onClick={() => navigate(`/orders/${order.id}`)}>
                                                        Szczegóły
                                                    </DropdownMenuItem>
                                                    {canCancel(order.status) && (
                                                        <DropdownMenuItem
                                                            onClick={() => setCancelDialog({
                                                                open: true,
                                                                id: order.id,
                                                                label: order.order_number
                                                            })}
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

            {/* Create Order Dialog */}
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Nowe zamówienie</DialogTitle>
                        <DialogDescription>Wypełnij dane nowego zamówienia transportowego.</DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="order_number">Nr zamówienia *</Label>
                                <Input
                                    id="order_number"
                                    placeholder="ORD-2024-001"
                                    value={createForm.order_number}
                                    onChange={(e) => setCreateForm(p => ({...p, order_number: e.target.value}))}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="client_name">Klient *</Label>
                                <Input
                                    id="client_name"
                                    placeholder="Nazwa klienta"
                                    value={createForm.client_name}
                                    onChange={(e) => setCreateForm(p => ({...p, client_name: e.target.value}))}
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Magazyn nadania *</Label>
                                <select
                                    value={createForm.origin_warehouse_id}
                                    onChange={(e) => setCreateForm(p => ({...p, origin_warehouse_id: e.target.value}))}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                >
                                    <option value="">Wybierz magazyn...</option>
                                    {warehouses.map((w) => (
                                        <option key={w.id} value={w.id}>{w.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <Label>Magazyn docelowy *</Label>
                                <select
                                    value={createForm.destination_warehouse_id}
                                    onChange={(e) => setCreateForm(p => ({
                                        ...p,
                                        destination_warehouse_id: e.target.value
                                    }))}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                >
                                    <option value="">Wybierz magazyn...</option>
                                    {warehouses.map((w) => (
                                        <option key={w.id} value={w.id}>{w.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="client_contact">Kontakt do klienta</Label>
                                <Input
                                    id="client_contact"
                                    placeholder="tel. 123 456 789 lub email"
                                    value={createForm.client_contact}
                                    onChange={(e) => setCreateForm(p => ({...p, client_contact: e.target.value}))}
                                    className={
                                        createForm.client_contact && !validateContact(createForm.client_contact)
                                            ? "border-destructive"
                                            : ""
                                    }
                                />
                                {createForm.client_contact && !validateContact(createForm.client_contact) && (
                                    <p className="text-xs text-destructive">
                                        Podaj poprawny numer telefonu lub adres email
                                    </p>
                                )}
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="deadline_at">Termin dostawy</Label>
                                <Input
                                    id="deadline_at"
                                    type="datetime-local"
                                    value={createForm.deadline_at}
                                    onChange={(e) => setCreateForm(p => ({...p, deadline_at: e.target.value}))}
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="weight_kg">Waga (kg)</Label>
                                <Input
                                    id="weight_kg"
                                    type="text"
                                    inputMode="decimal"
                                    placeholder="np. 1500"
                                    value={createForm.weight_kg}
                                    onChange={(e) =>
                                        decimalOnChange(e.target.value, (v) =>
                                            setCreateForm(p => ({...p, weight_kg: v}))
                                        )
                                    }
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="volume_m3">Objętość (m³)</Label>
                                <Input
                                    id="volume_m3"
                                    type="text"
                                    inputMode="decimal"
                                    placeholder="np. 12.5"
                                    value={createForm.volume_m3}
                                    onChange={(e) =>
                                        decimalOnChange(e.target.value, (v) =>
                                            setCreateForm(p => ({...p, volume_m3: v}))
                                        )
                                    }
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="cargo_description">Opis ładunku</Label>
                            <Textarea
                                id="cargo_description"
                                placeholder="Co jest przewożone..."
                                value={createForm.cargo_description}
                                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                                    setCreateForm(p => ({...p, cargo_description: e.target.value}))
                                }
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="notes">Uwagi</Label>
                            <Textarea
                                id="notes"
                                placeholder="Dodatkowe informacje..."
                                value={createForm.notes}
                                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                                    setCreateForm(p => ({...p, notes: e.target.value}))
                                }
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Anuluj</Button>
                        <Button
                            onClick={() => {
                                if (!validateForm()) return;
                                createMutation.mutate();
                            }}
                            disabled={
                                createMutation.isPending ||
                                !createForm.order_number ||
                                !createForm.client_name ||
                                !createForm.origin_warehouse_id ||
                                !createForm.destination_warehouse_id
                            }
                        >
                            {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                            Utwórz zamówienie
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Cancel Dialog */}
            <ConfirmDialog
                open={cancelDialog.open}
                onOpenChange={(open) => setCancelDialog(d => ({...d, open}))}
                title="Anulować zamówienie?"
                description={<>Czy na pewno chcesz anulować zamówienie <strong>{cancelDialog.label}</strong>? Tej
                    operacji nie można cofnąć.</>}
                confirmLabel="Tak, anuluj"
                cancelLabel="Nie, zachowaj"
                isPending={cancelMutation.isPending}
                onConfirm={() => cancelMutation.mutate(cancelDialog.id)}
            />
        </div>
    );
}