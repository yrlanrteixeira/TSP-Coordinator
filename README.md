# TSP Distribuído

Sistema distribuído para resolução do Problema do Caixeiro Viajante (TSP) usando arquitetura cliente-servidor com múltiplos workers.

## Estrutura do Projeto

```
tsp-distribuido/
├── src/
│   ├── common/          # Utilitários e tipos compartilhados
│   ├── coordinator/     # Coordenador (líder)
│   ├── worker/          # Trabalhadores
│   ├── client/          # Cliente
│   └── algorithms/      # Algoritmos TSP e distribuição
├── tests/               # Testes
├── scripts/             # Scripts de inicialização
├── config/              # Configurações
├── requirements.txt     # Dependências
└── README.md           # Este arquivo
```

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar Coordenador

```bash
python scripts/start_coordinator.py
```

### Iniciar Worker

```bash
python scripts/start_worker.py
```

### Iniciar Cliente

```bash
python scripts/start_client.py
```
