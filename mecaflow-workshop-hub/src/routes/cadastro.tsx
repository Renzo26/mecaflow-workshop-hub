import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Wrench, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { setAuth } from "@/lib/auth";

export const Route = createFileRoute("/cadastro")({
  head: () => ({ meta: [{ title: "Cadastrar oficina — MecaFlow" }] }),
  component: CadastroPage,
});

const steps = ["Oficina", "Conta"];

function CadastroPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [workshopName, setWorkshopName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const next = async (e: React.FormEvent) => {
    e.preventDefault();
    if (step < steps.length - 1) {
      setStep(step + 1);
      return;
    }

    setError("");
    setLoading(true);
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
        user: { id: string; name: string; email: string; role: string; workshop_id: string };
        workshop: { id: string; name: string };
      }>("/auth/register", { workshop_name: workshopName, name, email, password });
      setAuth(data);
      navigate({ to: "/app" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cadastrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-secondary/40 px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <Link to="/login" className="inline-flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Wrench className="h-5 w-5" />
          </div>
          <span className="font-display text-lg font-bold">MecaFlow</span>
        </Link>

        <div className="mt-6 rounded-2xl border bg-card p-6 shadow-sm md:p-8">
          <div className="flex items-center gap-3">
            {steps.map((s, i) => (
              <div key={s} className="flex flex-1 items-center gap-3">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                    i <= step ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                  }`}
                >
                  {i < step ? <Check className="h-4 w-4" /> : i + 1}
                </div>
                <span className={`text-sm ${i === step ? "font-medium" : "text-muted-foreground"}`}>{s}</span>
                {i < steps.length - 1 && <div className="h-px flex-1 bg-border" />}
              </div>
            ))}
          </div>

          <form onSubmit={next} className="mt-8 space-y-4">
            {step === 0 && (
              <>
                <h1 className="font-display text-xl font-bold">Conte sobre sua oficina</h1>
                <div className="space-y-2">
                  <Label htmlFor="nome">Nome da oficina</Label>
                  <Input
                    id="nome"
                    required
                    placeholder="Auto Center Silva"
                    value={workshopName}
                    onChange={(e) => setWorkshopName(e.target.value)}
                  />
                </div>
              </>
            )}

            {step === 1 && (
              <>
                <h1 className="font-display text-xl font-bold">Crie sua conta de administrador</h1>
                <div className="space-y-2">
                  <Label htmlFor="adm">Nome</Label>
                  <Input
                    id="adm"
                    required
                    placeholder="Seu nome"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ema">E-mail</Label>
                  <Input
                    id="ema"
                    type="email"
                    required
                    placeholder="voce@oficina.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sen">Senha</Label>
                  <Input
                    id="sen"
                    type="password"
                    required
                    minLength={8}
                    placeholder="Mínimo 8 caracteres"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
              </>
            )}

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
            )}

            <div className="flex items-center justify-between pt-4">
              {step > 0 ? (
                <Button type="button" variant="ghost" onClick={() => setStep(step - 1)}>
                  Voltar
                </Button>
              ) : (
                <Link to="/login" className="text-sm text-muted-foreground hover:underline">
                  Já tenho conta
                </Link>
              )}
              <Button type="submit" disabled={loading}>
                {step === steps.length - 1
                  ? loading ? "Cadastrando..." : "Concluir cadastro"
                  : "Continuar"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
