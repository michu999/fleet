/**
 * Reusable table toolbar with search and filter toggles.
 *
 * Usage:
 *   <TableToolbar
 *     search={search}
 *     onSearchChange={setSearch}
 *     showInactive={showInactive}
 *     onShowInactiveChange={setShowInactive}
 *     placeholder="Szukaj po numerze rejestracyjnym..."
 *   />
 */

import {Search} from "lucide-react";
import {Input} from "@/components/ui/input";
import {Button} from "@/components/ui/button";
import {cn} from "@/lib/utils";

interface TableToolbarProps {
    search: string;
    onSearchChange: (value: string) => void;
    placeholder?: string;
    showInactive?: boolean;
    onShowInactiveChange?: (value: boolean) => void;
    inactiveLabel?: string;
    /** Additional filter buttons or elements */
    extra?: React.ReactNode;
}

export function TableToolbar({
                                 search,
                                 onSearchChange,
                                 placeholder = "Szukaj...",
                                 showInactive,
                                 onShowInactiveChange,
                                 inactiveLabel = "Nieaktywne",
                                 extra,
                             }: TableToolbarProps) {
    return (
        <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"/>
                <Input
                    placeholder={placeholder}
                    value={search}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10"
                />
            </div>

            {/* Show inactive toggle */}
            {onShowInactiveChange !== undefined && (
                <Button
                    variant={showInactive ? "secondary" : "outline"}
                    size="sm"
                    onClick={() => onShowInactiveChange(!showInactive)}
                    className={cn(showInactive && "border-primary")}
                >
                    {showInactive ? `Ukryj ${inactiveLabel.toLowerCase()}` : `Pokaż ${inactiveLabel.toLowerCase()}`}
                </Button>
            )}

            {/* Extra filters */}
            {extra}
        </div>
    );
}