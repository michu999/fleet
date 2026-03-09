/**
 * Vehicles management page
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { vehiclesApi } from "@/api";
import { useTableFilters } from "@/hooks/useTableFilters";
import { TableToolbar } from "@/components/ui/table-toolbar";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Plus, MoreHorizontal, Loader2, Truck } from "lucide-react";
import { VehicleStatus, VehicleType } from "@/types";
import type { Vehicle, VehicleCreate, VehicleUpdate } from "@/types";

// ─── Config ───────────────────────────────────────────────────────────────────

const vehicleStatusConfig: Record<VehicleStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
  [VehicleStatus.AVAILABLE]: { label: "Dostępny", variant: "success" },
  [VehicleStatus.ON_ROUTE]: { label: "W trasie", variant: "default" },
  [VehicleStatus.MAINTENANCE]: { label: "Serwis", variant: "warning" },
  [VehicleStatus.INACTIVE]: { label: "Nieaktywny", variant: "secondary" },
  [VehicleStatus.RESERVED]: { label: "Zarezerwowany", variant: "outline" },
};

const vehicleTypeLabels: Record<VehicleType, string> = {
  [VehicleType.TRUCK]: "Ciężarówka",
  [VehicleType.VAN]: "Van",
  [VehicleType.OTHER]: "Inny",
};

interface VehicleFormData {
  plate_number: string;
  brand: string;
  model: string;
  year: string;
  vehicle_type: VehicleType;
  status: VehicleStatus;
}

const initialFormData: VehicleFormData = {
  plate_number: "",
  brand: "",
  model: "",
  year: "",
  vehicle_type: VehicleType.TRUCK,
  status: VehicleStatus.AVAILABLE,
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function VehiclesPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [formData, setFormData] = useState<VehicleFormData>(initialFormData);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, id: "", label: "" });
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["vehicles"],
    queryFn: () => vehiclesApi.list({ per_page: 100 }),
  });

  const vehicles = data?.data?.items || [];
  const { search, setSearch, showInactive, setShowInactive, filtered } = useTableFilters(vehicles, {
    searchFields: ["plate_number", "brand", "model"],
  });

  const createMutation = useMutation({
    mutationFn: (data: VehicleCreate) => vehiclesApi.create(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      toast.success("Pojazd został dodany");
      handleCloseDialog();
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas dodawania pojazdu");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: VehicleUpdate }) =>
      vehiclesApi.update(id, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      toast.success("Pojazd został zaktualizowany");
      handleCloseDialog();
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas aktualizacji pojazdu");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => vehiclesApi.delete(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      toast.success("Pojazd został usunięty");
      setDeleteDialog({ open: false, id: "", label: "" });
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd podczas usuwania pojazdu");
    },
  });

  const handleOpenDialog = (vehicle?: Vehicle) => {
    if (vehicle) {
      setEditingVehicle(vehicle);
      setFormData({
        plate_number: vehicle.plate_number,
        brand: vehicle.brand || "",
        model: vehicle.model || "",
        year: vehicle.year?.toString() || "",
        vehicle_type: vehicle.vehicle_type,
        status: vehicle.status,
      });
    } else {
      setEditingVehicle(null);
      setFormData(initialFormData);
    }
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setEditingVehicle(null);
    setFormData(initialFormData);
  };

  const handleSubmit = () => {
    if (formData.year) {
      const year = parseInt(formData.year);
      if (isNaN(year) || year < 1900 || year > new Date().getFullYear()) {
        toast.error(`Rok produkcji musi być liczbą między 1900 a ${new Date().getFullYear()}`);
        return;
      }
    }
    const vehicleData: VehicleCreate | VehicleUpdate = {
      plate_number: formData.plate_number,
      brand: formData.brand || undefined,
      model: formData.model || undefined,
      year: formData.year ? parseInt(formData.year) : undefined,
      vehicle_type: formData.vehicle_type,
      status: formData.status,
    };
    if (editingVehicle) {
      updateMutation.mutate({ id: editingVehicle.id, data: vehicleData });
    } else {
      createMutation.mutate(vehicleData as VehicleCreate);
    }
  };

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center text-destructive">Błąd podczas ładowania pojazdów</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-3xl font-bold">Pojazdy</h1>
        <Button onClick={() => handleOpenDialog()}>
          <Plus className="mr-2 h-4 w-4" />
          Dodaj pojazd
        </Button>
      </div>

      <TableToolbar
        search={search}
        onSearchChange={setSearch}
        placeholder="Szukaj po numerze rejestracyjnym, marce..."
        showInactive={showInactive}
        onShowInactiveChange={setShowInactive}
        inactiveLabel="Nieaktywne"
      />

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <Truck className="mb-4 h-12 w-12 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Brak pojazdów</h3>
          <p className="text-muted-foreground">
            {search ? "Nie znaleziono pasujących pojazdów" : "Dodaj pierwszy pojazd"}
          </p>
          {!search && (
            <Button className="mt-4" onClick={() => handleOpenDialog()}>
              <Plus className="mr-2 h-4 w-4" />Dodaj pojazd
            </Button>
          )}
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rejestracja</TableHead>
                <TableHead>Marka/Model</TableHead>
                <TableHead>Rok</TableHead>
                <TableHead>Typ</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[70px]">Akcje</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((vehicle: Vehicle) => {
                const statusConfig = vehicleStatusConfig[vehicle.status];
                return (
                  <TableRow key={vehicle.id}>
                    <TableCell className="font-medium">{vehicle.plate_number}</TableCell>
                    <TableCell>
                      {vehicle.brand || vehicle.model
                        ? `${vehicle.brand || ""} ${vehicle.model || ""}`.trim()
                        : "-"}
                    </TableCell>
                    <TableCell>{vehicle.year || "-"}</TableCell>
                    <TableCell>{vehicleTypeLabels[vehicle.vehicle_type] || vehicle.vehicle_type}</TableCell>
                    <TableCell>
                      <Badge variant={statusConfig?.variant || "default"}>
                        {statusConfig?.label || vehicle.status}
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
                          <DropdownMenuItem onClick={() => handleOpenDialog(vehicle)}>
                            Edytuj
                          </DropdownMenuItem>
                          {vehicle.status !== VehicleStatus.INACTIVE && (
                            <DropdownMenuItem
                              onClick={() => updateMutation.mutate({ id: vehicle.id, data: { status: VehicleStatus.INACTIVE } })}
                              className="text-destructive"
                            >
                              Dezaktywuj
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            onClick={() => setDeleteDialog({ open: true, id: vehicle.id, label: vehicle.plate_number })}
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

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingVehicle ? "Edytuj pojazd" : "Dodaj pojazd"}</DialogTitle>
            <DialogDescription>
              {editingVehicle ? "Zaktualizuj dane pojazdu" : "Wprowadź dane nowego pojazdu"}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="plate_number">Numer rejestracyjny *</Label>
              <Input
                id="plate_number"
                value={formData.plate_number}
                onChange={(e) => setFormData({ ...formData, plate_number: e.target.value })}
                placeholder="np. WA 12345"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="brand">Marka</Label>
                <Input
                  id="brand"
                  value={formData.brand}
                  onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                  placeholder="np. Volvo"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="model">Model</Label>
                <Input
                  id="model"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  placeholder="np. FH16"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="year">Rok produkcji</Label>
                <Input
                  id="year"
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                  placeholder="np. 2022"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="vehicle_type">Typ</Label>
                <select
                  id="vehicle_type"
                  value={formData.vehicle_type}
                  onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value as VehicleType })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {Object.entries(vehicleTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as VehicleStatus })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {Object.entries(vehicleStatusConfig).map(([value, config]) => (
                  <option key={value} value={value}>{config.label}</option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog}>Anuluj</Button>
            <Button
              onClick={handleSubmit}
              disabled={!formData.plate_number || createMutation.isPending || updateMutation.isPending}
            >
              {(createMutation.isPending || updateMutation.isPending) && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {editingVehicle ? "Zapisz" : "Dodaj"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog(d => ({ ...d, open }))}
        title="Usunąć pojazd?"
        description={<>Czy na pewno chcesz usunąć pojazd <strong>{deleteDialog.label}</strong>? Tej operacji nie można cofnąć.</>}
        confirmLabel="Usuń"
        isPending={deleteMutation.isPending}
        onConfirm={() => deleteMutation.mutate(deleteDialog.id)}
      />
    </div>
  );
}