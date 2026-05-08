import { createFileRoute } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/app/configuracoes/conhecimento")({
  head: () => ({ meta: [{ title: "Minha oficina — MecaFlow" }] }),
  component: Conhecimento,
});

function Conhecimento() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold">Minha oficina</h1>
        <p className="text-sm text-muted-foreground">Informações da oficina usadas pelo bot e pela equipe.</p>
      </div>

      <form className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-base">Identificação</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2"><Label>Nome da oficina</Label><Input defaultValue="Auto Center Silva" /></div>
            <div className="space-y-2"><Label>CNPJ</Label><Input defaultValue="00.000.000/0000-00" /></div>
            <div className="space-y-2"><Label>Telefone</Label><Input defaultValue="(11) 99999-0000" /></div>
            <div className="space-y-2"><Label>E-mail</Label><Input type="email" defaultValue="contato@oficina.com" /></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Endereço</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2"><Label>Endereço</Label><Input defaultValue="Av. Brasil, 1000" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Cidade</Label><Input defaultValue="São Paulo" /></div>
              <div className="space-y-2"><Label>UF</Label><Input defaultValue="SP" /></div>
            </div>
            <div className="space-y-2"><Label>CEP</Label><Input defaultValue="01000-000" /></div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="text-base">Funcionamento e serviços</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label>Horário de funcionamento</Label>
              <Input defaultValue="Seg–Sex 08h–18h, Sáb 08h–12h" />
            </div>
            <div className="space-y-2">
              <Label>Serviços oferecidos</Label>
              <Textarea rows={4} defaultValue="Troca de óleo, alinhamento, balanceamento, revisão completa, freios, suspensão." />
            </div>
            <div className="space-y-2">
              <Label>Informações adicionais para o bot</Label>
              <Textarea rows={4} placeholder="Formas de pagamento, garantias, política de cancelamento..." />
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 flex justify-end">
          <Button type="submit">Salvar alterações</Button>
        </div>
      </form>
    </div>
  );
}
