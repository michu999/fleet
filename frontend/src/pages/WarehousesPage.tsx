/**
 * Warehouses / Locations management page
 * Visible only for: ADMIN, SUPER_ADMIN, DISPATCHER
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { warehouseApi } from "@/api";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { Plus, MoreHorizontal, Loader2, Warehouse, Search } from "lucide-react";
import { UserRole } from "@/types";
import type { Warehouse as WarehouseType } from "@/types";

// ─── Types ───────────────────────────────────────────────────────────────────

enum WarehouseTypeEnum {
  WAREHOUSE = "warehouse",
  CLIENT = "client",
  PICKUP_POINT = "pickup_point",
}

const warehouseTypeConfig: Record<WarehouseTypeEnum, { label: string; variant: "default" | "secondary" | "outline" }> = {
  [WarehouseTypeEnum.WAREHOUSE]: { label: "Magazyn", variant: "default" },
  [WarehouseTypeEnum.CLIENT]: { label: "Klient", variant: "secondary" },
  [WarehouseTypeEnum.PICKUP_POINT]: { label: "Punkt odbioru", variant: "outline" },
};

const emptyForm = {
  name: "",
  address: "",
  latitude: "",
  longitude: "",
  warehouse_type: WarehouseTypeEnum.WAREHOUSE,
  is_active: true,
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function WarehousesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState<WarehouseType | null>(null);
  const [createForm, setCreateForm] = useState(emptyForm);
  const [editForm, setEditForm] = useState(emptyForm);

  // Sprawdź uprawnienia
  const canManage = user?.role === UserRole.SUPER_ADMIN
    || user?.role === UserRole.ADMIN
    || user?.role === UserRole.DISPATCHER;

  // Fetch warehouses
  const { data, isLoading, error } = useQuery({
    queryKey: ["warehouses"],
    queryFn: () => warehouseApi.list({ per_page: 100 }),
  });

  // Create mutation
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
      await queryClient.invalidateQueries({ queryKey: ["warehouses"] });
      toast.success("Lokalizacja została dodana");
      setCreateDialogOpen(false);
      setCreateForm(emptyForm);
    },

    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas dodawania lokalizacji");
    },
  });

  // Update mutation
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
      await queryClient.invalidateQueries({ queryKey: ["warehouses"] });
      toast.success("Lokalizacja została zaktualizowana");
      setEditDialogOpen(false);
      setEditingWarehouse(null);
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas aktualizacji lokalizacji");
    },
  });

  // Deactivate mutation
  const deactivateMutation = useMutation({
    mutationFn: (id: string) =>
      warehouseApi.update(id, { is_active: false }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["warehouses"] });
      toast.success("Lokalizacja została dezaktywowana");
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas dezaktywacji");
    },
  });

  const warehouses: WarehouseType[] = data?.data?.items || [];

  const filteredWarehouses = warehouses.filter((w) =>
    w.name.toLowerCase().includes(search.toLowerCase()) ||
    w.address.toLowerCase().includes(search.toLowerCase())
  );

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
        <div className="text-center text-destructive">
          Błąd podczas ładowania lokalizacji
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-3xl font-bold">Lokalizacje</h1>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Dodaj lokalizację
        </Button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 max-w-sm">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Szukaj po nazwie lub adresie..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : filteredWarehouses.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <Warehouse className="mb-4 h-12 w-12 text-muted-foreground" />
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
              {filteredWarehouses.map((warehouse) => {
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
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEditClick(warehouse)}>
                            Edytuj
                          </DropdownMenuItem>
                          {warehouse.is_active && (
                            <DropdownMenuItem
                              onClick={() => deactivateMutation.mutate(warehouse.id)}
                              className="text-destructive"
                            >
                              Dezaktywuj
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
    </div>
  );
}

// ─── Reusable Form Dialog ─────────────────────────────────────────────────────

interface FormState {
  name: string;
  address: string;
  latitude: string;
  longitude: string;
  warehouse_type: WarehouseTypeEnum;
  is_active: boolean;
}

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
              onChange={(e) => setForm(p => ({ ...p, name: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">Adres *</Label>
            <Input
              id="address"
              placeholder="ul. Logistyczna 1, 02-001 Warszawa"
              value={form.address}
              onChange={(e) => setForm(p => ({ ...p, address: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Typ lokalizacji</Label>
            <select
              value={form.warehouse_type}
              onChange={(e) => setForm(p => ({ ...p, warehouse_type: e.target.value as WarehouseTypeEnum }))}
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
                onChange={(e) => setForm(p => ({ ...p, latitude: e.target.value }))}
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
                onChange={(e) => setForm(p => ({ ...p, longitude: e.target.value }))}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Współrzędne możesz znaleźć klikając prawym przyciskiem myszy na Google Maps.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Anuluj
          </Button>
          <Button onClick={onSubmit} disabled={isPending || !isValid}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}