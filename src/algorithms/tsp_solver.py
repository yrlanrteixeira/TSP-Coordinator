import itertools
from typing import Any, Dict, List, Tuple


class TSPSolver:
    def __init__(self):
        self.logger = None

    def solve_partial_permutations(
        self,
        distance_matrix: List[List[float]],
        cities: List[str],
        start_permutations: List[List[int]] = None,
        end_permutations: List[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve TSP para um conjunto específico de permutações
        """
        n_cities = len(cities)

        if start_permutations and end_permutations:
            # Trabalha com range específico de permutações
            permutations = self._generate_permutation_range(
                n_cities, start_permutations, end_permutations
            )
        else:
            # Gera todas as permutações (para casos pequenos)
            permutations = list(itertools.permutations(range(n_cities)))

        best_path = None
        best_cost = float("inf")
        permutations_checked = 0

        for perm in permutations:
            cost = self._calculate_path_cost(distance_matrix, perm)
            permutations_checked += 1

            if cost < best_cost:
                best_cost = cost
                best_path = [cities[i] for i in perm]

        return {
            "best_path": best_path,
            "best_cost": best_cost,
            "permutations_checked": permutations_checked,
        }

    def _generate_permutation_range(
        self, n_cities: int, start_perms: List[List[int]], end_perms: List[List[int]]
    ) -> List[Tuple[int]]:
        """
        Gera permutações entre start e end (usado para distribuição de trabalho)
        """
        # Implementação simplificada - na prática seria mais sofisticada
        all_perms = list(itertools.permutations(range(n_cities)))

        # Para este exemplo, retorna um slice das permutações
        if start_perms and end_perms:
            start_idx = 0
            end_idx = len(all_perms)

            # Encontra índices baseado nas permutações de início e fim
            for i, perm in enumerate(all_perms):
                if list(perm) in start_perms:
                    start_idx = i
                    break

            for i, perm in enumerate(all_perms):
                if list(perm) in end_perms:
                    end_idx = i + 1
                    break

            return all_perms[start_idx:end_idx]

        return all_perms

    def _calculate_path_cost(
        self, distance_matrix: List[List[float]], path: Tuple[int]
    ) -> float:
        """
        Calcula custo total de um caminho no TSP
        """
        total_cost = 0.0
        n_cities = len(path)

        for i in range(n_cities):
            from_city = path[i]
            to_city = path[(i + 1) % n_cities]  # Volta para o início no final
            total_cost += distance_matrix[from_city][to_city]

        return total_cost

    def solve_complete_tsp(
        self, distance_matrix: List[List[float]], cities: List[str]
    ) -> Dict[str, Any]:
        """
        Resolve TSP completo (força bruta) - apenas para casos pequenos
        """
        return self.solve_partial_permutations(distance_matrix, cities)
