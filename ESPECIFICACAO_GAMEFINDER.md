## Paleta de Cores Recomendada (Foco em Roxo)

- **Fundo principal:** #181A20 (preto azulado, escuro, elegante)
- **Cards/Blocos:** #23263A (cinza-azulado escuro, para separar seções)
- **Roxo principal:** #7C3AED (roxo vibrante, para botões, links, destaques)
- **Roxo claro (hover/destaque):** #A78BFA (para efeitos de hover, gradientes, detalhes)
- **Secundário (detalhes):** #00C9A7 (verde água, para pequenos destaques e contraste)
- **Texto principal:** #F5F6FA (quase branco, ótima leitura em fundo escuro)
- **Texto secundário:** #A0A3B1 (cinza claro, para descrições e infos menos importantes)
- **Atenção/erro:** #FF5F5F (vermelho suave, para alertas)
- **Favorito/estrela:** #FFD700 (amarelo ouro, para ícones de favoritos/avaliação)

### Gradiente sugerido

- `background: linear-gradient(90deg, #7C3AED 0%, #A78BFA 100%);`

Essa paleta é moderna, acessível, fácil de aplicar e transmite bem a proposta gamer/tecnológica do GameFinder.
# GameFinder – Especificação de Módulos e Funcionalidades

## 1. ETL/Data Pipeline
- Unificação, limpeza e enriquecimento dos dados de jogos e avaliações (incluindo comentários, links, tags/gêneros para humor)
- Extração de tags/gêneros para mapeamento de humor
- Scripts para atualização incremental e monitoramento de qualidade (futuro)

## 2. Serviço de Recomendação
- API de recomendações híbridas (por usuário, por jogo)
- Recomendações baseadas em humor (relaxar, desafiar, socializar, nostalgia, explorar)
- Randomização/diversidade nas recomendações
- Endpoints de debug e validação
- Recomendações para cold start (usuário novo ou sem avaliações)
- Recomendações de jogos "esquecidos" (pouco avaliados)
- Suporte a filtros avançados (gênero, plataforma, nota, etc)
- (Futuro) Feedback do usuário e atualização incremental dos modelos

## 3. Backend API (Laravel)
- **Autenticação:** registro, login, logout, perfil
- **Usuários:** dados do usuário, favoritos, avaliações, conquistas, feed de atividades
- **Jogos:** apenas leitura (listar, buscar, detalhes), incluindo:
  - Média de avaliação
  - Número de avaliações
  - Comentários dos usuários
  - Link para o jogo (Steam, Amazon, etc)
- **Avaliações:** criar, listar, remover avaliações de jogos (com nota e comentário)
- **Favoritos:** favoritar/desfavoritar jogos, listar favoritos do usuário
- **Recomendações:** integração com serviço Python (por usuário, por jogo, por humor)
- **Descubra Novos Jogos:** listas temáticas, filtros, “Surpreenda-me”
- **Conquistas/Badges:** desbloqueio e exibição de conquistas
- **Feed de Atividades:** histórico de ações do próprio usuário
- **Recomendações de Comunidade:** listas públicas criadas por usuários, votação/curtida
- **Filtros Avançados e Busca Inteligente:** busca por múltiplos critérios, autocomplete
- **Gamificação do Onboarding:** progresso e incentivos para completar perfil e primeiras ações
- **Sugestão de Jogos “Esquecidos”:** recomendar jogos com poucas avaliações
- **Administração:** (opcional) gerenciar usuários e avaliações

## 4. Frontend (React)
- **Landing Page:** apresentação da plataforma, listagem/carrossel de jogos em destaque, como funciona, benefícios
- **Autenticação:** telas de login, registro, logout
- **Home/Listagem de Jogos:** lista, busca, filtros avançados
- **Detalhe do Jogo:** informações, avaliações, favoritar, link para loja
- **Perfil do Usuário:** dados, favoritos, conquistas, histórico de avaliações, recomendações personalizadas, feed de atividades
- **Avaliação:** formulário para avaliar jogos (nota e comentário)
- **Favoritos:** página/lista de favoritos
- **Descubra Novos Jogos:** tela/aba de descoberta, carrosséis, filtros, “Surpreenda-me”
- **Recomendações por Humor:** tela/modal para escolher humor e receber sugestões temáticas
- **Conquistas/Badges:** exibição de badges e notificações ao desbloquear
- **Recomendações de Comunidade:** explorar, criar e votar em listas públicas
- **Gamificação do Onboarding:** barra de progresso, dicas, badges de onboarding
- **Sugestão de Jogos “Esquecidos”:** seção para incentivar avaliações em jogos pouco explorados
- **Administração:** (opcional) telas para gerenciar usuários/avaliações


## 5. Infraestrutura/DevOps
- Configuração de ambiente (.env)
- Dockerização (obrigatório para desenvolvimento e deploy)
  - Dockerfile para cada serviço (backend, recommender-service, frontend)
  - docker-compose.yml para orquestrar todos os serviços e banco de dados
- Documentação (README, SETUP)

---

**Observações:**
- Não haverá CRUD de jogos (dados vêm do ETL/datasets)
- Cold start tratado via onboarding e recomendações por preferências iniciais
- Acessibilidade não será prioridade neste momento
- Design moderno, com dark mode, carrosséis, cards e microinterações
- Funcionalidades extras: conquistas, feed de atividades, recomendações de comunidade, filtros avançados, gamificação do onboarding, sugestões de jogos esquecidos, recomendações por humor
