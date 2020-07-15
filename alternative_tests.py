""" An attempt at making the tests faster by exploiting
the fact that most actions just fail and cause no other effect"""

import actions as act
from copy import copy, deepcopy
import queue

import core_logic
import ast


def test_action_sequences(default_ast, max_action_sequence_length):
    actions = list(act.actions.keys())
    to_test = queue.SimpleQueue()

    get_vim_input = lambda x: 'USER_INPUT'

    # Insert the initial set of actions
    for action in actions:
        to_test.put((deepcopy(default_ast), [], [], action))

    while (case_to_test := to_test.get()) if not to_test.empty() else False:
        tree, cursor_trail, actions_performed, action_name = case_to_test
        action_function, is_local = act.actions[action_name]

        try: 
            cursor_trail_after, tree_after = core_logic.core_act(
                    action_function,
                    is_local,
                    copy(cursor_trail),
                    deepcopy(tree),
                    get_vim_input)

        except Exception as e:
            print("Action sequence: ", str(actions_performed + [action_name]))
            raise e

        # The whole point of this alternative test:
        # If the action kept the state intact, don't bother following it up with anything
        if cursor_trail == cursor_trail_after and identical_nodes(tree, tree_after):
            continue

        # Assert the invariant (The ast should be valid at all times)
        assert core_logic.is_valid_ast(tree
                ), "actions: " + str(actions_performed + [action_name])

        # This print makes it satisfying to watch the number of remainig checks going down
        print(to_test.qsize())
        if len(actions_performed) < max_action_sequence_length:
            for action in actions:
                to_test.put((tree_after, cursor_trail_after, 
                    actions_performed + [action_name], action))


def identical_nodes(tree1, tree2):
    """ Tests if the two ast nodes are identical """
    # TODO: Check more than the fields for the module node

    if isinstance(tree1, list) and isinstance(tree2, list):
        if len(tree1) != len(tree2):
            #print("Different lens: ", len(tree1), len(tree2))
            return False
        
        for (v1, v2) in zip(tree1, tree2):
            if not identical_nodes(v1, v2):
                #print(v1, " different from ", v2)
                return False
            
        return True

    # Do regular equality on regular objects
    if not (isinstance(tree1, ast.AST) and isinstance(tree2, ast.AST)):
        #print("regular equality: ", tree1, tree2)
        return tree1 == tree2

    if not tree1._fields == tree2._fields:
        #print("Different field")
        return False

    # Check if each field has an identical node
    for fieldname in tree1._fields:
        if not identical_nodes(getattr(tree1, fieldname), getattr(tree2, fieldname)):
            #print("Non identical ", fieldname)
            return False

    return True


if __name__ == '__main__':
    with open('python_file_examples/sudoku.py', 'r') as f:
        tree = ast.parse(f.read())

    test_action_sequences(tree, 3)
    #copy = deepcopy(tree)
    #print(identical_nodes(tree, copy))
