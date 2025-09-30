import operator
import unittest
from random import choice
from functools import reduce
from typing import List, Set, Optional

# literal: int.
# if literal is negative, it is negated, otherwise positive


class Clause:
    """Represents a disjunction of literals (a clause)."""

    def __init__(self, literals: Set[int]):
        # Use frozenset internally for proper hashing/comparison stability
        # and to enforce that literals within a clause are unique.
        self.literals = set(literals)

    def __len__(self):
        return len(self.literals)

    def __hash__(self):
        # Must return an integer. Hash of a frozenset of literals ensures
        # that clauses with the same literals are considered equal.
        return hash(frozenset(self.literals))

    def __eq__(self, other):
        if not isinstance(other, Clause):
            return False
        return self.literals == other.literals

    def __repr__(self):
        return "({})".format(", ".join(map(str, sorted(self.literals))))

    def dupe(self):
        """Returns a deep copy of the clause."""
        return Clause(set(self.literals))

    def remove(self, literal: int):
        """Removes a literal from the clause set."""
        self.literals.discard(literal)


class CNF:
    """Represents a Conjunctive Normal Form (CNF) formula (a set of clauses)."""

    def __init__(
        self,
        clauses: List[Clause],
        num_literals: Optional[int] = None,
        num_clauses: Optional[int] = None,
    ):
        # Use a set of Clause objects for efficient clause management
        self.clauses = set(clauses)
        self.num_literals = (
            num_literals if num_literals is not None else len(self.get_literals())
        )
        self.num_clauses = num_clauses if num_clauses is not None else len(self.clauses)

    def __repr__(self):
        return "CNF: {" + " ^ ".join(str(c) for c in self.clauses) + "}"

    def get_literals(self):
        return reduce(operator.or_, [c.literals for c in self.clauses], set())

    def add_literal(self, literal: int) -> "CNF":
        """
        Returns a *new* CNF object representing the current formula
        AND the new unit clause containing the literal.
        This is used for the splitting step.
        """
        new_clauses = [c.dupe() for c in self.clauses]
        new_clauses.append(Clause({literal}))
        return CNF(new_clauses)

    def is_sat(self) -> bool:
        """
        Checks if the CNF is satisfied. In DPLL, this means the clause set is empty.
        (Note: The original implementation logic was confusing here, using the standard
        DPLL definition: an empty set of clauses is satisfied.)
        """
        return len(self.clauses) == 0

    def is_unsat(self) -> bool:
        """
        Checks if the CNF is unsatisfiable, which occurs when it contains
        an empty clause (a clause with length 0, denoted as \\square).
        """
        return any(len(c) == 0 for c in self.clauses)

    def apply_pure(self, verbose=True) -> bool:
        """
        Applies Pure Literal Elimination.
        Removes all clauses containing a pure literal (one that appears only
        positively or only negatively across the formula).
        Returns True if any clause was removed.
        """
        # Find all literals present in the formula
        all_literals = self.get_literals()

        # Determine the set of pure literals
        pure_set = {l for l in all_literals if -l not in all_literals}

        if not pure_set:
            return False

        clauses_to_keep = set()
        removed_count = 0

        # Keep only clauses that DO NOT contain a pure literal
        for clause in self.clauses:
            if not clause.literals.intersection(pure_set):
                clauses_to_keep.add(clause)
            else:
                removed_count += 1

        self.clauses = clauses_to_keep
        if verbose:
            print(f"  > Pure Literal Elimination: Removed {removed_count} clauses.")
        return removed_count > 0

    def apply_unit(self, verbose=True) -> bool:
        """
        Applies Unit Propagation.
        Finds the first unit clause (length 1) and assigns its literal to True.
        1. Removes clauses containing the unit literal (satisfied).
        2. Removes the negation of the unit literal from other clauses (simplification).
        Returns True if any unit propagation occurred (i.e., if a unit clause was found).
        """
        unit_clauses = [c for c in self.clauses if len(c) == 1]

        if not unit_clauses:
            return False

        # Select the first unit literal found
        (unit_literal,) = unit_clauses[0].literals
        removed_clauses = set()
        simplified_clauses = 0

        # Create a new set of clauses after applying the assignment
        new_clauses = set()

        for other_clause in self.clauses:
            # Skip the clause that was used for propagation (it will be satisfied)
            if other_clause == unit_clauses[0]:
                continue

            # Case 1: Clause is satisfied (contains the unit literal)
            if unit_literal in other_clause.literals:
                removed_clauses.add(
                    other_clause
                )  # Mark for removal (or simply don't add to new_clauses)

            # Case 2: Clause is simplified (contains the negation)
            elif -unit_literal in other_clause.literals:
                simplified_clauses += 1
                # Must create a deep copy to modify it safely while iterating/building new set
                simplified_clause = other_clause.dupe()
                simplified_clause.remove(-unit_literal)
                new_clauses.add(simplified_clause)

            # Case 3: Clause is unaffected
            else:
                new_clauses.add(other_clause)

        self.clauses = new_clauses
        if verbose:
            print(f"  > Unit Propagation (Literal={unit_literal}): Formula simplified.")
        return True  # Since we found a unit clause, propagation occurred

    def apply_split(self, verbose=True) -> bool:
        """
        Selects an arbitrary literal and tries DPLL with the literal set to True,
        and if that fails, tries it set to False (by adding the negative unit clause).
        """
        # Find all literals present in the formula
        literals = self.get_literals()

        if not literals:
            # Should not happen if not is_sat() or is_unsat() returned True
            return False

        # Select some literal randomly to split on
        split_literal = choice(tuple(literals))
        if verbose:
            print(f"  > Splitting on literal: {split_literal}")

        # DPLL(F U {l}) OR DPLL(F U {~l})
        return (
            self.add_literal(split_literal).dpll()
            or self.add_literal(-split_literal).dpll()
        )

    def dpll(self, verbose: bool = False) -> bool:
        """The main DPLL algorithm loop."""
        if verbose:
            print(f"\n--- Starting DPLL Cycle ({len(self.clauses)} clauses) ---")

        # 1. Apply Unit Propagation until no more unit clauses exist
        while self.apply_unit(verbose=verbose):
            # Check for immediate contradiction after propagation
            if self.is_unsat():
                if verbose:
                    print("--- UNSAT: Found empty clause after Unit Propagation ---")
                return False

        # 2. Apply Pure Literal Elimination until no more pure literals exist
        while self.apply_pure(verbose=verbose):
            pass

        # 3. Check for base cases
        if self.is_sat():
            if verbose:
                print("--- SAT: Clause set is empty ---")
            return True

        if self.is_unsat():
            if verbose:
                print("--- UNSAT: Found empty clause (after pure elimination) ---")
            return False

        # 4. Splitting (Branching)
        return self.apply_split(verbose=verbose)


