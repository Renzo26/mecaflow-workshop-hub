import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Plus, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/agenda")({
  head: () => ({ meta: [{ title: "Agenda — MecaFlow" }] }),
  component: Agenda,
});

type Evento = { id: string; data: string; hora: string; titulo: string; cliente: string };

const HOJE = new Date();
const fmt = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
};
const DIAS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

function Agenda() {
  const [ref, setRef] = useState(new Date(HOJE.getFullYear(), HOJE.getMonth(), 1));
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [diaSel, setDiaSel] = useState<string>(fmt(HOJE));

  useEffect(() => {
    api.get<Evento[]>("/appointments")
      .then(setEventos)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const dias = useMemo(() => {
    const inicio = new Date(ref.getFullYear(), ref.getMonth(), 1);
    const fim = new Date(ref.getFullYear(), ref.getMonth() + 1, 0);
    const cells: (Date | null)[] = [];
    for (let i = 0; i < inicio.getDay(); i++) cells.push(null);
    for (let d = 1; d <= fim.getDate(); d++) cells.push(new Date(ref.getFullYear(), ref.getMonth(), d));
    while (cells.length % 7 !== 0) cells.push(null);
    return cells;
  }, [ref]);

  const mesAno = ref.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
  const evDia = (d: string) => eventos.filter((e) => e.data === d).sort((a, b) => a.hora.localeCompare(b.hora));

  const criar = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const novo = await api.post<Evento>("/appointments", {
        data: String(f.get("data")),
        hora: String(f.get("hora")),
        titulo: String(f.get("titulo")),
        cliente: String(f.get("cliente")),
      });
      setEventos((arr) => [...arr, novo]);
      setOpen(false);
    } catch { /* ignora */ } finally {
      setSaving(false);
    }
  };

  const deletar = async (id: string) => {
    await api.delete(`/appointments/${id}`).catch(() => {});
    setEventos((arr) => arr.filter((e) => e.id !== id));
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Agenda</h1>
          <p className="text-sm text-muted-foreground">Visualize e gerencie agendamentos.</p>
        </div>
        <Button onClick={() => setOpen(true)}><Plus className="mr-1 h-4 w-4" /> Novo agendamento</Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <div className="rounded-xl border bg-card">
            <div className="flex items-center justify-between border-b p-4">
              <h2 className="font-display text-lg font-semibold capitalize">{mesAno}</h2>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" onClick={() => setRef(new Date(ref.getFullYear(), ref.getMonth() - 1, 1))}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={() => setRef(new Date(HOJE.getFullYear(), HOJE.getMonth(), 1))}>Hoje</Button>
                <Button variant="ghost" size="icon" onClick={() => setRef(new Date(ref.getFullYear(), ref.getMonth() + 1, 1))}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-7 border-b text-center text-xs font-medium text-muted-foreground">
              {DIAS.map((d) => <div key={d} className="py-2">{d}</div>)}
            </div>
            <div className="grid grid-cols-7">
              {dias.map((d, i) => {
                if (!d) return <div key={i} className="h-24 border-b border-r bg-muted/20" />;
                const k = fmt(d);
                const evs = evDia(k);
                const isHoje = k === fmt(HOJE);
                const isSel = k === diaSel;
                return (
                  <button
                    key={i}
                    onClick={() => setDiaSel(k)}
                    className={`h-24 border-b border-r p-1.5 text-left transition hover:bg-muted/40 ${
                      isSel ? "bg-primary/5 ring-1 ring-inset ring-primary/30" : ""
                    }`}
                  >
                    <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                      isHoje ? "bg-primary text-primary-foreground font-semibold" : ""
                    }`}>{d.getDate()}</span>
                    <div className="mt-1 space-y-0.5">
                      {evs.slice(0, 2).map((e) => (
                        <div key={e.id} className="truncate rounded bg-primary/15 px-1 text-[10px] text-primary">
                          {e.hora} {e.titulo}
                        </div>
                      ))}
                      {evs.length > 2 && <div className="text-[10px] text-muted-foreground">+{evs.length - 2}</div>}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-xl border bg-card p-4">
            <h3 className="font-display font-semibold">
              {new Date(diaSel + "T00:00:00").toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
            </h3>
            <div className="mt-4 space-y-2">
              {evDia(diaSel).length === 0 && <p className="text-sm text-muted-foreground">Sem agendamentos.</p>}
              {evDia(diaSel).map((e) => (
                <div key={e.id} className="flex gap-3 rounded-lg border p-3">
                  <div className="flex h-12 w-14 flex-col items-center justify-center rounded-md bg-primary/10 text-primary">
                    <span className="text-sm font-bold">{e.hora}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{e.titulo}</p>
                    <p className="text-sm text-muted-foreground">{e.cliente}</p>
                  </div>
                  <Button variant="ghost" size="icon" className="shrink-0 self-start" onClick={() => deletar(e.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Novo agendamento</DialogTitle></DialogHeader>
          <form onSubmit={criar} className="space-y-3">
            <div className="space-y-2"><Label>Cliente</Label><Input name="cliente" required /></div>
            <div className="space-y-2"><Label>Serviço</Label><Input name="titulo" required /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Data</Label><Input name="data" type="date" required defaultValue={diaSel} /></div>
              <div className="space-y-2"><Label>Hora</Label><Input name="hora" type="time" required /></div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Criar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
