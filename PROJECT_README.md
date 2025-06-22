# 🎯 Distributed TSP Solver System

A production-ready distributed system for solving the Traveling Salesman Problem (TSP) using Python. This system implements advanced distributed computing concepts including fault tolerance, leader election, and load balancing.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Demo
```bash
python run_demo.py
```

This will start a coordinator, 3 workers, and solve a sample TSP problem automatically.

## 📁 Project Structure

```
distributed-tsp/
├── src/                    # Source code
│   ├── common/            # Shared utilities
│   ├── coordinator/       # Coordinator implementation
│   ├── worker/           # Worker implementation
│   ├── client/           # Client implementation
│   └── algorithms/       # TSP algorithms and task distribution
├── scripts/              # Startup scripts
├── config/               # Configuration files
├── examples/             # Example problems
├── requirements.txt      # Python dependencies
└── run_demo.py          # Demo script
```

## 🏗️ Architecture

The system consists of three main components:

### 🎯 Coordinator
- Manages worker registration and heartbeats
- Distributes TSP tasks to available workers
- Consolidates results and finds optimal solution
- Handles fault tolerance and worker failures

### ⚙️ Worker
- Connects to coordinator and registers for tasks
- Solves assigned TSP subtasks using brute force
- Reports results back to coordinator
- Maintains heartbeat with coordinator

### 💻 Client
- Submits TSP problems to coordinator
- Generates random TSP problems for testing
- Displays solutions and execution statistics
- Supports benchmark testing

## 🚀 Usage

### Starting Components Manually

#### 1. Start Coordinator
```bash
python scripts/start_coordinator.py --host localhost --port 8888
```

#### 2. Start Workers
```bash
# Terminal 2
python scripts/start_worker.py --host localhost --port 8888

# Terminal 3
python scripts/start_worker.py --host localhost --port 8888
```

#### 3. Generate and Solve Problems

Generate a random problem:
```bash
python scripts/start_client.py generate --cities 6 --seed 42 --output problem.json
```

Solve the problem:
```bash
python scripts/start_client.py solve --file problem.json --output result.json
```

Run benchmarks:
```bash
python scripts/start_client.py benchmark --output-dir results/
```

## 📊 Example Output

```
🎯 TSP SOLUTION FOUND
============================================================
💰 Best Cost: 234.56
🛤️  Best Path: City_1 → City_3 → City_2 → City_4 → City_1
👷 Found by: WORKER_A1B2C3D4
👥 Workers used: 3
📋 Total tasks: 6
⏱️  Total time: 2.34 seconds
============================================================
```

## 🔧 Configuration

Edit `config/default_config.py` to modify system settings:

```python
DEFAULT_CONFIG = {
    'coordinator': {
        'host': 'localhost',
        'port': 8888,
        'max_workers': 10
    },
    'worker': {
        'coordinator_host': 'localhost',
        'coordinator_port': 8888,
        'heartbeat_interval': 5
    },
    'timeouts': {
        'connection': 10,
        'heartbeat': 15,
        'task_completion': 60
    }
}
```

## 🧪 Testing

The system includes several ways to test functionality:

### 1. Use Sample Problem
```bash
python scripts/start_client.py solve --file examples/sample_problem.json
```

### 2. Generate Custom Problems
```bash
# Generate 8-city problem
python scripts/start_client.py generate --cities 8 --seed 123 --output my_problem.json
```

### 3. Run Benchmarks
```bash
python scripts/start_client.py benchmark --output-dir benchmark_results/
```

## 🛡️ Features

### Core Functionality
- ✅ Distributed TSP solving with optimal task distribution
- ✅ Dynamic worker registration and management
- ✅ Real-time result consolidation
- ✅ Scalable architecture supporting multiple workers

### Fault Tolerance
- ✅ Worker failure detection and task reassignment
- ✅ Heartbeat monitoring system
- ✅ Graceful shutdown and cleanup
- ✅ Connection timeout handling

### Performance
- ✅ Intelligent task distribution based on problem size
- ✅ Load balancing across available workers
- ✅ Parallel processing of TSP permutations
- ✅ Efficient communication protocol

## 📈 Performance

The system's performance scales with the number of workers:

| Cities | Workers | Time (approx) |
|--------|---------|---------------|
| 4      | 1       | < 1 second    |
| 6      | 2       | 2-3 seconds   |
| 8      | 3       | 10-30 seconds |
| 10     | 4       | 1-5 minutes   |

*Note: Times vary based on hardware and exact problem complexity*

## 🔍 Troubleshooting

### Common Issues

#### "Connection refused"
- Ensure coordinator is started before workers
- Check host/port configuration
- Verify firewall settings

#### "No workers available"
- Start at least one worker before submitting problems
- Check worker logs for connection errors
- Verify coordinator is accepting connections

#### "Timeout waiting for result"
- Increase timeout with `--timeout <seconds>`
- Ensure sufficient workers for problem size
- Check worker logs for processing errors

### Debug Mode
Add `--debug` flag to any component for verbose logging:
```bash
python scripts/start_coordinator.py --debug
python scripts/start_worker.py --debug
```

## 🛠️ Development

### Adding New Features

1. **New algorithms**: Add to `src/algorithms/`
2. **Communication protocols**: Extend `src/common/message_types.py`
3. **Client commands**: Add to `scripts/start_client.py`

### Code Structure
- All components inherit from base communication classes
- Message-driven architecture with registered handlers
- Thread-safe operations with proper locking
- Comprehensive error handling and logging

## 📚 Implementation Details

### Task Distribution
The system uses different strategies based on problem size:
- **Small problems (≤8 cities)**: Direct permutation division
- **Medium problems (9-12 cities)**: Fixed-prefix distribution
- **Large problems (>12 cities)**: Heuristic-based regions

### Communication Protocol
- TCP sockets with JSON message serialization
- Message length prefixes for reliable transmission
- Heartbeat system for connection monitoring
- Graceful connection handling and cleanup

### TSP Algorithm
- Brute force enumeration for guaranteed optimal solutions
- Parallel processing of permutation subsets
- Early termination capabilities
- Memory-efficient permutation generation

## 🤝 Contributing

This is an educational project demonstrating distributed systems concepts. Feel free to extend it with:

- Advanced TSP algorithms (genetic algorithms, simulated annealing)
- Web-based monitoring dashboard
- Database persistence for problems and results
- Docker containerization
- Kubernetes deployment manifests

## 📄 License

This project is provided for educational purposes. Use and modify freely for learning and research.

---

**Built with ❤️ as a comprehensive distributed systems example** 