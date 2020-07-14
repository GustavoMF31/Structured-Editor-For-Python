from copy import deepcopy
from hypothesis import strategies as st
from hypothesis import given
import ast
import astor

import renderer
import actions
import core_logic

# TODO: Make a directory with a bunch of kwnow valid .py files
# And test with them all

# I'm assuming dummy.py isn't messed up
tree = ast.parse(open("dummy.py", "r").read())


def get_copied_tree():
    return deepcopy(tree)


def get_action_info(action_name):
    return actions.actions[action_name]


list_of_action_names_strategy = st.lists(
                st.sampled_from(list(actions.actions))
            )


@given(st.builds(get_copied_tree), list_of_action_names_strategy)
def action_sequence_keeps_ast_valid(valid_ast, list_of_action_names):
    # This function assumes the actions don't have local state
    # Will likely break otherwise
    
    action_infos = map(get_action_info, list_of_action_names) 

    # Stub the get input function
    get_vim_input = lambda x : "USER_INPUT"

    # Initialize what are usually the global variables
    cursor_trail = []

    for action_info in action_infos:
        action_function, is_in_place, is_local = action_info

        cursor_trail, valid_ast = core_logic.core_act(
                action_function,
                is_in_place,
                is_local,
                cursor_trail,
                valid_ast,
                get_vim_input
            )

    # If everything went well we haven't crashed and the ast is still valid
    was_valid, exception = core_logic.is_valid_ast(valid_ast)
    if not was_valid:
        raise exception


if __name__ == "__main__":
    action_sequence_keeps_ast_valid()
