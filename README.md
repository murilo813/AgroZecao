# Projeto Zecão
Este projeto tem como objetivo fornecer uma plataforma completa para a Agropecuária Zecão, integrando diversas áreas da empresa com um sistema baseado em web e mobile. A plataforma inclui módulos de Financeiro, Gerência, Estoque e Controle de Gastos (tendo mais futuramente), cada um atendendo às necessidades específicas de cada funcionário e usuário.


## Funcionalidades

• **Financeiro**: Área dedicada à gestão de finanças da empresa, permitindo o usuário ver as notas, cheques, e outros dados do cliente e seus relacionados, cadastrar informações sobre notas específicas, atendimentos, informações do cliente, informações sobre pagamentos ditas pelo  cliente, etc, tendo a funcionalidade de agendar lembretes que aparecerão como notificação para o usuário que a fez.

• **Gerência**: Um painel para gerentes, com funcionalidades como enviar notificações/mensagens para outros usuários da respectiva loja, acessar dados do estoque, analisar informações gerais da empresa, fazer e  gerenciar orçamentos.

• **Estoque**: Controle do estoque de produtos, com dados dinâmicos carregados de um banco de dados PostgreSQL. Inclui diferentes lojas e dados de cada uma delas. Os usuários usarão pra realizar contagem de estoques, cadastrar informações como produtos com estoque furado, ao responsável do estoque o gerencimanto de contagens de seus colegas, etc. Com gamificação dando pontos por contagens, etc (futuro).

• **Controle de Gastos**: Monitoramento de despesas e investimentos da empresa, com relatórios permitindo também o cadastro de novos gastos sejam quais for. Com a implementação de um app futuro para os funcionários que são responsáveis por veículos da empresa cadastrarem abastecimentos e receberrem notificações de manutenção do carro ou mensagens dos gerentes ou da respónsável pelo controle de gastos.

• **Aplicativo para Vendedores**: Um app inicial desenvolvido para vendedores que pode escalar para um sistema mais robusto, semelhante a um CRM. Atualmente funciona para visualizar o estoque e preço de produtos, mas que irá escalar para controle de gastos, criador da DAVs direto para o sistema da empresa, e por fim uma espécie de CRM.


## Tecnologias Utilizadas

• **Backend**: Flask (Python)

• **Banco de Dados**: PostgreSQL

• **Frontend Web**: HTML, CSS, JavaScript

• **Mobile**: Flutter (para o app)

• **Integração de Dados**: Pentaho Spoon e Apache Hop para a transferência de dados entre o sistema ERP da empresa e o banco de dados do site


## Funcionalidades do Sistema

• **Integração com ERP**: Os dados do sistema ERP da empresa são integrados ao banco de dados do site, usando Pentaho Spoon para facilitar a transferência.

• **Painel para cada funcionário**: O sistema é dividido por áreas específicas para que cada funcionário tenha acesso apenas às informações relevantes para o seu trabalho.

• **Modais de Notificação e Cobrança**: O sistema conta com modais interativos que trazem notificações, cobranças agendadas, etc, proporcionando uma experiência mais dinâmica.

• **Controle de Estoque**: O estoque de produtos é atualizado e gerido diretamente pelo sistema, com dados que podem ser consultados por diferentes lojas, permitindo a criação de relatórios com filtros para contagem e conferência de estoque. Gerenciamento de contagens, cadastramento de furos de estoque e futura gamificação pra contagens.

• **CRM para Vendedores**: Inicialmente voltado para os vendedores, o aplicativo permitirá o gerenciamento de clientes e vendas, controle de gastos, lembretes, lançamento de DAVs, etc, com planos para expansão para um CRM mais robusto.


## Como Funciona

• **Cadastro e Login**: O sistema permite que funcionários e gerentes se cadastrem e façam login para acessar suas respectivas áreas.

• **Visão Personalizada**: Dependendo do cargo do usuário (financeiro, gerência, estoque), ele terá acesso a funcionalidades e dados específicos.

• **Integração e Sincronização**: Os dados entre o sistema ERP e o banco de dados do site são sincronizados de forma automática, garantindo que as informações estejam sempre atualizadas.

• **App Móvel**: O aplicativo para vendedores oferece uma interface simples para gerenciar clientes e vendas, com a possibilidade de escalar para um CRM completo no futuro.
