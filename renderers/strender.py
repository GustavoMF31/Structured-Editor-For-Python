import ast

SPACES_PER_INDENTATION_LEVEL = 4


def render_view(tree, selected_node, window_width):
    return render(tree, cols_left=window_width)


def render(node, indentation_spaces=0, cols_left=80):
    class_name = type(node).__name__
    render_function = globals().get('render_' + class_name, not_implemented_render)

    # indentation is how many levels indented the node should draw itself
    # cols-left is the amount of room it will have left on the line to draw itself
    # given that it will draw the indentation first
    return render_function(node, indentation_spaces, cols_left)


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
    cols_left = cols_left - len(import_str)

    full_import = ( import_str 
                    + render_aliases(node.names, indentation, initial_cols_left, cols_left)
                  )

    return indent(indentation, full_import)


def render_ImportFrom(node, indentation, cols_left):
    initial_cols_left = cols_left
    # Default level to 0
    level = node.level if node.level is not None else 0 

    from_str = "from "
    module_str = "." * level + (node.module if node.module is not None else "")
    import_str = " import "

    cols_left = cols_left - len(from_str + module_str + import_str)
    aliases_str = render_aliases(node.names, indentation, initial_cols_left, cols_left)

    return from_str + module_str + import_str + aliases_str


def render_aliases(aliases, indentation, initial_cols_left, cols_left):
     
    rendered_aliases = list(map(render, aliases))

    # len + 2 because of the ", " in between
    # Except for the last one (so -2 in the end)
    if not sum(map(lambda x: len(x) + 2, rendered_aliases)) -2 > cols_left:
        # If drawing all of them doesn't go off screen, just render them inline
        return render_simple_group(indentation, rendered_aliases)

    # Grouping recovers the initial amount of cols left
    # but requires one more indentation level
    cols_left = initial_cols_left - SPACES_PER_INDENTATION_LEVEL 

    # Group them such that no group goes off screen
    alias_groups = [[rendered_aliases[0]]]
    for alias in rendered_aliases[1:]:
        current_group_len = sum(map(lambda x: len(x) +2, alias_groups[-1]))

        # If adding this alias and a " ," overflows
        if current_group_len + len(alias) + 2 > cols_left:
            # Make a new group
            alias_groups.append([alias])
        
        # Otherwise add it to the last group
        else:
            alias_groups[-1].append(alias)
    
    # render_simple_group takes care of indentation
    return "(\n" + ",\n".join(map(
                lambda x: render_simple_group(indentation+SPACES_PER_INDENTATION_LEVEL, x),
                alias_groups)
            ) + "\n)" 


def render_simple_group(indentation_spaces, group):
    return indent(indentation_spaces, ", ".join(group))

# Doesn't care about indentaion or cols left, just draws itself
# The parent should take care of that
def render_alias(node, _, __):
    as_str = "" if node.asname is None else f" as {node.asname}"
    return node.name + as_str


def indent(indentation_spaces, string):
    return " " * indentation_spaces + string


def is_import(node):
    return isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)


def first_matching(iterable, predicate):
    for index, item in enumerate(iterable):
        if predicate(item):
            return index
    return None


def newline_join(iterable): return '\n'.join(iterable) 
