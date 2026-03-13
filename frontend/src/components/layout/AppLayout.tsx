/**
 * Main application layout with sidebar and navbar
 */

import {ReactNode} from "react";
import {Sidebar} from "./Sidebar";
import {Navbar} from "./Navbar";
import {ImpersonationBanner} from "@/components/layout/ImpersonationBanner";

interface AppLayoutProps {
    children: ReactNode;
}

export function AppLayout({children}: AppLayoutProps) {
    return (
        <div className="flex h-screen flex-col overflow-hidden bg-background">
            <ImpersonationBanner/>
            <div className="flex flex-1 overflow-hidden">
                <div className="hidden md:block">
                    <Sidebar/>
                </div>
                <div className="flex flex-1 flex-col overflow-hidden">
                    <Navbar/>
                    <main className="flex-1 overflow-y-auto p-6">{children}</main>
                </div>
            </div>
        </div>
    );
}
