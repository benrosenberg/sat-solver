import os
import time
from enum import Enum

from dpll_sat import Clause, CNF


class ParserState(Enum):
    INIT = 0
    PROB = 1


def parse_dimacs(filename) -> CNF:
    parser_state = ParserState.INIT
    num_literals, num_clauses = -1, -1
    clauses = []
    current_literals = set()
    with open(filename, "r") as f:
        for line_num, line in enumerate(f.readlines()):
            # remove trailing whitespace
            line = line.rstrip()
            # skip empty lines
            if not line:
                continue
            # skip comments
            if line[0] == "c":
                continue
            if parser_state == ParserState.INIT:
                if line[0] != "p":
                    raise ValueError(
                        'Error on line {}: Unexpected character "{}" found while parsing in INIT state'.format(
                            line_num, line[0]
                        )
                    )
                prob_info = line.split()
                assert len(prob_info) == 4
                assert prob_info[0] == "p"
                assert prob_info[1] == "cnf", "Non-CNF formats unsupported"
                try:
                    num_literals = int(prob_info[2])
                except ValueError:
                    print(
                        'Error on line {}: Invalid (non-integer) number of literals: "{}"'.format(
                            line_num, prob_info[2]
                        )
                    )
                try:
                    num_clauses = int(prob_info[3])
                except ValueError:
                    print(
                        'Error on line {}: Invalid (non-integer) number of clauses: "{}"'.format(
                            line_num, prob_info[3]
                        )
                    )
                parser_state = ParserState.PROB
            elif parser_state == ParserState.PROB:
                literal_strs = line.split()
                literals = set()
                final_line = False  # track whether 0 encountered
                for index, literal_str in enumerate(literal_strs):
                    if literal_str == "0":
                        assert (
                            index == len(literal_strs) - 1
                        ), "Error on line {}: Zero terminator encountered in index {}, not as final integer".format(
                            line_num, index
                        )
                        final_line = True
                    else:
                        try:
                            literal = int(literal_str)
                        except ValueError:
                            print(
                                'Error on line {}: Invalid (non-integer) literal value encountered: "{}"'.format(
                                    line_num, literal_str
                                )
                            )
                        literals.add(literal)
                current_literals |= literals
                if final_line:
                    clauses.append(Clause(current_literals))
                    current_literals.clear()
            else:
                raise ValueError(
                    'Error on line {}: Parser is in unknown state "{}"'.format(
                        line_num, parser_state
                    )
                )
    if current_literals:
        raise ValueError(
            "Error at end of file: Last clause not terminated with 0, {} literals discarded".format(
                len(current_literals)
            )
        )
    return CNF(clauses, num_literals=num_literals, num_clauses=num_clauses)


if __name__ == "__main__":
    filename = "aim-50-1_6-yes1-1.cnf"
    print("Test: parsing {}".format(filename))
    problem = parse_dimacs(os.path.join("aim", filename))
    print("Parsed {} successfully.".format(filename))
    start_time = time.time()
    result = problem.dpll()
    print(
        "{} in {:.2f}s".format("SAT" if result else "UNSAT", time.time() - start_time)
    )
    from timeout import timeout_wrapper

    result = timeout_wrapper(problem.dpll)
    print(
        "{} in {:.2f}s".format("SAT" if result else "UNSAT", time.time() - start_time)
    )
