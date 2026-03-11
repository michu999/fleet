/**
 * Application sidebar navigation
 */

import {useState} from "react";
import {Link, useLocation} from "react-router-dom";
import {cn} from "@/lib/utils";
import {useAuth} from "@/hooks/useAuth";
import {
    LayoutDashboard,
    Truck,
    Warehouse,
    Package,
    ChevronLeft,
    ChevronRight,
    LogOut,
    ShieldCheck
} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Avatar, AvatarFallback, AvatarImage} from "@/components/ui/avatar";
import {Badge} from "@/components/ui/badge";
import {UserRole} from "@/types";

interface NavItem {
    title: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
}

const getNavItems = (role: UserRole): NavItem[] => {
    const items: NavItem[] = [
        {
            title: "Dashboard",
            href: "/dashboard",
            icon: LayoutDashboard,
        },
        {
            title: "Pojazdy",
            href: "/vehicles",
            icon: Truck,
        },
        {
            title: "Zamówienia",
            href: "/orders",
            icon: Package,
        },
    ];

    if (
        role === UserRole.SUPER_ADMIN ||
        role === UserRole.ADMIN ||
        role === UserRole.DISPATCHER
    ) {
        items.push({
            title: "Lokalizacje",
            href: "/warehouses",
            icon: Warehouse,
        });
    }
    if (role === UserRole.SUPER_ADMIN) {
        items.push({
            title: "Ops Panel",
            href: "/ops",
            icon: ShieldCheck,
        });
    }

    return items;
};


const roleLabels: Record<UserRole, string> = {
    super_admin: "Super Admin",
    admin: "Administrator",
    manager: "Menedżer",
    dispatcher: "Dyspozytor",
    driver: "Kierowca",
};

export function Sidebar() {
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();
    const {user, logout, isLoggingOut} = useAuth();
    const navItems = user ? getNavItems(user.role) : [];

    const getInitials = (name: string) => {
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <aside
            className={cn(
                "flex h-screen flex-col border-r bg-card transition-all duration-300",
                collapsed ? "w-16" : "w-64"
            )}
        >
            {/* Header */}
            <div className="flex h-16 items-center justify-between border-b px-4">
                {!collapsed && (
                    <span className="text-xl font-bold text-primary">Fleet SaaS</span>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCollapsed(!collapsed)}
                    className="ml-auto"
                >
                    {collapsed ? (
                        <ChevronRight className="h-4 w-4"/>
                    ) : (
                        <ChevronLeft className="h-4 w-4"/>
                    )}
                </Button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 p-2">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.href;
                    const Icon = item.icon;


                    return (

                        <Link
                            key={item.href}
                            to={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            )}
                        >
                            <Icon className="h-5 w-5 shrink-0"/>
                            {!collapsed && <span>{item.title}</span>}
                        </Link>
                    );
                })}
            </nav>

            {/* User section */}
            <div className="border-t p-4">
                {user && (
                    <div
                        className={cn(
                            "flex items-center gap-3",
                            collapsed && "justify-center"
                        )}
                    >
                        <Avatar className="h-10 w-10 shrink-0">
                            <AvatarImage src={user.picture || undefined} alt={user.name}/>
                            <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
                        </Avatar>

                        {!collapsed && (
                            <div className="flex flex-col overflow-hidden">
                <span className="truncate text-sm font-medium">
                  {user.name}
                </span>
                                <Badge variant="secondary" className="w-fit text-xs">
                                    {roleLabels[user.role] || user.role}
                                </Badge>
                            </div>
                        )}
                    </div>
                )}

                <Button
                    variant="ghost"
                    size={collapsed ? "icon" : "default"}
                    onClick={() => logout()}
                    disabled={isLoggingOut}
                    className={cn("mt-3 w-full", collapsed && "w-10")}
                >
                    <LogOut className="h-4 w-4"/>
                    {!collapsed && <span className="ml-2">Wyloguj</span>}
                </Button>
            </div>
        </aside>
    );
}
