/**
 * Warehouses / Locations management page
 * Visible only for: ADMIN, SUPER_ADMIN, DISPATCHER
 */

import {useState} from "react";
import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import {toast} from "sonner";
import {warehouseApi} from "@/api";
import {useAuth} from "@/hooks/useAuth";
import {useTableFilters} from "@/hooks/useTableFilters";
import {TableToolbar} from "@/components/ui/table-toolbar";
import {ConfirmDialog} from "@/components/ui/confirm-dialog";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Input} from "@/components/ui/input";
import {Label} from "@/components/ui/label";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
    Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {Plus, MoreHorizontal, Loader2, Warehouse} from "lucide-react";
import {UserRole} from "@/types";
import type {Warehouse as WarehouseType} from "@/types";

// ─── Config ───────────────────────────────────────────────────────────────────

enum WarehouseTypeEnum {
    WAREHOUSE = "warehouse",
    CLIENT = "client",
    PICKUP_POINT = "pickup_point",
}

const warehouseTypeConfig: Record<WarehouseTypeEnum, {
    label: string;
    variant: "default" | "secondary" | "outline"
}> = {
    [WarehouseTypeEnum.WAREHOUSE]: {label: "Magazyn", variant: "default"},
    [WarehouseTypeEnum.CLIENT]: {label: "Klient", variant: "secondary"},
    [WarehouseTypeEnum.PICKUP_POINT]: {label: "Punkt odbioru", variant: "outline"},
};

interface FormState {
    name: string;
    address: string;
    latitude: string;
    longitude: string;
    warehouse_type: WarehouseTypeEnum;
    is_active: boolean;
}

