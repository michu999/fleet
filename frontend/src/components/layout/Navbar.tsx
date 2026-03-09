/**
 * Application navbar
 */

import {useAuth} from "@/hooks/useAuth";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {Avatar, AvatarFallback, AvatarImage} from "@/components/ui/avatar";
import {Button} from "@/components/ui/button";
import {LogOut, User as UserIcon} from "lucide-react";
import type {UserRole} from "@/types";

const roleLabels: Record<UserRole, string> = {
    super_admin: "Super Admin",
    admin: "Administrator",
    manager: "Menedżer",
    dispatcher: "Dyspozytor",
    driver: "Kierowca",
};

export function Navbar() {
    const {user, logout, isLoggingOut} = useAuth();

    const getInitials = (name: string) => {
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b bg-background px-6">
            {/* Left side - can add breadcrumbs or page title here */}
            <div className="flex items-center gap-4">
                <h1 className="text-lg font-semibold md:hidden">Fleet SaaS</h1>
            </div>

            {/* Right side - user menu */}
            <div className="flex items-center gap-4">
                {user && (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                                <Avatar className="h-10 w-10">
                                    <AvatarImage src={user.picture || undefined} alt={user.name}/>
                                    <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
                                </Avatar>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent className="w-56" align="end" forceMount>
                            <DropdownMenuLabel className="font-normal">
                                <div className="flex flex-col space-y-1">
                                    <p className="text-sm font-medium leading-none">{user.name}</p>
                                    <p className="text-xs leading-none text-muted-foreground">
                                        {user.email}
                                    </p>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator/>
                            <DropdownMenuItem disabled>
                                <UserIcon className="mr-2 h-4 w-4"/>
                                <span>Rola: {roleLabels[user.role] || user.role}</span>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator/>
                            <DropdownMenuItem
                                onClick={() => logout()}
                                disabled={isLoggingOut}
                                className="text-destructive focus:text-destructive"
                            >
                                <LogOut className="mr-2 h-4 w-4"/>
                                <span>Wyloguj</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                )}
            </div>
        </header>
    );
}
