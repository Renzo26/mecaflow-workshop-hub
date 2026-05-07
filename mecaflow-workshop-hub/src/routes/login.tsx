import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { setAuth, isAuthenticated } from "@/lib/auth";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Entrar — MecaFlow" }] }),
  beforeLoad: () => {
    if (isAuthenticated()) throw redirect({ to: "/app" });
  },
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
        user: { id: string; name: string; email: string; role: string; workshop_id: string };
        workshop: { id: string; name: string };
      }>("/auth/login", { email, password });
      setAuth(data);
      navigate({ to: "/app" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden bg-sidebar text-sidebar-foreground lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
            <Wrench className="h-5 w-5" />
          </div>
          <span className="font-display text-xl font-bold">MecaFlow</span>
        </div>
        <div>
          <h2 className="font-display text-3xl font-bold leading-tight">
            Sua oficina, organizada do balcão até a saída do veículo.
          </h2>
          <p className="mt-3 text-sidebar-foreground/70">
            Conversas, agenda, clientes e equipe em um só lugar.
          </p>
        </div>
        <p className="text-xs text-sidebar-foreground/50">© MecaFlow</p>
      </div>

      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <h1 className="font-display text-2xl font-bold">Bem-vindo de volta</h1>
          <p className="mt-1 text-sm text-muted-foreground">Entre para acessar sua oficina.</p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                required
                placeholder="voce@oficina.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="senha">Senha</Label>
              </div>
              <Input
                id="senha"
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Primeira vez?{" "}
            <Link to="/cadastro" className="text-primary hover:underline">
              Cadastrar oficina
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
