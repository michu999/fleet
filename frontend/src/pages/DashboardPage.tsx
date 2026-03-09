/**
 * Dashboard page with stats and recent data
 */

import {useQuery} from "@tanstack/react-query";
import {vehiclesApi, ordersApi} from "@/api";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {Truck, Package, CheckCircle, Clock, Loader2,} from "lucide-react";
import {VehicleStatus, OrderStatus,} from "@/types";
import type {Vehicle, Order,} from "@/types";

// Status badge configuration
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

const vehicleStatusConfig: Record<VehicleStatus, {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
}> = {
    [VehicleStatus.AVAILABLE]: {label: "Dostępny", variant: "success"},
    [VehicleStatus.ON_ROUTE]: {label: "W trasie", variant: "default"},
    [VehicleStatus.MAINTENANCE]: {label: "Serwis", variant: "warning"},
    [VehicleStatus.INACTIVE]: {label: "Nieaktywny", variant: "secondary"},
    [VehicleStatus.RESERVED]: {label: "Zarezerwowany", variant: "outline"},
};

function StatCard({
                      title,
                      value,
                      icon: Icon,
                      isLoading,
                  }: {
    title: string;
    value: number;
    icon: React.ComponentType<{ className?: string }>;
    isLoading: boolean;
}) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{title}</CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground"/>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin"/>
                ) : (
                    <div className="text-2xl font-bold">{value}</div>
                )}
            </CardContent>
        </Card>
    );
}

export default function DashboardPage() {
    // Fetch vehicles
    const {data: vehiclesData, isLoading: vehiclesLoading} = useQuery({
        queryKey: ["vehicles"],
        queryFn: () => vehiclesApi.list({per_page: 100}),
        refetchInterval: 30000, // Refetch every 30 seconds
    });

    // Fetch orders
    const {data: ordersData, isLoading: ordersLoading} = useQuery({
        queryKey: ["orders"],
        queryFn: () => ordersApi.list({per_page: 100}),
        refetchInterval: 30000,
    });

    const vehicles = vehiclesData?.data?.items || [];
    const orders = ordersData?.data?.items || [];

    // Calculate stats
    const activeVehicles = vehicles.filter(
        (v: Vehicle) => v.status === VehicleStatus.ON_ROUTE
    ).length;

    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);

    const ordersToday = orders.filter((o: Order) => {
        const createdAt = new Date(o.created_at);
        return createdAt >= todayStart;
    }).length;

    const deliveredToday = orders.filter((o: Order) => {
        const createdAt = new Date(o.created_at);
        return createdAt >= todayStart && o.status === OrderStatus.DELIVERED;
    }).length;

    const pendingOrders = orders.filter(
        (o: Order) => o.status === OrderStatus.PENDING
    ).length;

    // Recent orders (last 5)
    const recentOrders = orders.slice(0, 5);

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold">Dashboard</h1>

            {/* Stats cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatCard
                    title="Aktywne pojazdy"
                    value={activeVehicles}
                    icon={Truck}
                    isLoading={vehiclesLoading}
                />
                <StatCard
                    title="Zamówienia dziś"
                    value={ordersToday}
                    icon={Package}
                    isLoading={ordersLoading}
                />
                <StatCard
                    title="Dostarczone dziś"
                    value={deliveredToday}
                    icon={CheckCircle}
                    isLoading={ordersLoading}
                />
                <StatCard
                    title="Oczekujące"
                    value={pendingOrders}
                    icon={Clock}
                    isLoading={ordersLoading}
                />
            </div>

            {/* Main content */}
            <div className="grid gap-6 lg:grid-cols-5">
                {/* Recent orders */}
                <Card className="lg:col-span-3">
                    <CardHeader>
                        <CardTitle>Ostatnie zamówienia</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {ordersLoading ? (
                            <div className="flex justify-center py-8">
                                <Loader2 className="h-8 w-8 animate-spin"/>
                            </div>
                        ) : recentOrders.length === 0 ? (
                            <div className="py-8 text-center text-muted-foreground">
                                Brak zamówień
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Nr zamówienia</TableHead>
                                        <TableHead>Klient</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Termin</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {recentOrders.map((order: Order) => {
                                        const statusConfig = orderStatusConfig[order.status];
                                        return (
                                            <TableRow key={order.id}>
                                                <TableCell className="font-medium">
                                                    {order.order_number}
                                                </TableCell>
                                                <TableCell>{order.client_name}</TableCell>
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
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>

                {/* Vehicles summary */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>Status pojazdów</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {vehiclesLoading ? (
                            <div className="flex justify-center py-8">
                                <Loader2 className="h-8 w-8 animate-spin"/>
                            </div>
                        ) : vehicles.length === 0 ? (
                            <div className="py-8 text-center text-muted-foreground">
                                Brak pojazdów
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {vehicles.slice(0, 8).map((vehicle: Vehicle) => {
                                    const statusConfig = vehicleStatusConfig[vehicle.status];
                                    return (
                                        <div
                                            key={vehicle.id}
                                            className="flex items-center justify-between"
                                        >
                                            <span className="font-medium">{vehicle.plate_number}</span>
                                            <Badge variant={statusConfig?.variant || "default"}>
                                                {statusConfig?.label || vehicle.status}
                                            </Badge>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
