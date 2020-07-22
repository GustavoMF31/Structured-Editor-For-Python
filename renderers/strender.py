import ast

SPACES_PER_INDENTATION_LEVEL = 4


def render_view(tree, selected_node, window_width):
    return render(tree, cols_left=window_width)


def render(node, identation_levels=0, cols_left=80):
    class_name = type(node).__name__
    render_function = globals().get('render_' + class_name, not_implemented_render)

    # indentation is how many levels indented the node should draw itself
    # cols-left is the amount of room it will have left on the line to draw itself
    # given that it will draw the indentation first
    return render_function(node, identation_levels, cols_left)


def not_implemented_render(node, indentation, cols_left):
    return indent(indentation, "NOT IMPLEMENTED")


def render_Module(node, indentation, cols_left):
    end_of_imports = first_matching(node.body, lambda x: not is_import(x))
    imports, rest = node.body[:end_of_imports], node.body[end_of_imports:]

    return (
            # The docstring
            # TODO: :)
            # Start with the imports
            newline_join(map(lambda x : render(x, indentation, cols_left), imports))
            # Some space
            + '\n\n\n' 
            # Then the definitions separated by two newlines
            + '\n\n\n'.join(map(lambda x: render(x, indentation, cols_left), rest))
            # Then a trailing newline
            + '\n'
           )


def render_Import(node, indentation, cols_left):
    initial_cols_left = cols_left

    import_str = "import "

    # Remove the indentation size
    # And the size of the import keyword string
    cols_left = cols_left - SPACES_PER_INDENTATION_LEVEL - len(import_str)

    rendered_aliases = list(map(render, node.names))
    
    # If drawing all of them would go off screen
    # len + 2 becaus of the ", " in between
    # Except for the last one (so -2 in the end)
    if sum(map(lambda x: len(x) + 2, rendered_aliases)) -2 > cols_left:
        # Grouping recovers the initial amount of cols left
        # but requires one more indentation level
        cols_left = initial_cols_left - SPACES_PER_INDENTATION_LEVEL 

        # Group them such that no group goes off screen
        alias_groups = [[]]
        for alias in rendered_aliases:
            current_group_len = sum(map(lambda x: len(x) +2, alias_groups[-1]))

            # If adding this alias and a " ," overflows
            if current_group_len + len(alias) + 2 > cols_left:
                # Make a new group
                alias_groups.append([alias])
            
            # Otherwise add it to the last group
            else:
                alias_groups[-1].append(alias)
        
        import_line = indent(indentation, "import (\n")
        # draw_alias_group takes care of indentation
        alias_groups_lines = ",\n".join(map(lambda x: draw_alias_group(indentation+1, x), alias_groups)) + "\n"
        ending_line = indent(indentation, ")")

        return import_line + alias_groups_lines + ending_line
    else:
        joined_aliases = ", ".join(rendered_aliases)

        rendered_import = f"import {joined_aliases}" 
        return indent(indentation, rendered_import)


def draw_alias_group(indentation, aliases):
    return indent(indentation, ", ".join(aliases))


# Doesn't care about indentaion or cols left, just draws itself
# The parent should take care of that
def render_alias(node, _, __):
    as_str = "" if node.asname is None else f" as {node.asname}"
    return node.name + as_str


def indent(indentation_levels, string):
    return " " * SPACES_PER_INDENTATION_LEVEL * indentation_levels + string


def is_import(node):
    return isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)


def first_matching(iterable, predicate):
    for index, item in enumerate(iterable):
        if predicate(item):
            return index
    return None


def newline_join(iterable): return '\n'.join(iterable) 
