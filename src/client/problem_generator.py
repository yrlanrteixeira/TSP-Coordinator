import math
import random
from typing import Any, Dict


class TSPProblemGenerator:
    """Gerador de problemas TSP para testes"""

    @staticmethod
    def generate_random_problem(num_cities: int, seed: int = None) -> Dict[str, Any]:
        """
        Gera problema TSP aleatório

        Args:
            num_cities: Número de cidades
            seed: Seed para reprodutibilidade

        Returns:
            Dicionário com cities e distance_matrix
        """
        if seed:
            random.seed(seed)

        # Gera nomes das cidades
        cities = [f"City_{i + 1}" for i in range(num_cities)]

        # Gera coordenadas aleatórias
        coordinates = []
        for i in range(num_cities):
            x = random.uniform(0, 100)
            y = random.uniform(0, 100)
            coordinates.append((x, y))

        # Calcula matriz de distâncias euclidianas
        distance_matrix = []
        for i in range(num_cities):
            row = []
            for j in range(num_cities):
                if i == j:
                    distance = 0.0
                else:
                    x1, y1 = coordinates[i]
                    x2, y2 = coordinates[j]
                    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                row.append(distance)
            distance_matrix.append(row)

        return {
            "cities": cities,
            "distance_matrix": distance_matrix,
            "coordinates": coordinates,
            "generated_with_seed": seed,
        }

    @staticmethod
    def load_problem_from_file(file_path: str) -> Dict[str, Any]:
        """
        Carrega problema TSP de arquivo JSON

        Args:
            file_path: Caminho para arquivo JSON

        Returns:
            Dicionário com problema TSP
        """
        import json

        with open(file_path, "r") as f:
            problem = json.load(f)

        # Valida estrutura
        required_fields = ["cities", "distance_matrix"]
        for field in required_fields:
            if field not in problem:
                raise ValueError(f"Missing required field: {field}")

        return problem

    @staticmethod
    def save_problem_to_file(problem: Dict[str, Any], file_path: str):
        """
        Salva problema TSP em arquivo JSON

        Args:
            problem: Dicionário com problema TSP
            file_path: Caminho para salvar
        """
        import json

        with open(file_path, "w") as f:
            json.dump(problem, f, indent=2)

    @staticmethod
    def create_benchmark_problems() -> Dict[str, Dict[str, Any]]:
        """
        Cria conjunto de problemas benchmark para testes

        Returns:
            Dicionário com problemas de diferentes tamanhos
        """
        problems = {}

        # Problema pequeno (4 cidades)
        problems["small"] = TSPProblemGenerator.generate_random_problem(4, seed=42)

        # Problema médio (8 cidades)
        problems["medium"] = TSPProblemGenerator.generate_random_problem(8, seed=123)

        # Problema grande (12 cidades)
        problems["large"] = TSPProblemGenerator.generate_random_problem(12, seed=456)

        return problems
