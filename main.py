from simulation import (
    TOPOLOGY_EDGES,
    build_base_network,
    demonstrate_link_failure_and_recovery,
    compare_loop_prevention_scenarios,
    demonstrate_count_to_infinity,
)


def main():
    print("=" * 70)
    print(" CCN CEP - DISTANCE VECTOR (BELLMAN-FORD) ROUTING SIMULATOR")
    print(" Five-Campus Network Topology")
    print("Designed by:Zaheer Ahmed (24CSE10)")
    print("=" * 70)
    print(f" Routers : 10  (R0 - R9)")
    print(f" Links   : {len(TOPOLOGY_EDGES)}  (all costs = 1)")

    
    print("\n" + "#" * 65)
    print("# 1. BASELINE CONVERGENCE  (full 10-router topology)")
    print("#" * 65)

    net = build_base_network()
    net.print_all_compact("BEFORE CONVERGENCE (routers know only direct neighbors)")

    rounds, elapsed, messages = net.run_convergence()

    net.print_all_compact("AFTER CONVERGENCE")

    print("\nExample - full detailed table for R0:")
    net.routers["R0"].print_table()

    print()
    net.print_stats("Baseline convergence stats", rounds, elapsed, messages)


    demonstrate_link_failure_and_recovery()

   
    print("\n" + "#" * 65)
    print("# 3. COMPARISON OF LOOP-PREVENTION SCENARIOS")
    print("#" * 65)
    compare_loop_prevention_scenarios()

  
    demonstrate_count_to_infinity()

    print("\n" + "=" * 70)
    print(" SIMULATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()