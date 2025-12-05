# Simulação de Topologia de Rede em Árvore/Hierárquica (XProbe/RTT)

Este projeto implementa uma simulação da topologia de rede em árvore hierárquica, utilizando a biblioteca NetworkX em Python. O objetivo principal é demonstrar o endereçamento IP hierárquico, exibir as tabelas de roteamento e simular o comportamento de medição de latência (RTT) de um protocolo como o XProbe.

## 🛠️ Requisitos

Para rodar o simulador, você precisa ter o Python 3 instalado, juntamente com as seguintes bibliotecas:

- networkx: Para modelar a estrutura da rede como um grafo.

- matplotlib: Para visualizar graficamente a topologia da rede.

Abra seu terminal ou prompt de comando e execute:

```Bash

pip install networkx matplotlib
```

## Como Executar

Execute o arquivo via terminal:

```Bash

python simulador_redeV2.py

```

O programa iniciará o Menu Interativo no terminal e exibirá a topologia da rede em uma janela gráfica.

## 🗺️ Topologia Implementada

A simulação cria a estrutura de rede em árvore com os seguintes componentes hierárquicos:

Core (Raiz): root

Aggregation: a1 e a2

Edge/Borda: e1, e2, e3, e4

Hosts (Folhas): H1x, H2x, H3x, H4x (número de hosts gerado aleatoriamente)

Endereçamento IP
O sistema atribui endereços IP baseados em sub-redes (CIDR) para demonstrar o roteamento hierárquico:

Sub-rede 1 (e1): 192.168.1.0/27 (Hosts: H1x)

Sub-rede 2 (e2): 192.168.1.32/27 (Hosts: H2x)

Sub-rede 3 (e3): 192.168.1.64/28 (Hosts: H3x)

Sub-rede 4 (e4): 192.168.1.80/28 (Hosts: H4x)

## 🔑 Funcionalidades do Simulador

O menu interativo oferece as seguintes opções para atender aos requisitos do projeto:

1. Visualizar Topologia
   Exibe o diagrama de rede (grafo) na janela do matplotlib .

2. Exibir Tabelas de Roteamento (Fase 2, Item 2)
   Apresenta no console as tabelas de roteamento para os nós que atuam como roteadores (root, a1, a2). Essas tabelas demonstram como o roteamento é feito para as sub-redes definidas.

3. Simulação XProbe/RTT (Fase 2, Quadro 1)
   Esta função simula o processo de medição de latência (RTT), conforme exigido pelo protocolo XProbe, entre quaisquer dois hosts da rede.

Processo:

Solicita o host de Origem e Destino (e.g., H11 e H41).

Simula o envio e recebimento de 3 amostras de pacotes.

Calcula o RTT (Round Trip Time) para cada amostra com base no número de saltos no caminho mais curto, adicionando uma variação para simulação de atraso.

Exibe as Estatísticas do XProbe, incluindo o RTT MÉDIO, que é o resultado final solicitado no Quadro 1.

Exemplo de Saída (RTT):

**_ RTT MÉDIO (3 Amostras): 0.5478 ms _**
