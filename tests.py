from copy import deepcopy
from hypothesis import strategies as st
from hypothesis import given, settings, example
import ast
from os import listdir

import renderer
import actions
import core_logic


example_python_files = listdir("python_file_examples")

# Save the name along with the file itself
files = map(lambda x : (x, open("python_file_examples/" + x, "r")), example_python_files)

# Keeps the name there and reads the file
trees = list(map(lambda file : (file[0], ast.parse(file[1].read())), files))

# Close the files
[f.close() for (name, f) in files]


def get_action_info(action_name):
    return actions.actions[action_name]


list_of_action_names_strategy = st.lists(
                st.sampled_from(list(actions.actions)),
            )


# Start all the tests with "cursor_down", otherwise a bunch
# of time gets wasted trying invalid stuff on the Module node
# (the root node)
# Trades a little bit of testing for "amount of actions" times faster testing
list_of_action_names_strategy = list_of_action_names_strategy.map(lambda l : ["cursor_down"] + l)


# TODO: Fail tests that raise syntax warnings
@settings(max_examples=3000)
#@settings(max_examples=60000)
#@settings(max_examples=234256)
@given(st.builds(deepcopy, st.sampled_from(trees)), list_of_action_names_strategy)
@example(deepcopy(trees[0]), [
    'cursor_down',
     'make_call',
     'cursor_down',
     'make_if_exp', "extend" ] 
     )
def action_sequence_keeps_ast_valid(file, list_of_action_names):
    # This function assumes the actions don't have local state
    # Will likely break otherwise

    # Save the name for better error messages
    # even though it isn't needed
    name, valid_ast = file

    action_infos = map(get_action_info, list_of_action_names) 

    # Stub the get input function
    get_vim_input = lambda x : "USER_INPUT"

    # Initialize what are usually the global variables
    cursor_trail = []

    for action_info in action_infos:
        action_function, is_local = action_info

        cursor_trail, valid_ast = core_logic.core_act(
                action_function,
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
    # It takes me 5 minutes to run the total 30.000 tests.
    # Given that we currently have 22 actions
    # Testing every sequence of 5 actions would take me 15 hours
    # (That is the nature of exponential growth...)
    action_sequence_keeps_ast_valid()
