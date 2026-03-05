/**
 * Login page with Google OAuth
 */

import { useNavigate } from "react-router-dom";
import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authApi } from "@/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Truck } from "lucide-react";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
console.log("CLIENT ID:", JSON.stringify(GOOGLE_CLIENT_ID));

function LoginContent() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const loginMutation = useMutation({
    mutationFn: (credential: string) => authApi.googleLogin(credential),
    onSuccess: (response) => {
      // Invalidate and refetch user data
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      
      const { is_new_user, user } = response.data;
      
      if (is_new_user) {
        toast.success(`Witamy, ${user.name}! Twoje konto zostało utworzone.`);
      } else {
        toast.success(`Witamy ponownie, ${user.name}!`);
      }
      
      navigate("/dashboard");
    },
    onError: (error: { message: string }) => {
      toast.error(error.message || "Błąd logowania. Spróbuj ponownie.");
    },
  });

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4 text-center">
          {/* Logo */}
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary">
            <Truck className="h-8 w-8 text-primary-foreground" />
          </div>
          
          <div>
            <CardTitle className="text-2xl font-bold">Fleet SaaS</CardTitle>
            <CardDescription className="mt-2">
              Zarządzanie flotą pojazdów
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="text-center text-sm text-muted-foreground">
            Zaloguj się, aby kontynuować
          </div>
          
          {/* Google Login Button */}
          <div className="flex justify-center">
            {GOOGLE_CLIENT_ID ? (
              <GoogleLogin
                onSuccess={(credentialResponse) => {
                  if (credentialResponse.credential) {
                    loginMutation.mutate(credentialResponse.credential);
                  }
                }}
                onError={() => {
                  toast.error("Błąd logowania Google. Spróbuj ponownie.");
                }}
                theme="outline"
                size="large"
                text="signin_with"
                shape="rectangular"
              />
            ) : (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-center text-sm text-destructive">
                Brak konfiguracji Google OAuth.
              </div>
            )}
          </div>
          
          {loginMutation.isPending && (
            <div className="text-center text-sm text-muted-foreground">
              Logowanie...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  if (!GOOGLE_CLIENT_ID) {
    return <LoginContent />;
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <LoginContent />
    </GoogleOAuthProvider>
  );
}
