import time
from router import Router, INFINITY


class Network:
    def __init__(self, split_horizon=False, poison_reverse=False, triggered_updates=False):
        self.routers = {}                       # name -> Router
        self.split_horizon = split_horizon
        self.poison_reverse = poison_reverse
        self.triggered_updates = triggered_updates
        self.messages_sent = 0

    #construct topology.
    def add_router(self, name):
        if name not in self.routers:
            self.routers[name] = Router(name, self.split_horizon, self.poison_reverse)

    def add_link(self, r1, r2, cost=1):
        """Create a bidirectional link -> automatically builds the adjacency list."""
        self.add_router(r1)
        self.add_router(r2)
        self.routers[r1].add_neighbor(r2, cost)
        self.routers[r2].add_neighbor(r1, cost)

    def remove_link(self, r1, r2):
        """Simulate a link failure between two directly connected routers."""
        if r1 in self.routers:
            self.routers[r1].remove_neighbor(r2)
        if r2 in self.routers:
            self.routers[r2].remove_neighbor(r1)

        for name, r in self.routers.items():
            other = r2 if name == r1 else (r1 if name == r2 else None)
            if other is not None and other in r.routing_table:
                cost, next_hop = r.routing_table[other]
                if next_hop == other:
                    r.routing_table[other] = [INFINITY, other]

    def build_from_edge_list(self, edges):
        for (a, b) in edges:
            self.add_link(a, b)

 
    def run_convergence(self, max_rounds=100, verbose=False):
        """
        Run synchronous DV rounds until no router's table changes, or
        max_rounds is reached.

        Returns: (rounds_taken, elapsed_time_seconds, messages_sent)
        """
        start_time = time.time()
        self.messages_sent = 0
        round_num = 0

        while round_num < max_rounds:
            round_num += 1
            any_change = False

            # Step 1 - every router builds an advertisement for every neighbor
            advertisements = {}
            for name, router in self.routers.items():
                for neighbor in router.neighbors:
                    advertisements[(name, neighbor)] = router.advertise_to(neighbor)
                    self.messages_sent += 1

            # Step 2 - every router consumes advertisements addressed to it
            changed_routers = set()
            for (sender, receiver), vector in advertisements.items():
                if self.routers[receiver].update_table(sender, vector):
                    any_change = True
                    changed_routers.add(receiver)

            if verbose:
                shown = changed_routers if changed_routers else "none"
                print(f"Round {round_num}: routers updated = {shown}")

            if not any_change:
                break

        elapsed = time.time() - start_time
        return round_num, elapsed, self.messages_sent

    
    def run_triggered_convergence(self, max_iterations=200, verbose=False):
        """
        Event-driven convergence: only routers whose table just changed
        immediately advertise to their neighbors, instead of waiting for
        the next full periodic round. This models Triggered Updates.

        Returns: (iterations_taken, elapsed_time_seconds, messages_sent)
        """
        start_time = time.time()
        self.messages_sent = 0
        queue = list(self.routers.keys())   # everyone advertises once initially
        iterations = 0

        while queue and iterations < max_iterations:
            iterations += 1
            next_queue = []
            for name in queue:
                router = self.routers[name]
                for neighbor in router.neighbors:
                    vector = router.advertise_to(neighbor)
                    self.messages_sent += 1
                    if self.routers[neighbor].update_table(name, vector):
                        if neighbor not in next_queue:
                            next_queue.append(neighbor)
            if verbose:
                print(f"Trigger step {iterations}: re-advertising = {next_queue if next_queue else 'none'}")
            queue = next_queue

        elapsed = time.time() - start_time
        return iterations, elapsed, self.messages_sent

    
    def print_all_tables(self, label=""):
        """Full, detailed dump - use sparingly (this is verbose)."""
        print(f"\n{'=' * 60}")
        print(f" ROUTING TABLES {label}")
        print(f"{'=' * 60}")
        for name in sorted(self.routers.keys()):
            self.routers[name].print_table()

    def print_all_compact(self, label=""):
        """Clean, one-line-per-router summary - ideal for screenshots."""
        print(f"\n--- {label} ---")
        for name in sorted(self.routers.keys()):
            self.routers[name].print_table_compact()

    @staticmethod
    def print_stats(title, rounds, elapsed, messages):
        print(f"  {title:<32} Rounds: {rounds:<4} Time: {elapsed * 1000:7.3f} ms   Messages: {messages}")

    def sample_route(self, src, dst):
        """Trace the forwarding path from src to dst using next-hop pointers."""
        if src not in self.routers or dst not in self.routers[src].routing_table:
            return None
        path = [src]
        current = src
        visited = set()
        while current != dst:
            if current in visited:
                return None  # a loop was detected in the forwarding path
            visited.add(current)
            cost, next_hop = self.routers[current].routing_table[dst]
            if cost >= INFINITY:
                return None
            current = next_hop
            path.append(current)
        return path