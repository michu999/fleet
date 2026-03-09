/**
 * Application router with protected routes
 */

import {ReactNode} from "react";
import {
    BrowserRouter,
    Routes,
    Route,
    Navigate,
    Outlet,
} from "react-router-dom";
import {useAuth} from "@/hooks/useAuth";
import {Loader2} from "lucide-react";

// Pages (lazy loaded later)
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import VehiclesPage from "@/pages/VehiclesPage";
import OrdersPage from "@/pages/OrdersPage";
import OrderDetailPage from "@/pages/OrderDetailPage";

// Layout
import {AppLayout} from "@/components/layout/AppLayout";
import WarehousesPage from "@/pages/WarehousesPage.tsx";

/**
 * Loading spinner component
 */
function LoadingSpinner() {
    return (
        <div className="flex h-screen w-full items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary"/>
        </div>
    );
}

/**
 * Protected route wrapper - redirects to login if not authenticated
 */
function ProtectedRoute({children}: { children?: ReactNode }) {
    const {user, isLoading} = useAuth();

    if (isLoading) {
        return <LoadingSpinner/>;
    }

    if (!user) {
        return <Navigate to="/login" replace/>;
    }

    return children ? <>{children}</> : <Outlet/>;
}

/**
 * Public route wrapper - redirects to dashboard if already authenticated
 */
function PublicRoute({children}: { children: ReactNode }) {
    const {user, isLoading} = useAuth();

    if (isLoading) {
        return <LoadingSpinner/>;
    }

    if (user) {
        return <Navigate to="/dashboard" replace/>;
    }

    return <>{children}</>;
}

/**
 * Application router
 */
export function AppRouter() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Public routes */}
                <Route
                    path="/login"
                    element={
                        <PublicRoute>
                            <LoginPage/>
                        </PublicRoute>
                    }
                />

                {/* Protected routes with layout */}
                <Route
                    element={
                        <ProtectedRoute>
                            <AppLayout>
                                <Outlet/>
                            </AppLayout>
                        </ProtectedRoute>
                    }
                >
                    <Route path="/dashboard" element={<DashboardPage/>}/>
                    <Route path="/vehicles" element={<VehiclesPage/>}/>
                    <Route path="/orders" element={<OrdersPage/>}/>
                    <Route path="/orders" element={<OrdersPage/>}/>
                    <Route path="/orders/:id" element={<OrderDetailPage/>}/> {/* ← dodaj */}
                    <Route path="/warehouses" element={<ProtectedRoute><WarehousesPage/></ProtectedRoute>}/>
                    <Route path="/warehouses" element={<ProtectedRoute><WarehousesPage/></ProtectedRoute>}/>
                </Route>

                {/* Redirects */}
                <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
                <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
            </Routes>
        </BrowserRouter>
    );
}

export default AppRouter;
