/**
 * Ops Panel — Super Admin interface for managing tenants and users
 */

import {useState} from "react";
import {useQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import {useNavigate} from "react-router-dom";
import {toast} from "sonner";
import {adminApi} from "@/api/admin";
import {useAuth} from "@/hooks/useAuth";
import {TenantPlan, UserRole} from "@/types";
import type {Tenant, User} from "@/types";
import type {TenantCreatePayload, UserCreatePayload, TenantStats} from "@/api/admin";

import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Input} from "@/components/ui/input";
import {Label} from "@/components/ui/label";
import {ConfirmDialog} from "@/components/ui/confirm-dialog";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
    Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Building2, Users, Plus, MoreHorizontal, Loader2, ChevronLeft,
    Package, Truck, ShieldCheck, ToggleLeft, ToggleRight, LogIn,
} from "lucide-react";

// ─── Config ────────────────────────────────────────────────────────────────

const planConfig: Record<TenantPlan, { label: string; variant: "default" | "secondary" | "outline" | "success" }> = {
    [TenantPlan.TRIAL]: {label: "Trial", variant: "outline"},
    [TenantPlan.BASIC]: {label: "Basic", variant: "secondary"},
    [TenantPlan.PROFESSIONAL]: {label: "Professional", variant: "default"},
    [TenantPlan.ENTERPRISE]: {label: "Enterprise", variant: "success"},
};

const roleLabels: Record<UserRole, string> = {
    [UserRole.SUPER_ADMIN]: "Super Admin",
    [UserRole.ADMIN]: "Admin",
    [UserRole.MANAGER]: "Manager",
    [UserRole.DISPATCHER]: "Dyspozytor",
    [UserRole.DRIVER]: "Kierowca",
};

const roleOptions = [UserRole.ADMIN, UserRole.MANAGER, UserRole.DISPATCHER, UserRole.DRIVER];
const planOptions = Object.values(TenantPlan);

const emptyTenantForm: TenantCreatePayload = {
    name: "", slug: "", domain: "", plan: TenantPlan.TRIAL, max_users: 10,
};

