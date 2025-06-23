#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from client.client import TSPClient
from client.problem_generator import TSPProblemGenerator


def solve_command(args):
    """Executa comando solve"""
    try:
        # Carrega problema
        problem = TSPProblemGenerator.load_problem_from_file(args.file)

        print(f"Loaded TSP problem with {len(problem['cities'])} cities")
        print(f"Cities: {', '.join(problem['cities'])}")

        # Cria cliente e resolve
        client = TSPClient(args.host, args.port)
        start_time = time.time()

        result = client.solve_tsp_problem(
            problem["distance_matrix"], problem["cities"], args.timeout
        )

        end_time = time.time()
        total_time = end_time - start_time

        if result:
            display_result(result, total_time)

            # Salva resultado se especificado
            if args.output:
                save_result(result, args.output, total_time)
        else:
            print("❌ Failed to solve TSP problem")

    except Exception as e:
        print(f"❌ Error: {e}")


def generate_command(args):
    """Executa comando generate"""
    try:
        problem = TSPProblemGenerator.generate_random_problem(args.cities, args.seed)
        TSPProblemGenerator.save_problem_to_file(problem, args.output)

        print(f"✅ Generated TSP problem with {args.cities} cities")
        print(f"Saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error generating problem: {e}")


def benchmark_command(args):
    """Executa comando benchmark"""
    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)

        problems = TSPProblemGenerator.create_benchmark_problems()
        client = TSPClient(args.host, args.port)

        results = {}

        for name, problem in problems.items():
            print(f"\n🔄 Running benchmark: {name} ({len(problem['cities'])} cities)")

            start_time = time.time()
            result = client.solve_tsp_problem(
                problem["distance_matrix"], problem["cities"], args.timeout
            )
            end_time = time.time()

            if result:
                total_time = end_time - start_time
                results[name] = {
                    "problem": problem,
                    "result": result,
                    "total_time": total_time,
                }

                print(
                    f"✅ {name}: Cost = {result['best_solution']['best_cost']:.2f}, Time = {total_time:.2f}s"
                )

                # Salva resultado individual
                result_file = output_dir / f"benchmark_{name}.json"
                save_result(result, result_file, total_time)
            else:
                print(f"❌ {name}: Failed")

        # Salva resumo dos benchmarks
        summary_file = output_dir / "benchmark_summary.json"
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Benchmark completed. Results saved to {output_dir}")

    except Exception as e:
        print(f"❌ Benchmark error: {e}")


def display_result(result, total_time):
    """Exibe resultado na tela"""
    print("\n" + "=" * 60)
    print("🎯 TSP SOLUTION FOUND")
    print("=" * 60)

    if "best_solution" in result:
        solution = result["best_solution"]

        print(f"💰 Best Cost: {solution['best_cost']:.2f}")
        print(f"🛤️  Best Path: {' → '.join(solution['best_path'])}")
        print(f"👷 Found by: {solution.get('found_by', 'unknown')}")

    if "execution_stats" in result:
        stats = result["execution_stats"]
        print(f"👥 Workers used: {stats['active_workers']}")
        print(f"📋 Total tasks: {result.get('total_tasks', 0)}")

    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print("=" * 60)


def save_result(result, output_file, total_time):
    """Salva resultado em arquivo"""
    output_data = {"result": result, "total_time": total_time, "timestamp": time.time()}

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"📁 Result saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="TSP Distributed Client")
    parser.add_argument("--host", default="localhost", help="Coordinator host")
    parser.add_argument("--port", type=int, default=8888, help="Coordinator port")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Comando solve
    solve_parser = subparsers.add_parser("solve", help="Solve TSP problem")
    solve_parser.add_argument(
        "--file", required=True, help="JSON file with TSP problem"
    )
    solve_parser.add_argument("--output", help="Output file for result")

    # Comando generate
    gen_parser = subparsers.add_parser("generate", help="Generate random TSP problem")
    gen_parser.add_argument(
        "--cities", type=int, required=True, help="Number of cities"
    )
    gen_parser.add_argument("--seed", type=int, help="Random seed")
    gen_parser.add_argument("--output", required=True, help="Output JSON file")

    # Comando benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmark tests")
    bench_parser.add_argument(
        "--output-dir",
        default="benchmark_results",
        help="Directory for benchmark results",
    )

    args = parser.parse_args()

    if args.command == "solve":
        solve_command(args)
    elif args.command == "generate":
        generate_command(args)
    elif args.command == "benchmark":
        benchmark_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
