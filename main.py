import sys

def parse_var_file(var_file):
    variables = {}
    with open(var_file, "r") as file:
        for line in file:
            parts= line.strip().split(": ")
            variable= parts[0]
            domain= list(map(int, parts[1].split()))
            variables[variable] = domain
    return variables


def parse_con_file(con_file):
    constraints =[]
    with open(con_file, "r") as file:
        for line in file:
            parts=line.strip().split()
            var1,op,var2=parts[0],parts[1],parts[2]
            constraints.append((var1,op,var2))
    return constraints


def select_variable(assignments, variables, domains, constraints): # select most constrained variable, break ties with most constraining, break ties with alphabetical
    unassigned_vars = [var for var in variables if var not in assignments]
    if not unassigned_vars:
        return None
    # most constrained variable == smallest domain size
    min_domain_size = min(len(domains[var]) for var in unassigned_vars)
    most_constrained_vars = [
        var for var in unassigned_vars if len(domains[var]) == min_domain_size
    ]

    if len(most_constrained_vars) > 1:
    # count constraints only when both variables are unassigned.
        constraint_count = {
            var: sum(
                1 for (v1, _, v2) in constraints 
                if (v1 == var or v2 == var) and (v1 not in assignments and v2 not in assignments)
            )
            for var in most_constrained_vars
        }
        max_constraints = max(constraint_count.values())
        most_constrained_vars = [
            var for var in most_constrained_vars if constraint_count[var] == max_constraints
        ]
    return sorted(most_constrained_vars)[0]


def is_consistent(assignments, var, value, constraints):
    for var1, op, var2 in constraints:

        if var1 == var and var2 in assignments:
            if not check_constraint(value, assignments[var2], op):
                return False
        
        elif var2 == var and var1 in assignments:
            if not check_constraint(assignments[var1], value, op):
                return False
    return True


def check_constraint(val1, val2, op):
    # Python2 has no switch statement??? Maybe try match and case if we allowed to use Python3
    if op == "=":
        return val1 == val2
    elif op == "!=":
        return val1 != val2
    elif op == ">":
        return val1 > val2
    elif op == "<":
        return val1 < val2
    return False


def least_constraining_value(var, domains, constraints, assignments):
    def count_conflicts(value):
        count = 0
        for var1, _, var2 in constraints:
            if var1 == var and var2 not in assignments:
                count += sum(
                    1 for val in domains[var2] if not check_constraint(value, val, _)
                )
            elif var2 == var and var1 not in assignments:
                count += sum(
                    1 for val in domains[var1] if not check_constraint(val, value, _)
                )
        return count

    return sorted(domains[var], key=lambda value: (count_conflicts(value), value))


def forward_check(assignments, domains, var, value, constraints):
    local_domains = {v: list(dom) for v, dom in domains.items()}
    local_domains[var] = [value]
    for var1,op,var2 in constraints:
        if var1 == var and var2 not in assignments:
            local_domains[var2] = [
                val for val in local_domains[var2] if check_constraint(value, val, op)
            ]
        elif var2 == var and var1 not in assignments:
            local_domains[var1] = [
                val for val in local_domains[var1] if check_constraint(val, value, op)
            ]
        if any(len(local_domains[v]) == 0 for v in local_domains): # empty domain, return none. Failure
            return None
    return local_domains


def backtracking_search(variables, domains, constraints, fc=False):
    branches_visited = []
    def backtrack(assignments, current_domains):
        if len(assignments) == len(variables): # all variables have an assignment that does not violate a constraint. Solution
            branches_visited.append((assignments.copy(), "solution"))
            return assignments, True
        # else:
        #     branches_visited.append((assignments.copy(), "failure"))
        var = select_variable(assignments, variables, current_domains, constraints)
        if var is None:
            return None, False
        for value in least_constraining_value(
            var, current_domains, constraints, assignments
        ):
            if is_consistent(assignments, var, value, constraints):
                assignments[var] = value
                # Output branch visited
                # branch = ", ".join(f"{v}={assignments[v]}" for v in sorted(assignments))
                # branches_visited.append((assignments.copy(), "failure"))

                # apply forward checking
                if fc:
                    new_domains = forward_check(
                        assignments, current_domains, var, value, constraints
                    )
                    if new_domains is None:
                        branches_visited.append((assignments.copy(), "failure"))
                        del assignments[var]
                        continue
                    result, success = backtrack(assignments, new_domains) # set domains of variablse to new domains
                else:
                    result, success = backtrack(assignments, current_domains) # fc not enabled, keep domains the same

                if success:
                    return result, True
                del assignments[var]
            else:
                assignments[var] = value
                branches_visited.append((assignments.copy(), "failure"))
                del assignments[var]
        return None, False

    solution, success = backtrack({},domains)
    for idx, (assignment, status) in enumerate(branches_visited, 1):
        print(
            f"{idx}. {', '.join(f'{var}={val}' for var, val in assignment.items())} {status}"
        )
    return solution, success


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python csp_solver.py <var_file> <con_file> <none|fc>")
        sys.exit(1)
    var_file = sys.argv[1]
    con_file = sys.argv[2]
    consistency = sys.argv[3]

    variables = parse_var_file(var_file)
    constraints = parse_con_file(con_file)
    domains = {var: list(domain) for var, domain in variables.items()}

    solution, success = backtracking_search(
        variables, domains, constraints, fc=(consistency == "fc")
    )
    # if success:
    #     print("Solution found!")
    # else:
    #     print("No solution exists.")
