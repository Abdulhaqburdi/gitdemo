import copy
INFINITY = 16


class Router:
    def __init__(self, name, split_horizon=False, poison_reverse=False):
        self.name = name

        self.neighbors = {}

      
        self.routing_table = {self.name: [0, self.name]}

        self.split_horizon = split_horizon
        self.poison_reverse = poison_reverse

    def add_neighbor(self, neighbor_name, cost=1):
        """Register a direct neighbor and seed the routing table entry."""
        self.neighbors[neighbor_name] = cost
        if neighbor_name not in self.routing_table or self.routing_table[neighbor_name][0] > cost:
            self.routing_table[neighbor_name] = [cost, neighbor_name]

    def remove_neighbor(self, neighbor_name):
        """Drop a direct neighbor (used to simulate a link failure)."""
        if neighbor_name in self.neighbors:
            del self.neighbors[neighbor_name]


    def advertise_to(self, neighbor_name):
        """
        Build the distance vector this router sends to 'neighbor_name'.
        Applies Split Horizon / Poison Reverse when the destination's
        current best route happens to go back out through that same
        neighbor (i.e. would create a routing loop if advertised as-is).

        Returns: dict {destination: advertised_cost}
        """
        vector = {}
        for dest, (cost, next_hop) in self.routing_table.items():
            learned_via_this_neighbor = (next_hop == neighbor_name and neighbor_name in self.neighbors)

            if learned_via_this_neighbor:
                if self.poison_reverse:
                    vector[dest] = INFINITY   
                elif self.split_horizon:
                    continue                 
                else:
                    vector[dest] = cost        
            else:
                vector[dest] = cost
        return vector

    def update_table(self, from_neighbor, received_vector):
        """
        Bellman-Ford relaxation: incorporate a neighbor's advertised
        distance vector into this router's own routing table.

        Returns True if the routing table changed as a result.
        """
        changed = False

        if from_neighbor not in self.neighbors:
            return False  # advertisement from a link that no longer exists

        link_cost = self.neighbors[from_neighbor]

        for dest, adv_cost in received_vector.items():
            if dest == self.name:
                continue  

            new_cost = adv_cost + link_cost
            if new_cost > INFINITY:
                new_cost = INFINITY

            if dest not in self.routing_table:
                if new_cost < INFINITY:
                    self.routing_table[dest] = [new_cost, from_neighbor]
                    changed = True
                continue

            current_cost, current_next_hop = self.routing_table[dest]

            if current_next_hop == from_neighbor:
                
                if new_cost != current_cost:
                    self.routing_table[dest] = [new_cost, from_neighbor]
                    changed = True
            elif new_cost < current_cost:
                # Strictly better alternate route found
                self.routing_table[dest] = [new_cost, from_neighbor]
                changed = True

        return changed

    
    def get_table_copy(self):
        return copy.deepcopy(self.routing_table)

    def print_table(self):
        """Full, detailed table - used sparingly (one example router)."""
        print(f"\nRouting Table for {self.name}:")
        print(f"{'Destination':<12}{'Cost':<8}{'Next Hop':<10}")
        for dest in sorted(self.routing_table.keys()):
            cost, next_hop = self.routing_table[dest]
            cost_display = "INF" if cost >= INFINITY else str(cost)
            print(f"{dest:<12}{cost_display:<8}{next_hop:<10}")

    def print_table_compact(self):
        """One clean line per router - used for screenshot-friendly summaries."""
        parts = []
        for dest in sorted(self.routing_table.keys()):
            cost, next_hop = self.routing_table[dest]
            c = "INF" if cost >= INFINITY else str(cost)
            parts.append(f"{dest}({c} via {next_hop})")
        print(f"  {self.name:<4} -> " + ", ".join(parts))