class DPLLTests(unittest.TestCase):

    def test_01_trivial_sat(self):
        """Test the empty formula: it is always SAT."""
        cnf = CNF([])
        self.assertTrue(cnf.dpll(), "Empty CNF should be SAT.")

    def test_02_trivial_unsat(self):
        """Test the formula containing only the empty clause: it is UNSAT."""
        cnf = CNF([Clause(set())])
        self.assertFalse(cnf.dpll(), "CNF with empty clause should be UNSAT.")

    def test_03_unit_propagation_sat(self):
        """Test formula solvable by Unit Propagation (e.g., (1) ^ (~1 v 2))."""
        clauses = [
            Clause({1}),  # Unit clause: 1 is True
            Clause({-1, 2}),  # Should simplify to (2)
        ]
        cnf = CNF(clauses)
        self.assertTrue(cnf.dpll(), "Unit propagation should lead to SAT.")

    def test_04_unit_propagation_unsat(self):
        """Test formula solvable by Unit Propagation leading to contradiction (e.g., (1) ^ (~1))."""
        clauses = [
            Clause({1}),  # 1 is True
            Clause({-1}),  # -1 is True, leading to 1 AND -1 (contradiction)
        ]
        cnf = CNF(clauses)
        self.assertFalse(
            cnf.dpll(), "Unit propagation of a contradiction should be UNSAT."
        )

    def test_05_pure_literal_elimination_sat(self):
        """Test formula solvable by Pure Literal Elimination (e.g., (1 v 2) ^ (-2 v 3) ^ (1 v 3))."""
        # Literal 2 is NOT pure (appears as 2 and -2).
        # Literal 3 is PURE (only appears as 3).
        clauses = [Clause({1, 2}), Clause({-2, 3}), Clause({1, 3})]
        cnf = CNF(clauses)
        # Setting 3=True should satisfy and remove the last two clauses.
        # The remaining clause (1 v 2) will satisfy the formula.
        self.assertTrue(cnf.dpll(), "Pure literal elimination should lead to SAT.")

    def test_06_simple_splitting_sat(self):
        """Test a formula requiring one split to be solved (e.g., (1 v 2))."""
        # No unit or pure literals. Must split.
        clauses = [Clause({1, 2}), Clause({-1, -2})]
        cnf = CNF(clauses)
        # Split on 1.
        # Branch 1 (+1): Formula becomes (1) ^ (-1 v -2) -> Unit prop -> (-2). Final state: (-2) -> SAT.
        # Branch 2 (-1): Formula becomes (-1) ^ (1 v 2) -> Unit prop -> (2). Final state: (2) -> SAT.
        self.assertTrue(cnf.dpll(), "Splitting should resolve to SAT.")

    def test_07_unsat_requiring_splitting(self):
        """Test a formula that is inherently UNSAT and requires splitting (XOR of 3 vars, e.g., (1 XOR 2 XOR 3) and (1 XOR 2 XOR 3)). This is a known UNSAT case."""
        # A simple contradiction with 2 variables: (A v B) ^ (A v ~B) ^ (~A v B) ^ (~A v ~B)
        # This covers all 4 possible assignments for A and B.
        clauses = [Clause({1, 2}), Clause({1, -2}), Clause({-1, 2}), Clause({-1, -2})]
        cnf = CNF(clauses)
        # Requires splitting, which will eventually lead to an empty clause on all branches.
        # Split on 1:
        #   Branch 1 (+1): (1) ^ (1 v 2) ^ (1 v -2) ^ (-1 v 2) ^ (-1 v -2)
        #     Unit Prop (+1): Clauses (1 v 2) and (1 v -2) satisfied/removed.
        #     Simplify: (-1 v 2) -> (2). (-1 v -2) -> (-2).
        #     New state: (1) ^ (2) ^ (-2). -> Unit Prop on (2), then on (-2). -> Empty Clause. UNSAT.
        #   Branch 2 (-1): Similarly leads to (1) ^ (-1) and UNSAT.
        self.assertFalse(
            cnf.dpll(), "Formula covering all possibilities should be UNSAT."
        )

    def test_08_complex_php_3_to_2_unsat(self):
        """
        Test the Pigeonhole Principle (PHP_3^2): placing 3 pigeons (1, 2, 3) into 2 holes (A, B) is impossible.
        Variables: 1=P1A, 2=P1B, 3=P2A, 4=P2B, 5=P3A, 6=P3B
        This requires deep, non-trivial branching to prove UNSAT.
        """
        clauses = [
            # Every pigeon must be in a hole (Exhaustion)
            Clause({1, 2}),
            Clause({3, 4}),
            Clause({5, 6}),
            # Hole A can't hold two pigeons (Exclusivity)
            Clause({-1, -3}),  # Not (P1A and P2A)
            Clause({-1, -5}),  # Not (P1A and P3A)
            Clause({-3, -5}),  # Not (P2A and P3A)
            # Hole B can't hold two pigeons (Exclusivity)
            Clause({-2, -4}),  # Not (P1B and P2B)
            Clause({-2, -6}),  # Not (P1B and P3B)
            Clause({-4, -6}),  # Not (P2B and P3B)
        ]
        cnf = CNF(clauses)
        self.assertFalse(cnf.dpll(), "Pigeonhole Principle (3 into 2) should be UNSAT.")

    def test_09_moderate_random_3cnf_sat(self):
        """
        Test a moderately sized, randomly constructed 3-CNF that is SAT.
        V=7, C=15. Ratio C/V ~ 2.1. This should require a few branches.
        """
        clauses = [
            Clause({-1, -2, -3}),
            Clause({-2, 3, 7}),
            Clause({-1, 4, 5}),
            Clause({1, 2, -6}),
            Clause({3, 4, -7}),
            Clause({-4, 5, 6}),
            Clause({1, -5, -6}),
            Clause({-3, -4, 7}),
            Clause({-1, 2, 5}),
            Clause({1, -3, 6}),
            Clause({-5, 6, 7}),
            Clause({-2, -5, -7}),
            Clause({-1, 3, -4}),
            Clause({2, 4, -5}),
            Clause({1, -7}),  # This unit/near-unit helps guide the solver
        ]
        cnf = CNF(clauses)
        self.assertTrue(cnf.dpll(), "Moderate random 3-CNF should be SAT.")


if __name__ == "__main__":
    # You can run the tests by uncommenting the line below:
    unittest.main(argv=["first-arg-is-ignored"], exit=False)

    # Example usage for manual testing:
    print("\n--- Manual Test: (1) ^ (~1 v 2) ---")
    manual_clauses = [Clause({1}), Clause({-1, 2})]
    manual_cnf = CNF(manual_clauses)
    print(f"Result: {manual_cnf.dpll()}")  # Expected: True

    print("\n--- Manual Test: (1) ^ (-1) ---")
    manual_clauses_unsat = [Clause({1}), Clause({-1})]
    manual_cnf_unsat = CNF(manual_clauses_unsat)
    print(f"Result: {manual_cnf_unsat.dpll()}")  # Expected: False
