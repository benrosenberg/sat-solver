# SAT solver

Iterative work on a simple SAT solver, benchmarked with [AIM SAT instances](https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/AIM/descr.html).

- 2025-09-29 - Initial implementation of SAT solver using DPLL

TODO (future optimizations):

- CDCL (clause learning and non-chronological backtracking)
- Data structure improvements

## Notes

These tests are run on a Windows 10 desktop computer with an AMD Ryzen 3700X, 32GB of RAM, and an NVIDIA RTX 3060 Ti.

The wrapper in `timeout.py` is used to kill solver execution after some time threshold. A timeout of 10 seconds was arbitrarily chosen.