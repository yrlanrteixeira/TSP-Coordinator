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
        n_cities = len(cities)

        # Calcula total de permutações
        total_permutations = math.factorial(n_cities)

        # Escolhe estratégia baseada no tamanho do problema
        if n_cities <= 8:
            return self._distribute_small_problem(distance_matrix, cities, num_workers)
        elif n_cities <= 12:
            return self._distribute_medium_problem(distance_matrix, cities, num_workers)
        else:
            return self._distribute_large_problem(distance_matrix, cities, num_workers)

    def _distribute_small_problem(
        self, distance_matrix: List[List[float]], cities: List[str], num_workers: int
    ) -> List[Dict[str, Any]]:
        """
        Distribui problema pequeno (≤8 cidades) usando permutações completas
        """
        n_cities = len(cities)
        all_permutations = list(itertools.permutations(range(n_cities)))
        total_perms = len(all_permutations)

        # Divide permutações entre workers
        perms_per_worker = max(1, total_perms // num_workers)

        tasks = []
        for i in range(num_workers):
            start_idx = i * perms_per_worker
            end_idx = min((i + 1) * perms_per_worker, total_perms)

            if start_idx >= total_perms:
                break

            # Se é o último worker, pega todas as permutações restantes
            if i == num_workers - 1:
                end_idx = total_perms

            worker_permutations = all_permutations[start_idx:end_idx]

            task = {
                "distance_matrix": distance_matrix,
                "cities": cities,
                "start_permutations": [list(p) for p in worker_permutations[:1]],
                "end_permutations": [list(p) for p in worker_permutations[-1:]],
                "estimated_work_size": len(worker_permutations),
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


class AdvancedTaskDistributor(TaskDistributor):
    """Versão avançada do distribuidor com otimizações"""

    def __init__(self):
        super().__init__()
        self.worker_performance_history = {}
        self.task_completion_history = {}

    def distribute_adaptive_tasks(
        self,
        distance_matrix: List[List[float]],
        cities: List[str],
        worker_capabilities: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Distribui tarefas de forma adaptativa baseada nas capacidades dos workers

        Args:
            distance_matrix: Matriz de distâncias
            cities: Lista de cidades
            worker_capabilities: Capacidades de cada worker

        Returns:
            Lista de tarefas otimizadas
        """
        n_cities = len(cities)
        num_workers = len(worker_capabilities)

        # Calcula fator de performance para cada worker
        worker_factors = self._calculate_performance_factors(worker_capabilities)

        # Distribui trabalho proporcionalmente às capacidades
        total_work = math.factorial(n_cities)

        tasks = []
        work_distributed = 0

        for worker_id, factor in worker_factors.items():
            # Calcula quantidade de trabalho para este worker
            worker_work = int(total_work * factor)

            if worker_work == 0:
                continue

            # Cria tarefa para este worker
            task = self._create_adaptive_task(
                distance_matrix,
                cities,
                worker_id,
                work_distributed,
                work_distributed + worker_work,
            )

            tasks.append(task)
            work_distributed += worker_work

        return tasks

    def _calculate_performance_factors(
        self, worker_capabilities: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calcula fatores de performance baseado no histórico e capacidades
        """
        factors = {}
        total_capability = 0

        for worker_id, capabilities in worker_capabilities.items():
            # Fatores baseados em capacidades
            max_cities = capabilities.get("max_cities", 10)
            cpu_cores = capabilities.get("cpu_cores", 1)
            memory_gb = capabilities.get("memory_gb", 1)

            # Fator baseado no histórico
            historical_factor = self._get_historical_performance(worker_id)

            # Combina fatores
            capability_factor = (max_cities / 20) * (cpu_cores / 4) * (memory_gb / 8)
            combined_factor = (capability_factor + historical_factor) / 2

            factors[worker_id] = combined_factor
            total_capability += combined_factor

        # Normaliza fatores
        if total_capability > 0:
            for worker_id in factors:
                factors[worker_id] /= total_capability

        return factors

    def _get_historical_performance(self, worker_id: str) -> float:
        """
        Obtém performance histórica do worker
        """
        if worker_id not in self.worker_performance_history:
            return 0.5  # Valor padrão para workers novos

        history = self.worker_performance_history[worker_id]

        # Calcula média ponderada (dá mais peso a performance recente)
        if not history:
            return 0.5

        total_weight = 0
        weighted_sum = 0

        for i, performance in enumerate(
            reversed(history[-10:])
        ):  # Últimas 10 execuções
            weight = (i + 1) / 10  # Peso crescente para execuções mais recentes
            weighted_sum += performance * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _create_adaptive_task(
        self,
        distance_matrix: List[List[float]],
        cities: List[str],
        worker_id: str,
        start_work: int,
        end_work: int,
    ) -> Dict[str, Any]:
        """
        Cria tarefa adaptada para um worker específico
        """
        n_cities = len(cities)

        # Converte trabalho em permutações
        all_permutations = list(itertools.permutations(range(n_cities)))

        start_idx = min(start_work, len(all_permutations) - 1)
        end_idx = min(end_work, len(all_permutations))

        worker_permutations = all_permutations[start_idx:end_idx]

        return {
            "distance_matrix": distance_matrix,
            "cities": cities,
            "worker_id": worker_id,
            "start_permutations": [list(worker_permutations[0])]
            if worker_permutations
            else [],
            "end_permutations": [list(worker_permutations[-1])]
            if worker_permutations
            else [],
            "estimated_work_size": len(worker_permutations),
            "adaptive_params": {
                "start_work": start_work,
                "end_work": end_work,
                "total_permutations": len(worker_permutations),
            },
        }

    def update_worker_performance(
        self, worker_id: str, permutations_processed: int, processing_time: float
    ):
        """
        Atualiza histórico de performance do worker
        """
        if worker_id not in self.worker_performance_history:
            self.worker_performance_history[worker_id] = []

        # Calcula permutações por segundo
        perms_per_second = (
            permutations_processed / processing_time if processing_time > 0 else 0
        )

        # Adiciona ao histórico
        self.worker_performance_history[worker_id].append(perms_per_second)

        # Mantém apenas os últimos 20 registros
        if len(self.worker_performance_history[worker_id]) > 20:
            self.worker_performance_history[worker_id] = (
                self.worker_performance_history[worker_id][-20:]
            )
