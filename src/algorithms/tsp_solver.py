import itertools
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class TSPSolver:
    """Solver para problemas TSP usando diferentes estratégias"""

    def __init__(self):
        self.logger = None

    def solve_tsp_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve uma subtarefa TSP baseada nos dados fornecidos

        Args:
            task_data: Dados da tarefa contendo matriz de distâncias, cidades e parâmetros

        Returns:
            Resultado contendo melhor caminho e custo encontrado
        """
        start_time = time.time()

        distance_matrix = np.array(task_data["distance_matrix"])
        cities = task_data["cities"]
        task_type = task_data.get("task_type", "index_range")

        if task_type == "index_range":
            result = self._solve_index_range_task(task_data, distance_matrix, cities)
        elif "assigned_second_cities" in task_data:
            result = self._solve_medium_problem_task(task_data, distance_matrix, cities)
        elif "assigned_second_third_combinations" in task_data:
            result = self._solve_large_problem_task(task_data, distance_matrix, cities)
        else:
            # Fallback to simple exhaustive search
            result = self._solve_exhaustive(distance_matrix, cities)

        processing_time = time.time() - start_time
        result["processing_time"] = processing_time

        return result

    def _solve_index_range_task(
        self, task_data: Dict[str, Any], distance_matrix: np.ndarray, cities: List[str]
    ) -> Dict[str, Any]:
        """Resolve tarefa usando range de índices de permutações"""
        start_idx = task_data["start_permutation_index"]
        end_idx = task_data["end_permutation_index"]
        fixed_first_city = task_data.get("fixed_first_city", 0)

        n_cities = len(cities)
        if n_cities <= 1:
            return {
                "best_path": cities,
                "best_cost": 0.0,
                "paths_evaluated": 0,
            }

        # Cidades restantes (excluindo a primeira fixa)
        remaining_cities = [i for i in range(n_cities) if i != fixed_first_city]

        best_cost = float("inf")
        best_path = None
        paths_evaluated = 0

        # Gera permutações usando islice para eficiência
        perms_generator = itertools.islice(
            itertools.permutations(remaining_cities), start_idx, end_idx
        )

        for perm in perms_generator:
            # Constrói caminho completo com primeira cidade fixa
            path = [fixed_first_city] + list(perm)
            cost = self._calculate_path_cost_numpy(distance_matrix, path)

            if cost < best_cost:
                best_cost = cost
                best_path = [cities[i] for i in path]

            paths_evaluated += 1

        return {
            "best_path": best_path or cities,
            "best_cost": best_cost if best_cost != float("inf") else 0.0,
            "paths_evaluated": paths_evaluated,
        }

    def _solve_medium_problem_task(
        self, task_data: Dict[str, Any], distance_matrix: np.ndarray, cities: List[str]
    ) -> Dict[str, Any]:
        """Resolve tarefa para problema médio com segundas cidades fixas"""
        fixed_first_city = task_data["fixed_first_city"]
        assigned_second_cities = task_data["assigned_second_cities"]

        n_cities = len(cities)
        best_cost = float("inf")
        best_path = None
        paths_evaluated = 0

        for second_city in assigned_second_cities:
            # Cidades restantes (excluindo primeira e segunda fixas)
            remaining_cities = [
                i for i in range(n_cities) if i not in [fixed_first_city, second_city]
            ]

            # Gera todas as permutações das cidades restantes
            for perm in itertools.permutations(remaining_cities):
                path = [fixed_first_city, second_city] + list(perm)
                cost = self._calculate_path_cost_numpy(distance_matrix, path)

                if cost < best_cost:
                    best_cost = cost
                    best_path = [cities[i] for i in path]

                paths_evaluated += 1

        return {
            "best_path": best_path or cities,
            "best_cost": best_cost if best_cost != float("inf") else 0.0,
            "paths_evaluated": paths_evaluated,
        }

    def _solve_large_problem_task(
        self, task_data: Dict[str, Any], distance_matrix: np.ndarray, cities: List[str]
    ) -> Dict[str, Any]:
        """Resolve tarefa para problema grande com combinações de segunda/terceira cidades"""
        fixed_first_city = task_data["fixed_first_city"]
        assigned_combinations = task_data["assigned_second_third_combinations"]

        n_cities = len(cities)
        best_cost = float("inf")
        best_path = None
        paths_evaluated = 0

        for second_city, third_city in assigned_combinations:
            # Cidades restantes
            remaining_cities = [
                i
                for i in range(n_cities)
                if i not in [fixed_first_city, second_city, third_city]
            ]

            # Gera permutações das cidades restantes
            for perm in itertools.permutations(remaining_cities):
                path = [fixed_first_city, second_city, third_city] + list(perm)
                cost = self._calculate_path_cost_numpy(distance_matrix, path)

                if cost < best_cost:
                    best_cost = cost
                    best_path = [cities[i] for i in path]

                paths_evaluated += 1

        return {
            "best_path": best_path or cities,
            "best_cost": best_cost if best_cost != float("inf") else 0.0,
            "paths_evaluated": paths_evaluated,
        }

    def _solve_exhaustive(
        self, distance_matrix: np.ndarray, cities: List[str]
    ) -> Dict[str, Any]:
        """Resolve TSP usando busca exaustiva completa"""
        n_cities = len(cities)
        if n_cities <= 1:
            return {
                "best_path": cities,
                "best_cost": 0.0,
                "paths_evaluated": 0,
            }

        best_cost = float("inf")
        best_path = None
        paths_evaluated = 0

        # Fixa primeira cidade e permuta as restantes
        remaining_indices = list(range(1, n_cities))

        for perm in itertools.permutations(remaining_indices):
            path = [0] + list(perm)  # Primeira cidade sempre é índice 0
            cost = self._calculate_path_cost_numpy(distance_matrix, path)

            if cost < best_cost:
                best_cost = cost
                best_path = [cities[i] for i in path]

            paths_evaluated += 1

        return {
            "best_path": best_path or cities,
            "best_cost": best_cost if best_cost != float("inf") else 0.0,
            "paths_evaluated": paths_evaluated,
        }

    def _calculate_path_cost_numpy(
        self, distance_matrix: np.ndarray, path: List[int]
    ) -> float:
        """
        Calcula custo de um caminho usando NumPy para melhor performance

        Args:
            distance_matrix: Matriz de distâncias como array NumPy
            path: Lista de índices das cidades na ordem do caminho

        Returns:
            Custo total do caminho
        """
        if len(path) < 2:
            return 0.0

        # Usa indexação avançada do NumPy para calcular distâncias
        path_array = np.array(path)
        costs = distance_matrix[path_array[:-1], path_array[1:]]

        # Adiciona custo de retorno à cidade inicial
        return_cost = distance_matrix[path[-1], path[0]]

        return np.sum(costs) + return_cost

    def _calculate_path_cost(
        self, distance_matrix: List[List[float]], path: List[int]
    ) -> float:
        """
        Calcula custo de um caminho (versão tradicional)

        Args:
            distance_matrix: Matriz de distâncias
            path: Lista de índices das cidades na ordem do caminho

        Returns:
            Custo total do caminho
        """
        if len(path) < 2:
            return 0.0

        total_cost = 0.0

        # Soma distâncias entre cidades consecutivas
        for i in range(len(path) - 1):
            total_cost += distance_matrix[path[i]][path[i + 1]]

        # Adiciona custo de retorno à cidade inicial
        total_cost += distance_matrix[path[-1]][path[0]]

        return total_cost

    def solve_tsp_heuristic(
        self, distance_matrix: List[List[float]], cities: List[str]
    ) -> Dict[str, Any]:
        """
        Resolve TSP usando heurística nearest neighbor para problemas grandes

        Args:
            distance_matrix: Matriz de distâncias
            cities: Lista de nomes das cidades

        Returns:
            Resultado com caminho e custo aproximado
        """
        n_cities = len(cities)
        if n_cities <= 1:
            return {
                "best_path": cities,
                "best_cost": 0.0,
                "paths_evaluated": 1,
                "method": "heuristic_nearest_neighbor",
            }

        best_cost = float("inf")
        best_path = None

        # Tenta começar de cada cidade para melhor resultado
        for start_city in range(n_cities):
            path, cost = self._nearest_neighbor_from_city(
                distance_matrix, start_city, n_cities
            )

            if cost < best_cost:
                best_cost = cost
                best_path = [cities[i] for i in path]

        return {
            "best_path": best_path or cities,
            "best_cost": best_cost if best_cost != float("inf") else 0.0,
            "paths_evaluated": n_cities,
            "method": "heuristic_nearest_neighbor",
        }

    def _nearest_neighbor_from_city(
        self, distance_matrix: List[List[float]], start_city: int, n_cities: int
    ) -> Tuple[List[int], float]:
        """
        Executa algoritmo nearest neighbor começando de uma cidade específica

        Args:
            distance_matrix: Matriz de distâncias
            start_city: Índice da cidade inicial
            n_cities: Número total de cidades

        Returns:
            Tupla com (caminho, custo_total)
        """
        unvisited = set(range(n_cities))
        current_city = start_city
        path = [current_city]
        unvisited.remove(current_city)
        total_cost = 0.0

        while unvisited:
            # Encontra cidade mais próxima não visitada
            nearest_city = min(
                unvisited, key=lambda city: distance_matrix[current_city][city]
            )

            total_cost += distance_matrix[current_city][nearest_city]
            path.append(nearest_city)
            unvisited.remove(nearest_city)
            current_city = nearest_city

        # Adiciona custo de retorno
        total_cost += distance_matrix[current_city][start_city]

        return path, total_cost

    def estimate_task_complexity(self, task_data: Dict[str, Any]) -> int:
        """
        Estima complexidade computacional de uma tarefa

        Args:
            task_data: Dados da tarefa

        Returns:
            Estimativa do número de operações necessárias
        """
        if (
            "start_permutation_index" in task_data
            and "end_permutation_index" in task_data
        ):
            return (
                task_data["end_permutation_index"]
                - task_data["start_permutation_index"]
            )

        if "assigned_second_cities" in task_data:
            n_cities = len(task_data["cities"])
            remaining_cities = n_cities - 2  # Primeira e segunda fixas
            return len(task_data["assigned_second_cities"]) * math.factorial(
                remaining_cities
            )

        if "assigned_second_third_combinations" in task_data:
            n_cities = len(task_data["cities"])
            remaining_cities = n_cities - 3  # Três primeiras fixas
            return len(
                task_data["assigned_second_third_combinations"]
            ) * math.factorial(remaining_cities)

        # Fallback para busca exaustiva
        n_cities = len(task_data.get("cities", []))
        return math.factorial(max(1, n_cities - 1))
