# Autonomous Duel - Fuzzy Logic Edition

Um simulador de duelo autônomo que utiliza lógica fuzzy e árvores de comportamento para criar avatares inteligentes que lutam entre si, com um sistema emocional dinâmico que influencia suas ações.

![Apresentação](https://github.com/Msamuelsons/adaptive-system/blob/main/docs/apresentacao.gif?raw=true)

## Sobre o Projeto

Este projeto implementa um simulador de duelo autônomo entre dois avatares controlados por inteligência artificial. A IA é baseada em duas tecnologias principais:

1. **Árvores de Comportamento**: Controla a tomada de decisões dos avatares usando a biblioteca `py_trees`.
2. **Lógica Fuzzy**: Define o sistema de dano adaptativo através da biblioteca `skfuzzy`.

Os avatares possuem um sistema emocional complexo que influencia seu comportamento. À medida que um avatar sofre danos, sua raiva aumenta, podendo entrar em um "modo berserk" que aumenta seus ataques e velocidade de movimento.

## Características Principais

- **Sistema Emocional Dinâmico**: Avatares experimentam emoções como raiva e frustração
- **Modo Berserk**: Quando a raiva atinge um nível crítico, os avatares entram em frenesi
- **Lógica Fuzzy para Danos**: O dano causado é calculado por um sistema fuzzy que considera níveis de raiva e porcentagem de vida
- **Árvores de Comportamento**: Controle autônomo de decisões de aproximação e ataque
- **Animações Fluidas**: Animações para estados de movimento, ataque e idle
- **Interface Visual**: Exibição de barras de vida, níveis de raiva e status dos avatares

## Requisitos

- Python 3.7+
- Pygame
- py_trees
- NumPy
- scikit-fuzzy

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/autonomous-duel-fuzzy.git
cd autonomous-duel-fuzzy
```

2. Instale as dependências:
```
pip install pygame py_trees numpy scikit-fuzzy
```

3. Execute o jogo:
```
python main.py
```

## Estrutura de Arquivos

```
├── main.py                  # Arquivo principal do jogo
├── fuzzy_ai_controller.py   # Implementação da IA com árvores de comportamento
├── resources/               # Recursos gráficos e de áudio
│   └── sprites/             # Sprites para os avatares
│       ├── avatarA/         # Sprites do Avatar A
│       ├── avatarB/         # Sprites do Avatar B
│       └── background.png   # Imagem de fundo
```

## Como Funciona

### Sistema Fuzzy

O sistema usa lógica fuzzy para calcular o dano causado pelos avatares baseado em:

- **Raiva**: De 0 a 15, classificada como baixa, média, alta, ou berserk
- **Porcentagem de HP**: De 0 a 100, classificada como crítica, baixa, média, ou alta

As regras fuzzy combinam estes fatores para determinar um valor de dano que pode ser baixo, médio, alto ou crítico.

### Árvore de Comportamento

A árvore de comportamento controla as ações dos avatares com duas sequências principais:

1. **Sequência de Aproximação**: Se a distância for maior que o limiar, o avatar se aproxima
2. **Sequência de Ataque**: Se a distância for menor ou igual ao limiar, o avatar ataca

Em modo berserk, uma árvore modificada permite ataques mais agressivos e múltiplos.

### Sistema Emocional

O estado emocional dos avatares é influenciado por:

- Quantidade de HP restante
- Dano recente recebido
- Ataques consecutivos bem-sucedidos
- Falhas consecutivas ao atacar

## Jogabilidade

O jogo é totalmente autônomo - ambos os avatares são controlados pela IA e lutam até que um deles seja derrotado.

Quando o jogo termina:
- Pressione `R` para reiniciar o duelo
- Pressione `ESC` para sair do jogo

## Personalizações

É possível ajustar vários parâmetros do jogo:

- Limiares de distância de ataque
- Velocidade de movimento
- Parâmetros de raiva e modo berserk
- Funções de pertinência do sistema fuzzy

## Desenvolvimento Futuro

Ideias para expansão:
- Adicionar mais avatares com comportamentos distintos
- Implementar um sistema de evolução genética para melhorar as IAs
- Adicionar elementos de ambiente interativos
- Criar um modo para controle manual pelo jogador

## Atribuições

Os sprites utilizados no projeto foram obtidos de fontes gratuitas ou de uso livre para fins educacionais.

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