const emptyUserForm: UserCreatePayload = {
    email: "", name: "", role: UserRole.ADMIN,
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function slugify(name: string): string {
    return name.toLowerCase().trim().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-");
}

function StatCard({icon: Icon, label, value}: { icon: React.ElementType; label: string; value: number }) {
    return (
        <div className="flex items-center gap-3 rounded-lg border bg-muted/30 px-4 py-3">
            <Icon className="h-5 w-5 text-muted-foreground"/>
            <div>
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-xl font-bold">{value}</p>
            </div>
        </div>
    );
}

// ─── Tenant Detail ─────────────────────────────────────────────────────────

function TenantDetail({tenant, onBack}: { tenant: Tenant; onBack: () => void }) {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const {setUser} = useAuth();
    const [createUserOpen, setCreateUserOpen] = useState(false);
    const [userForm, setUserForm] = useState(emptyUserForm);
    const [toggleDialog, setToggleDialog] = useState(false);
    const [impersonateTarget, setImpersonateTarget] = useState<User | null>(null);

    const {data: statsData} = useQuery({
        queryKey: ["admin", "stats", tenant.id],
        queryFn: () => adminApi.getTenantStats(tenant.id),
    });

    const {data: usersData, isLoading: usersLoading} = useQuery({
        queryKey: ["admin", "users", tenant.id],
        queryFn: () => adminApi.listUsers(tenant.id),
    });

    const stats: TenantStats | null = statsData?.data ?? null;
    const users: User[] = usersData?.data ?? [];

    const createUserMutation = useMutation({
        mutationFn: () => adminApi.createUser(tenant.id, userForm),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["admin", "users", tenant.id]});
            await queryClient.invalidateQueries({queryKey: ["admin", "stats", tenant.id]});
            toast.success(`Użytkownik ${userForm.email} został dodany`);
            setCreateUserOpen(false);
            setUserForm(emptyUserForm);
        },
        onError: (e: { message: string }) => toast.error(e.message || "Błąd podczas tworzenia użytkownika"),
    });

    const toggleUserMutation = useMutation({
        mutationFn: (user: User) => adminApi.updateUser(user.id, {is_active: !user.is_active}),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["admin", "users", tenant.id]});
            toast.success("Status użytkownika zmieniony");
        },
        onError: (e: { message: string }) => toast.error(e.message),
    });

    const changeRoleMutation = useMutation({
        mutationFn: ({userId, role}: { userId: string; role: UserRole }) =>
            adminApi.updateUser(userId, {role}),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["admin", "users", tenant.id]});
            toast.success("Rola zaktualizowana");
        },
        onError: (e: { message: string }) => toast.error(e.message),
    });

    const toggleTenantMutation = useMutation({
        mutationFn: () => adminApi.updateTenant(tenant.id, {is_active: !tenant.is_active}),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["admin", "tenants"]});
            toast.success(`Tenant ${tenant.is_active ? "dezaktywowany" : "aktywowany"}`);
            setToggleDialog(false);
            onBack();
        },
        onError: (e: { message: string }) => toast.error(e.message),
    });

    const impersonateMutation = useMutation({
        mutationFn: (userId: string) => adminApi.impersonate(userId),
        onSuccess: async (res) => {
            const impersonatedUser = res.data?.user ?? res.data;
            queryClient.setQueryData(["auth", "me"], impersonatedUser); // ← zamiast setUser
            toast.success(`Zalogowano jako ${impersonatedUser.name}`);
            setImpersonateTarget(null);
            navigate("/dashboard");
        },
        onError: (e: { message: string }) => toast.error(e.message || "Błąd impersonacji"),
    });

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={onBack}>
                    <ChevronLeft className="h-5 w-5"/>
                </Button>
                <div className="flex-1">
                    <div className="flex items-center gap-3">
                        <h2 className="text-2xl font-bold">{tenant.name}</h2>
                        <Badge variant={planConfig[tenant.plan]?.variant || "default"}>
                            {planConfig[tenant.plan]?.label || tenant.plan}
                        </Badge>
                        <Badge variant={tenant.is_active ? "success" : "destructive"}>
                            {tenant.is_active ? "Aktywny" : "Nieaktywny"}
                        </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{tenant.slug} · {tenant.domain || "brak domeny"}</p>
                </div>
                <Button variant={tenant.is_active ? "destructive" : "default"} size="sm"
                        onClick={() => setToggleDialog(true)}>
                    {tenant.is_active
                        ? <><ToggleLeft className="mr-2 h-4 w-4"/>Dezaktywuj</>
                        : <><ToggleRight className="mr-2 h-4 w-4"/>Aktywuj</>
                    }
                </Button>
            </div>

            {stats && (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <StatCard icon={Users} label="Użytkownicy" value={stats.users_count}/>
                    <StatCard icon={Truck} label="Pojazdy" value={stats.vehicles_count}/>
                    <StatCard icon={Package} label="Zamówienia" value={stats.orders_count}/>
                    <StatCard icon={ShieldCheck} label="Aktywne trasy" value={stats.active_trips_count}/>
                </div>
            )}

            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">
                        Użytkownicy
                        <span className="ml-2 text-sm font-normal text-muted-foreground">
              {users.length} / {tenant.max_users}
            </span>
                    </h3>
                    <Button size="sm" onClick={() => setCreateUserOpen(true)}>
                        <Plus className="mr-2 h-4 w-4"/>Dodaj użytkownika
                    </Button>
                </div>

                {usersLoading ? (
                    <div className="flex h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin"/>
                    </div>
                ) : users.length === 0 ? (
                    <div
                        className="flex h-32 items-center justify-center rounded-md border text-muted-foreground text-sm">
                        Brak użytkowników — dodaj pierwszego admina tenanta
                    </div>
                ) : (
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Imię i nazwisko</TableHead>
                                    <TableHead>Rola</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead className="w-[70px]">Akcje</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {users.map((user) => (
                                    <TableRow key={user.id}>
                                        <TableCell className="font-medium">{user.email}</TableCell>
                                        <TableCell>{user.name}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{roleLabels[user.role] || user.role}</Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={user.is_active ? "success" : "destructive"}>
                                                {user.is_active ? "Aktywny" : "Nieaktywny"}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon"><MoreHorizontal
                                                        className="h-4 w-4"/></Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    {user.is_active && (
                                                        <DropdownMenuItem onClick={() => setImpersonateTarget(user)}>
                                                            <LogIn className="mr-2 h-4 w-4"/>Zaloguj jako
                                                        </DropdownMenuItem>
                                                    )}
                                                    {roleOptions.map((role) =>
                                                        role !== user.role ? (
                                                            <DropdownMenuItem key={role}
                                                                              onClick={() => changeRoleMutation.mutate({
                                                                                  userId: user.id,
                                                                                  role
                                                                              })}>
                                                                Ustaw jako {roleLabels[role]}
                                                            </DropdownMenuItem>
                                                        ) : null
                                                    )}
                                                    <DropdownMenuItem
                                                        onClick={() => toggleUserMutation.mutate(user)}
                                                        className={user.is_active ? "text-destructive" : ""}
                                                    >
                                                        {user.is_active ? "Dezaktywuj" : "Aktywuj"}
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                )}
            </div>

            {/* Create User Dialog */}
            <Dialog open={createUserOpen} onOpenChange={setCreateUserOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Nowy użytkownik</DialogTitle>
                        <DialogDescription>
                            Dodaj użytkownika do tenanta <strong>{tenant.name}</strong>.
                            Użytkownik zaloguje się przez Google OAuth tym adresem email.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label>Email (Google) *</Label>
                            <Input type="email" placeholder="jan.kowalski@gmail.com" value={userForm.email}
                                   onChange={(e) => setUserForm(p => ({...p, email: e.target.value}))}/>
                        </div>
                        <div className="space-y-2">
                            <Label>Imię i nazwisko *</Label>
                            <Input placeholder="Jan Kowalski" value={userForm.name}
                                   onChange={(e) => setUserForm(p => ({...p, name: e.target.value}))}/>
                        </div>
                        <div className="space-y-2">
                            <Label>Rola</Label>
                            <select value={userForm.role}
                                    onChange={(e) => setUserForm(p => ({...p, role: e.target.value as UserRole}))}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                                {roleOptions.map((role) => (
                                    <option key={role} value={role}>{roleLabels[role]}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCreateUserOpen(false)}>Anuluj</Button>
                        <Button
                            onClick={() => {
                                if (!EMAIL_REGEX.test(userForm.email)) {
                                    toast.error("Podaj poprawny adres email");
                                    return;
                                }
                                createUserMutation.mutate();
                            }}
                            disabled={createUserMutation.isPending || !userForm.email || !userForm.name}
                        >
                            {createUserMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                            Utwórz użytkownika
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <ConfirmDialog
                open={toggleDialog}
                onOpenChange={setToggleDialog}
                title={tenant.is_active ? "Dezaktywować tenant?" : "Aktywować tenant?"}
                description={
                    tenant.is_active
                        ? <>Dezaktywacja zablokuje logowanie wszystkim użytkownikom
                            tenanta <strong>{tenant.name}</strong>.</>
                        : <>Aktywacja przywróci dostęp użytkownikom tenanta <strong>{tenant.name}</strong>.</>
                }
                confirmLabel={tenant.is_active ? "Dezaktywuj" : "Aktywuj"}
                isPending={toggleTenantMutation.isPending}
                onConfirm={() => toggleTenantMutation.mutate()}
            />

            <ConfirmDialog
                open={!!impersonateTarget}
                onOpenChange={(open) => !open && setImpersonateTarget(null)}
                title="Zalogować jako użytkownik?"
                description={
                    <>
                        Zostaniesz zalogowany
                        jako <strong>{impersonateTarget?.name}</strong> ({impersonateTarget?.email}).
                        Żółty baner u góry pozwoli Ci wrócić do konta Super Admin w każdej chwili.
                    </>
                }
                confirmLabel="Tak, zaloguj"
                isPending={impersonateMutation.isPending}
                onConfirm={() => impersonateTarget && impersonateMutation.mutate(impersonateTarget.id)}
            />
        </div>
    );
}

// ─── Main Page ─────────────────────────────────────────────────────────────

export default function OpsPanelPage() {
    const queryClient = useQueryClient();
    const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
    const [createTenantOpen, setCreateTenantOpen] = useState(false);
    const [tenantForm, setTenantForm] = useState(emptyTenantForm);

    const {data, isLoading} = useQuery({
        queryKey: ["admin", "tenants"],
        queryFn: () => adminApi.listTenants({limit: 100}),
    });

    const tenants: Tenant[] = data?.data ?? [];

    const createTenantMutation = useMutation({
        mutationFn: () => adminApi.createTenant({...tenantForm, domain: tenantForm.domain || undefined}),
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ["admin", "tenants"]});
            toast.success(`Tenant ${tenantForm.name} został utworzony`);
            setCreateTenantOpen(false);
            setTenantForm(emptyTenantForm);
        },
        onError: (e: { message: string }) => toast.error(e.message || "Błąd podczas tworzenia tenanta"),
    });

    if (selectedTenant) {
        return <TenantDetail tenant={selectedTenant} onBack={() => setSelectedTenant(null)}/>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Ops Panel</h1>
                    <p className="text-muted-foreground text-sm">Zarządzanie tenantami i użytkownikami</p>
                </div>
                <Button onClick={() => setCreateTenantOpen(true)}>
                    <Plus className="mr-2 h-4 w-4"/>Nowy tenant
                </Button>
            </div>

            {isLoading ? (
                <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin"/></div>
            ) : tenants.length === 0 ? (
                <div className="flex h-64 flex-col items-center justify-center text-center">
                    <Building2 className="mb-4 h-12 w-12 text-muted-foreground"/>
                    <h3 className="text-lg font-semibold">Brak tenantów</h3>
                    <p className="text-muted-foreground">Utwórz pierwszego klienta</p>
                </div>
            ) : (
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Nazwa</TableHead>
                                <TableHead>Slug</TableHead>
                                <TableHead>Plan</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Maks. użytkowników</TableHead>
                                <TableHead>Utworzony</TableHead>
                                <TableHead className="w-[70px]"/>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {tenants.map((tenant) => (
                                <TableRow key={tenant.id} className="cursor-pointer hover:bg-muted/50"
                                          onClick={() => setSelectedTenant(tenant)}>
                                    <TableCell className="font-medium">{tenant.name}</TableCell>
                                    <TableCell
                                        className="font-mono text-xs text-muted-foreground">{tenant.slug}</TableCell>
                                    <TableCell>
                                        <Badge variant={planConfig[tenant.plan]?.variant || "default"}>
                                            {planConfig[tenant.plan]?.label || tenant.plan}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={tenant.is_active ? "success" : "destructive"}>
                                            {tenant.is_active ? "Aktywny" : "Nieaktywny"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{tenant.max_users}</TableCell>
                                    <TableCell>{new Date(tenant.created_at).toLocaleDateString("pl-PL")}</TableCell>
                                    <TableCell onClick={(e) => e.stopPropagation()}>
                                        <Button variant="ghost" size="sm"
                                                onClick={() => setSelectedTenant(tenant)}>Zarządzaj</Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}

            <Dialog open={createTenantOpen} onOpenChange={setCreateTenantOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Nowy tenant</DialogTitle>
                        <DialogDescription>Utwórz nowego klienta. Po utworzeniu możesz dodać
                            użytkowników.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label>Nazwa firmy *</Label>
                            <Input placeholder="Kowalski Transport Sp. z o.o." value={tenantForm.name}
                                   onChange={(e) => setTenantForm(p => ({
                                       ...p,
                                       name: e.target.value,
                                       slug: slugify(e.target.value)
                                   }))}/>
                        </div>
                        <div className="space-y-2">
                            <Label>Slug *</Label>
                            <Input placeholder="kowalski-transport" value={tenantForm.slug}
                                   className="font-mono text-sm"
                                   onChange={(e) => setTenantForm(p => ({...p, slug: e.target.value}))}/>
                            <p className="text-xs text-muted-foreground">Generowany automatycznie, można edytować</p>
                        </div>
                        <div className="space-y-2">
                            <Label>Domena (opcjonalnie)</Label>
                            <Input placeholder="kowalski-transport.pl" value={tenantForm.domain}
                                   onChange={(e) => setTenantForm(p => ({...p, domain: e.target.value}))}/>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Plan</Label>
                                <select value={tenantForm.plan}
                                        onChange={(e) => setTenantForm(p => ({
                                            ...p,
                                            plan: e.target.value as TenantPlan
                                        }))}
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                                    {planOptions.map((plan) => (
                                        <option key={plan} value={plan}>{planConfig[plan]?.label || plan}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <Label>Maks. użytkowników</Label>
                                <Input type="number" min={1} max={500} value={tenantForm.max_users}
                                       onChange={(e) => setTenantForm(p => ({
                                           ...p,
                                           max_users: parseInt(e.target.value) || 10
                                       }))}/>
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCreateTenantOpen(false)}>Anuluj</Button>
                        <Button onClick={() => createTenantMutation.mutate()}
                                disabled={createTenantMutation.isPending || !tenantForm.name || !tenantForm.slug}>
                            {createTenantMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                            Utwórz tenant
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}