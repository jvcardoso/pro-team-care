# 🚀 Guia Rápido: Email Automático de Ativação

## 📖 Como Funciona Agora

Quando você cria uma assinatura para uma empresa, o sistema **automaticamente** envia um email de ativação para o cliente.

---

## 🎯 Cenários de Uso

### ✅ Cenário 1: Empresa COM Email Cadastrado (Recomendado)

**Passo a passo:**

1. **Cadastre a empresa** com pelo menos 1 email:
```
Nome: Hospital de Base
Email: contato@hospitaldebase.com.br
```

2. **Crie a assinatura** normalmente:
```
Empresa: Hospital de Base
Plano: Premium
Dia de cobrança: 10
```

3. **Sistema automaticamente**:
   - ✅ Busca email: `contato@hospitaldebase.com.br`
   - ✅ Envia email de ativação
   - ✅ Mostra notificação: "Email enviado"

4. **Cliente recebe email** e segue processo:
   - Aceita contrato
   - Cria usuário gestor
   - Empresa ativa!

---

### ✅ Cenário 2: Empresa SEM Email Cadastrado

**Passo a passo:**

1. **Cadastre a empresa** sem email:
```
Nome: Hospital de Base
(sem email cadastrado)
```

2. **Ao criar assinatura**, informe email manualmente:
```
Empresa: Hospital de Base
Plano: Premium
📧 Email do responsável: gestor@hospital.com.br
👤 Nome: Dr. João Silva
```

3. **Sistema envia** para o email informado

---

### ⚠️ Cenário 3: Não Enviar Agora (Exceção)

**Se quiser criar assinatura SEM enviar email:**

```
Ao criar assinatura:
☐ Desmarcar: "Enviar email de ativação"
```

Depois pode enviar manualmente:
1. Ir em "Empresas"
2. Clicar na empresa
3. Aba "Ativação"
4. Botão "Enviar Email de Ativação"

---

## 📝 Resumo

| Situação | O que fazer | Resultado |
|----------|-------------|-----------|
| ✅ **Empresa tem email** | Apenas criar assinatura | Email enviado automaticamente |
| ✅ **Empresa sem email** | Informar email ao criar assinatura | Email enviado para email informado |
| ⚠️ **Não enviar agora** | Desmarcar checkbox | Pode enviar depois manualmente |

---

## 🎉 Benefícios

- ✅ **Não precisa lembrar** de enviar email
- ✅ **Cliente notificado imediatamente**
- ✅ **Processo mais rápido**
- ✅ **Menos erros**

---

## ❓ FAQ

**P: E se eu esquecer de cadastrar email na empresa?**
R: Sem problemas! Ao criar a assinatura, você pode informar o email manualmente.

**P: Posso desabilitar o envio automático?**
R: Sim! Desmarque "Enviar email de ativação" ao criar assinatura.

**P: O que acontece se o email falhar?**
R: A assinatura é criada normalmente. Você recebe um aviso e pode reenviar depois.

**P: Posso enviar para mais de um email?**
R: Atualmente envia para 1 email. Para enviar para outros, use a aba "Ativação" depois.

**P: Como sei se o email foi enviado?**
R: Sistema mostra notificação "✅ Email enviado para X". Também fica registrado nos logs.

---

**Data**: 02/10/2025
**Versão**: 1.0
