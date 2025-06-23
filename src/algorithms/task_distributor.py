import itertools
import math
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TaskChunk:
    """Representa um pedaço de trabalho para um worker"""

    task_id: str
    distance_matrix: List[List[float]]
    cities: List[str]
    start_permutations: List[List[int]]
    end_permutations: List[List[int]]
    estimated_work_size: int


class TaskDistributor:
    """Distribui tarefas TSP de forma balanceada entre workers"""

    def __init__(self):
        self.logger = None

    def distribute_tsp_tasks(
        self, distance_matrix: List[List[float]], cities: List[str], num_workers: int
    ) -> List[Dict[str, Any]]:
        """
        Divide problema TSP em subtarefas para workers

        Args:
            distance_matrix: Matriz de distâncias
            cities: Lista de cidades
            num_workers: Número de workers disponíveis

        Returns:
            Lista de tarefas distribuídas
        """
        print(
            f"[DEBUG] distribute_tsp_tasks called with {len(cities)} cities and {num_workers} workers"
        )
        n_cities = len(cities)

        # Calcula total de permutações
        total_permutations = math.factorial(n_cities)

        # Escolhe estratégia baseada no tamanho do problema
        if n_cities <= 8:
            result = self._distribute_small_problem(
                distance_matrix, cities, num_workers
            )
        elif n_cities <= 12:
            result = self._distribute_medium_problem(
                distance_matrix, cities, num_workers
            )
        else:
            result = self._distribute_large_problem(
                distance_matrix, cities, num_workers
            )
        print(f"[DEBUG] distribute_tsp_tasks returning {len(result)} tasks")
        return result

    def _distribute_small_problem(
        self, distance_matrix: List[List[float]], cities: List[str], num_workers: int
    ) -> List[Dict[str, Any]]:
        """
        Distribui problema pequeno (≤8 cidades) usando permutações completas
        """
        n_cities = len(cities)

        # Para TSP, fixamos a primeira cidade para reduzir permutações equivalentes
        # Isso reduz de n! para (n-1)! permutações únicas
        total_perms = math.factorial(n_cities - 1)

        # Calcula quantas permutações cada worker deve processar
        perms_per_worker = max(1, total_perms // num_workers)

        # Certifica que todos os workers recebam trabalho
        actual_workers = min(num_workers, total_perms)

        tasks = []
        for i in range(actual_workers):
            start_idx = i * perms_per_worker
            end_idx = min((i + 1) * perms_per_worker, total_perms)

            # Se é o último worker, pega todas as permutações restantes
            if i == actual_workers - 1:
                end_idx = total_perms

            # Cria tarefa simples com range de índices
            task = {
                "distance_matrix": distance_matrix,
                "cities": cities,
                "start_permutation_index": start_idx,
                "end_permutation_index": end_idx,
                "estimated_work_size": end_idx - start_idx,
                "task_type": "index_range",
                "fixed_first_city": 0,
            }

            tasks.append(task)

        return tasks

    def _distribute_medium_problem(
        self, distance_matrix: List[List[float]], cities: List[str], num_workers: int
    ) -> List[Dict[str, Any]]:
        """
        Distribui problema médio (9-12 cidades) usando divisão por primeiros elementos
        """
        n_cities = len(cities)

        # Fixa primeira cidade e distribui baseado na segunda cidade
        first_city = 0
        remaining_cities = list(range(1, n_cities))

        # Divide cidades restantes entre workers
        cities_per_worker = max(1, len(remaining_cities) // num_workers)

        tasks = []
        for i in range(num_workers):
            start_idx = i * cities_per_worker
            end_idx = min((i + 1) * cities_per_worker, len(remaining_cities))

            if start_idx >= len(remaining_cities):
                break

            # Se é o último worker, pega todas as cidades restantes
            if i == num_workers - 1:
                end_idx = len(remaining_cities)

            worker_second_cities = remaining_cities[start_idx:end_idx]

            # Estima tamanho do trabalho
            remaining_positions = n_cities - 2  # Primeira e segunda fixas
            work_size = len(worker_second_cities) * math.factorial(remaining_positions)

            task = {
                "distance_matrix": distance_matrix,
                "cities": cities,
                "fixed_first_city": first_city,
                "assigned_second_cities": worker_second_cities,
                "estimated_work_size": work_size,
            }

            tasks.append(task)

        return tasks

    def _distribute_large_problem(
        self, distance_matrix: List[List[float]], cities: List[str], num_workers: int
    ) -> List[Dict[str, Any]]:
        """
        Distribui problema grande (>12 cidades) usando heurística
        """
        # Para problemas grandes, usa aproximação heurística
        # Cada worker recebe uma região do espaço de busca

        n_cities = len(cities)

        # Cria sub-regiões baseadas em permutações parciais
        tasks = []

        # Divide baseado nas primeiras 3 cidades da permutação
        first_city = 0
        remaining_cities = list(range(1, n_cities))

        # Gera combinações de 2 cidades para as posições 2 e 3
        second_third_combinations = list(itertools.combinations(remaining_cities, 2))

        # Divide combinações entre workers
        combos_per_worker = max(1, len(second_third_combinations) // num_workers)

        for i in range(num_workers):
            start_idx = i * combos_per_worker
            end_idx = min((i + 1) * combos_per_worker, len(second_third_combinations))

            if start_idx >= len(second_third_combinations):
                break

            # Se é o último worker, pega todas as combinações restantes
            if i == num_workers - 1:
                end_idx = len(second_third_combinations)

            worker_combinations = second_third_combinations[start_idx:end_idx]

            # Estima tamanho do trabalho
            remaining_positions = n_cities - 3  # Três primeiras fixas
            work_size = len(worker_combinations) * math.factorial(remaining_positions)

            task = {
                "distance_matrix": distance_matrix,
                "cities": cities,
                "fixed_first_city": first_city,
                "assigned_second_third_combinations": worker_combinations,
                "estimated_work_size": work_size,
            }

            tasks.append(task)

        return tasks

    def estimate_completion_time(
        self, tasks: List[Dict[str, Any]], worker_performance: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Estima tempo de conclusão para cada tarefa

        Args:
            tasks: Lista de tarefas
            worker_performance: Dicionário com performance de cada worker (perms/sec)

        Returns:
            Dicionário com estimativas de tempo
        """
        if not worker_performance:
            # Usa performance padrão
            default_perf = 1000  # 1000 permutações por segundo
            worker_performance = {
                f"worker_{i}": default_perf for i in range(len(tasks))
            }

        estimates = {}
        for i, task in enumerate(tasks):
            worker_id = f"worker_{i}"
            work_size = task.get("estimated_work_size", 1000)
            perf = worker_performance.get(worker_id, 1000)

            estimated_time = work_size / perf
            estimates[worker_id] = estimated_time

        return estimates
