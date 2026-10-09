from distance_vector import Network
from router import Router, INFINITY

TOPOLOGY_EDGES = [
    ("R0", "R1"), ("R0", "R2"), ("R0", "R3"),
    ("R1", "R2"), ("R1", "R3"), ("R1", "R4"), ("R1", "R6"),
    ("R2", "R4"),
    ("R3", "R5"), ("R3", "R6"),
    ("R4", "R6"), ("R4", "R9"),
    ("R5", "R6"), ("R5", "R7"), ("R5", "R8"),
    ("R6", "R7"), ("R6", "R8"), ("R6", "R9"),
    ("R7", "R8"), ("R7", "R9"),
    ("R8", "R9"),
]


def build_base_network(split_horizon=False, poison_reverse=False, triggered_updates=False):
    """Construct the full 10-router campus topology as a Network object."""
    net = Network(split_horizon, poison_reverse, triggered_updates)
    net.build_from_edge_list(TOPOLOGY_EDGES)
    return net

def demonstrate_link_failure_and_recovery():
    print("\n" + "#" * 65)
    print("# LINK FAILURE / RECOVERY DEMONSTRATION   (link R6 - R7)")
    print("#" * 65)

    net = build_base_network(split_horizon=True, poison_reverse=True)
    rounds, elapsed, msgs = net.run_convergence()
    print()
    net.print_stats("Initial convergence", rounds, elapsed, msgs)
    net.print_all_compact("BEFORE FAILURE")

    print("\n>>> Failing link R6-R7 ...")
    net.remove_link("R6", "R7")
    rounds, elapsed, msgs = net.run_convergence()
    net.print_stats("Re-convergence after FAILURE", rounds, elapsed, msgs)
    net.print_all_compact("AFTER FAILURE")

    print("\n>>> Recovering link R6-R7 ...")
    net.add_link("R6", "R7")
    rounds, elapsed, msgs = net.run_convergence()
    net.print_stats("Re-convergence after RECOVERY", rounds, elapsed, msgs)
    net.print_all_compact("AFTER RECOVERY")



def compare_loop_prevention_scenarios():
    scenarios = [
        ("A. No loop prevention",                        False, False, False),
        ("B. Split Horizon",                              True,  False, False),
        ("C. Split Horizon + Poison Reverse",             True,  True,  False),
        ("D. Split Horizon + Poison Reverse + Triggered", True,  True,  True),
    ]

    results = []
    for label, sh, pr, trig in scenarios:
        net = build_base_network(sh, pr, trig)

        if trig:
            rounds, elapsed, msgs = net.run_triggered_convergence()
        else:
            rounds, elapsed, msgs = net.run_convergence()

        # Stress-test this scenario with the same R6-R7 failure
        net.remove_link("R6", "R7")
        if trig:
            f_rounds, f_elapsed, f_msgs = net.run_triggered_convergence()
        else:
            f_rounds, f_elapsed, f_msgs = net.run_convergence()

        route = net.sample_route("R0", "R9")
        route_str = " -> ".join(route) if route else "UNREACHABLE"
        results.append((label, rounds, msgs, f_rounds, f_msgs, route_str))

    
    print()
    header = f"{'Scenario':<48}{'Init':>6}{'Init':>8}{'Fail':>6}{'Fail':>8}"
    print(header)
    header2 = f"{'':<48}{'Rnds':>6}{'Msgs':>8}{'Rnds':>6}{'Msgs':>8}   Sample Route (R0->R9)"
    print(header2)
    print("-" * 100)
    for label, r1, m1, r2, m2, route_str in results:
        print(f"{label:<48}{r1:>6}{m1:>8}{r2:>6}{m2:>8}   {route_str}")


def demonstrate_count_to_infinity():
    
    print("\n" + "#" * 65)
    print("# COUNT-TO-INFINITY DEMONSTRATION  (A - B - C, no loop prevention)")
    print("#" * 65)

    a = Router("A", split_horizon=False, poison_reverse=False)
    b = Router("B", split_horizon=False, poison_reverse=False)
    c = Router("C", split_horizon=False, poison_reverse=False)

    a.add_neighbor("B", 1)
    b.add_neighbor("A", 1)
    b.add_neighbor("C", 1)
    c.add_neighbor("B", 1)

    routers = {"A": a, "B": b, "C": c}

    for _ in range(10):
        changed = False
        vectors = {name: {n: r.advertise_to(n) for n in r.neighbors} for name, r in routers.items()}
        for name, r in routers.items():
            for neighbor in list(r.neighbors):
                if routers[neighbor].update_table(name, vectors[name][neighbor]):
                    changed = True
        if not changed:
            break

    print("\nBefore failure -> C's route to A:", c.routing_table["A"])

    print("\n>>> Link A-B fails ...")
    del a.neighbors["B"]
    del b.neighbors["A"]
    
    b.routing_table["A"] = [INFINITY, "A"]

    print("\nRound-by-round exchange between B and C only "
          "(A is disconnected and no longer participates):\n")

    for i in range(1, 16):
        c_to_b = c.advertise_to("B")
        b.update_table("C", c_to_b)

        b_to_c = b.advertise_to("C")
        c.update_table("B", b_to_c)

        cost_b, hop_b = b.routing_table.get("A", [INFINITY, None])
        cost_c, hop_c = c.routing_table.get("A", [INFINITY, None])

        cb = "INF" if cost_b >= INFINITY else cost_b
        cc = "INF" if cost_c >= INFINITY else cost_c
        print(f"Round {i:2d}: B's route to A = cost {cb} via {hop_b}   |   "
              f"C's route to A = cost {cc} via {hop_c}")

        if cost_b >= INFINITY and cost_c >= INFINITY:
            print("\nMetric saturated at INFINITY on both routers -> loop resolved "
                  "(but only after several slow rounds).")
            break

    print("\nWith Split Horizon, C would never advertise a route learned from")
    print("B back to B, preventing this loop. With Poison Reverse, C would")
    print("advertise that route back to B as INFINITY immediately, resolving")
    print("the failure in a single round instead of many.")