import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Send, Bot, Sparkles, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export const Route = createFileRoute("/app/assistente")({
  head: () => ({ meta: [{ title: "Meu Assistente — MecaFlow" }] }),
  component: Assistente,
});

type Papel = "assistant" | "user";
type Msg = { id: string; papel: Papel; texto: string; hora: string };

const agora = () =>
  new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

const BOAS_VINDAS: Msg = {
  id: "0",
  papel: "assistant",
  texto: "Olá! Sou o assistente da MecaFlow 👋 Tenho acesso aos dados da sua oficina em tempo real. Pode me perguntar sobre clientes, agendamentos, serviços mais realizados, conversas abertas e muito mais!",
  hora: agora(),
};

function Assistente() {
  const [msgs, setMsgs] = useState<Msg[]>([BOAS_VINDAS]);
  const [input, setInput] = useState("");
  const [carregando, setCarregando] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, carregando]);

  const enviar = async () => {
    const texto = input.trim();
    if (!texto || carregando) return;

    const msgUser: Msg = { id: String(Date.now()), papel: "user", texto, hora: agora() };
    setMsgs((prev) => [...prev, msgUser]);
    setInput("");
    setCarregando(true);

    try {
      // Monta histórico excluindo a mensagem de boas-vindas
      const history = msgs
        .filter((m) => m.id !== "0")
        .map((m) => ({ role: m.papel, content: m.texto }));

      const { response } = await api.post<{ response: string }>("/assistant/chat", {
        message: texto,
        history,
      });

      const msgBot: Msg = {
        id: String(Date.now() + 1),
        papel: "assistant",
        texto: response,
        hora: agora(),
      };
      setMsgs((prev) => [...prev, msgBot]);
    } catch {
      const msgErro: Msg = {
        id: String(Date.now() + 1),
        papel: "assistant",
        texto: "Desculpe, ocorreu um erro ao processar sua pergunta. Verifique se a chave da API está configurada no servidor.",
        hora: agora(),
      };
      setMsgs((prev) => [...prev, msgErro]);
    } finally {
      setCarregando(false);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 rounded-t-xl border border-b-0 bg-card px-5 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
          <Bot className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="font-semibold leading-tight">Meu Assistente</p>
          <p className="flex items-center gap-1 text-xs text-muted-foreground">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
            IA com dados em tempo real
          </p>
        </div>
        <Sparkles className="ml-auto h-4 w-4 text-muted-foreground/40" />
      </div>

      {/* Sugestões rápidas */}
      <div className="flex gap-2 flex-wrap border border-y-0 bg-card px-4 pb-3 pt-2">
        {[
          "Quantos clientes tenho?",
          "Agendamentos de hoje",
          "Serviço mais realizado",
          "Conversas abertas",
        ].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => { setInput(s); }}
            className="rounded-full border px-3 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Mensagens */}
      <div className="flex-1 overflow-y-auto border border-y-0 bg-muted/20 px-4 py-5 space-y-4">
        {msgs.map((m) => (
          <BubbleMensagem key={m.id} msg={m} />
        ))}

        {carregando && (
          <div className="flex items-end gap-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Bot className="h-3.5 w-3.5 text-primary" />
            </div>
            <div className="rounded-2xl rounded-bl-sm bg-card px-4 py-2.5 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:0ms]" />
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:150ms]" />
                <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 rounded-b-xl border border-t-0 bg-card px-4 py-3">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Pergunte sobre agendamentos, clientes, serviços..."
          className="flex-1"
          autoFocus
          disabled={carregando}
        />
        <Button size="icon" onClick={enviar} disabled={!input.trim() || carregando}>
          {carregando ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

function BubbleMensagem({ msg }: { msg: Msg }) {
  const isBot = msg.papel === "assistant";

  return (
    <div className={`flex items-end gap-2 ${isBot ? "" : "flex-row-reverse"}`}>
      {isBot && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <Bot className="h-3.5 w-3.5 text-primary" />
        </div>
      )}
      <div className={`flex max-w-[75%] flex-col gap-1 ${isBot ? "items-start" : "items-end"}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm shadow-sm whitespace-pre-wrap ${
            isBot
              ? "rounded-bl-sm bg-card text-card-foreground"
              : "rounded-br-sm bg-primary text-primary-foreground"
          }`}
        >
          {msg.texto}
        </div>
        <span className="text-[10px] text-muted-foreground px-1">{msg.hora}</span>
      </div>
    </div>
  );
}
