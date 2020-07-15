import renderers.standard


def render_view(tree, selected_node):
    """Shows the ast with the current_node selected. This renderer
    can be altered according to the user's preferences about how
    the code should look like (Like indentation, casing, etc),
    because those are not properties of the code, just of the render.
    Doesn't need to return valid python code, just readable code."""
    
    return renderers.standard.render_view(tree, selected_node)


def render_standard(tree):
    """Render the ast in the most standard python. Should not be 
    altered by the user."""

    return renderers.standard.render_standard(tree)


