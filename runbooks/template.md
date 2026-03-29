# Runbook: [Serviço] — Login e Validação

## URL
https://example.com/login

## Pré-condição
Usuário não está logado.

## Credenciais
- Email: `{{EMAIL}}`
- Senha: `{{PASSWORD}}`

## Passos

### 1. Login
1. Abrir `https://example.com/login`
2. Inserir email no campo `#email`
3. Inserir senha no campo `#password`
4. Clicar em `button[type="submit"]`
5. Esperar redirect para dashboard (máx 30s)

### 2. Validação
- Confirmar URL: `https://example.com/dashboard`
- Confirmar elemento `#user-profile` visível
- Screenshot: `evidence_post_login.png`

## Seletores úteis
```css
/* Input de email */
#email, input[name="email"], input[type="email"]

/* Input de senha */
#password, input[name="password"], input[type="password"]

/* Botão de submit */
button[type="submit"], input[type="submit"], .login-btn

/* Dashboard/logado */
.dashboard, #dashboard, [data-testid="dashboard"]
```

## Notas
- Timeout de login: 30s
- MFA: requer interação do usuário
- Se login falhar: capturar screenshot do erro e informar usuário