const emptyForm: FormState = {
    name: "",
    address: "",
    latitude: "",
    longitude: "",
    warehouse_type: WarehouseTypeEnum.WAREHOUSE,
    is_active: true,
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function WarehousesPage() {
    const {user} = useAuth();
    const queryClient = useQueryClient();

    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [editingWarehouse, setEditingWarehouse] = useState<WarehouseType | null>(null);
    const [createForm, setCreateForm] = useState<FormState>(emptyForm);
    const [editForm, setEditForm] = useState<FormState>(emptyForm);
    const [deleteDialog, setDeleteDialog] = useState({open: false, id: "", label: ""});

    const canManage = user?.role === UserRole.SUPER_ADMIN
        || user?.role === UserRole.ADMIN
        || user?.role === UserRole.DISPATCHER;

    const {data, isLoading, error} = useQuery({
        queryKey: ["warehouses"],
        queryFn: () => warehouseApi.list({per_page: 100}),
    });

    const warehouses: WarehouseType[] = data?.data?.items || [];
    const {search, setSearch, showInactive, setShowInactive, filtered} = useTableFilters(warehouses, {
        searchFields: ["name", "address"],
    });

    const createMutation = useMutation({
        mutationFn: () =>
            warehouseApi.create({
                name: createForm.name,
                address: createForm.address,
                latitude: parseFloat(createForm.latitude),
                longitude: parseFloat(createForm.longitude),
                warehouse_type: createForm.warehouse_type,
                is_active: createForm.is_active,
            }),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["warehouses"]});
            toast.success("Lokalizacja została dodana");
            setCreateDialogOpen(false);
            setCreateForm(emptyForm);
        },
        onError: (error: { message: string }) => {
            toast.error(error.message || "Błąd podczas dodawania lokalizacji");
        },
    });

    const updateMutation = useMutation({
        mutationFn: () =>
            warehouseApi.update(editingWarehouse!.id, {
                name: editForm.name,
                address: editForm.address,
                latitude: parseFloat(editForm.latitude),
                longitude: parseFloat(editForm.longitude),
                warehouse_type: editForm.warehouse_type,
                is_active: editForm.is_active,
            }),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["warehouses"]});
            toast.success("Lokalizacja została zaktualizowana");
            setEditDialogOpen(false);
            setEditingWarehouse(null);
        },
        onError: (error: { message: string }) => {
            toast.error(error.message || "Błąd podczas aktualizacji lokalizacji");
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => warehouseApi.delete(id),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["warehouses"]});
            toast.success("Lokalizacja została usunięta");
            setDeleteDialog({open: false, id: "", label: ""});
        },
        onError: (error: { message: string }) => {
            toast.error(error.message || "Błąd podczas usuwania lokalizacji");
        },
    });

    const handleEditClick = (warehouse: WarehouseType) => {
        setEditingWarehouse(warehouse);
        setEditForm({
            name: warehouse.name,
            address: warehouse.address,
            latitude: String(warehouse.latitude),
            longitude: String(warehouse.longitude),
            warehouse_type: warehouse.warehouse_type as WarehouseTypeEnum,
            is_active: warehouse.is_active,
        });
        setEditDialogOpen(true);
    };

    if (!canManage) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="text-center text-muted-foreground">
                    Brak uprawnień do zarządzania lokalizacjami.
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-64 items-center justify-center">
                <div className="text-center text-destructive">Błąd podczas ładowania lokalizacji</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <h1 className="text-3xl font-bold">Lokalizacje</h1>
                <Button onClick={() => setCreateDialogOpen(true)}>
                    <Plus className="mr-2 h-4 w-4"/>
                    Dodaj lokalizację
                </Button>
            </div>

            <TableToolbar
                search={search}
                onSearchChange={setSearch}
                placeholder="Szukaj po nazwie lub adresie..."
                showInactive={showInactive}
                onShowInactiveChange={setShowInactive}
                inactiveLabel="Nieaktywne"
            />

            {isLoading ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin"/>
                </div>
            ) : filtered.length === 0 ? (
                <div className="flex h-64 flex-col items-center justify-center text-center">
                    <Warehouse className="mb-4 h-12 w-12 text-muted-foreground"/>
                    <h3 className="text-lg font-semibold">Brak lokalizacji</h3>
                    <p className="text-muted-foreground">
                        {search ? "Nie znaleziono lokalizacji" : "Dodaj pierwszą lokalizację"}
                    </p>
                </div>
            ) : (
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Nazwa</TableHead>
                                <TableHead>Adres</TableHead>
                                <TableHead>Typ</TableHead>
                                <TableHead>Współrzędne</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="w-[70px]">Akcje</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filtered.map((warehouse) => {
                                const typeConfig = warehouseTypeConfig[warehouse.warehouse_type as WarehouseTypeEnum];
                                return (
                                    <TableRow key={warehouse.id} className={!warehouse.is_active ? "opacity-50" : ""}>
                                        <TableCell className="font-medium">{warehouse.name}</TableCell>
                                        <TableCell className="max-w-[200px] truncate text-muted-foreground">
                                            {warehouse.address}
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={typeConfig?.variant || "default"}>
                                                {typeConfig?.label || warehouse.warehouse_type}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-sm text-muted-foreground">
                                            {warehouse.latitude.toFixed(4)}, {warehouse.longitude.toFixed(4)}
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={warehouse.is_active ? "default" : "secondary"}>
                                                {warehouse.is_active ? "Aktywna" : "Nieaktywna"}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon">
                                                        <MoreHorizontal className="h-4 w-4"/>
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem onClick={() => handleEditClick(warehouse)}>
                                                        Edytuj
                                                    </DropdownMenuItem>
                                                    {warehouse.is_active && (
                                                        <DropdownMenuItem
                                                            onClick={() => warehouseApi.update(warehouse.id, {is_active: false}).then(() => queryClient.invalidateQueries({queryKey: ["warehouses"]}))}
                                                            className="text-destructive"
                                                        >
                                                            Dezaktywuj
                                                        </DropdownMenuItem>
                                                    )}
                                                    <DropdownMenuItem
                                                        onClick={() => setDeleteDialog({
                                                            open: true,
                                                            id: warehouse.id,
                                                            label: warehouse.name
                                                        })}
                                                        className="text-destructive"
                                                    >
                                                        Usuń
                                                    </DropdownMenuItem>
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

            {/* Create Dialog */}
            <WarehouseFormDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                title="Nowa lokalizacja"
                description="Dodaj magazyn, adres klienta lub punkt odbioru."
                form={createForm}
                setForm={setCreateForm}
                onSubmit={() => createMutation.mutate()}
                isPending={createMutation.isPending}
                submitLabel="Dodaj lokalizację"
            />

            {/* Edit Dialog */}
            <WarehouseFormDialog
                open={editDialogOpen}
                onOpenChange={setEditDialogOpen}
                title="Edytuj lokalizację"
                description="Zaktualizuj dane lokalizacji."
                form={editForm}
                setForm={setEditForm}
                onSubmit={() => updateMutation.mutate()}
                isPending={updateMutation.isPending}
                submitLabel="Zapisz zmiany"
            />

            {/* Delete Dialog */}
            <ConfirmDialog
                open={deleteDialog.open}
                onOpenChange={(open) => setDeleteDialog(d => ({...d, open}))}
                title="Usunąć lokalizację?"
                description={<>Czy na pewno chcesz usunąć lokalizację <strong>{deleteDialog.label}</strong>? Tej
                    operacji nie można cofnąć.</>}
                confirmLabel="Usuń"
                isPending={deleteMutation.isPending}
                onConfirm={() => deleteMutation.mutate(deleteDialog.id)}
            />
        </div>
    );
}

// ─── Form Dialog ──────────────────────────────────────────────────────────────

interface WarehouseFormDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title: string;
    description: string;
    form: FormState;
    setForm: React.Dispatch<React.SetStateAction<FormState>>;
    onSubmit: () => void;
    isPending: boolean;
    submitLabel: string;
}

function WarehouseFormDialog({
                                 open, onOpenChange, title, description,
                                 form, setForm, onSubmit, isPending, submitLabel,
                             }: WarehouseFormDialogProps) {
    const isValid =
        form.name.trim() &&
        form.address.trim() &&
        form.latitude &&
        form.longitude &&
        !isNaN(parseFloat(form.latitude)) &&
        !isNaN(parseFloat(form.longitude));

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                    <DialogDescription>{description}</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="name">Nazwa *</Label>
                        <Input
                            id="name"
                            placeholder="np. Magazyn Warszawa"
                            value={form.name}
                            onChange={(e) => setForm(p => ({...p, name: e.target.value}))}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="address">Adres *</Label>
                        <Input
                            id="address"
                            placeholder="ul. Logistyczna 1, 02-001 Warszawa"
                            value={form.address}
                            onChange={(e) => setForm(p => ({...p, address: e.target.value}))}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Typ lokalizacji</Label>
                        <select
                            value={form.warehouse_type}
                            onChange={(e) => setForm(p => ({
                                ...p,
                                warehouse_type: e.target.value as WarehouseTypeEnum
                            }))}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                            <option value={WarehouseTypeEnum.WAREHOUSE}>Magazyn (własny)</option>
                            <option value={WarehouseTypeEnum.CLIENT}>Klient</option>
                            <option value={WarehouseTypeEnum.PICKUP_POINT}>Punkt odbioru</option>
                        </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="latitude">Szerokość geogr. *</Label>
                            <Input
                                id="latitude"
                                type="number"
                                step="0.0001"
                                placeholder="52.2297"
                                value={form.latitude}
                                onChange={(e) => setForm(p => ({...p, latitude: e.target.value}))}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="longitude">Długość geogr. *</Label>
                            <Input
                                id="longitude"
                                type="number"
                                step="0.0001"
                                placeholder="21.0122"
                                value={form.longitude}
                                onChange={(e) => setForm(p => ({...p, longitude: e.target.value}))}
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label>Status</Label>
                        <select
                            value={form.is_active ? "true" : "false"}
                            onChange={(e) => setForm(p => ({...p, is_active: e.target.value === "true"}))}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                            <option value="true">Aktywna</option>
                            <option value="false">Nieaktywna</option>
                        </select>
                    </div>
                    <p className="text-xs text-muted-foreground">
                        Współrzędne możesz znaleźć klikając prawym przyciskiem myszy na Google Maps.
                    </p>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Anuluj</Button>
                    <Button onClick={onSubmit} disabled={isPending || !isValid}>
                        {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                        {submitLabel}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}