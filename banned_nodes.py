import ast

# Those are reported as nodes by ast.iter_child_nodes(parent)
# But cause trouble down the road
# (AttributeErrors when navigating to them)
banned_nodes = [
        ast.Load,
        ast.Store,
        ast.Del,
        ast.AugLoad,
        ast.AugStore,
        ast.Param,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Is,
        ast.IsNot,
        ast.In,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.MatMult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.LShift,
        ast.RShift,
        ast.BitOr,
        ast.BitXor,
        ast.BitAnd,
        ast.FloorDiv,
        ast.And,
        ast.Or,
        ast.Invert,
        ast.Not,
        ast.UAdd,
        ast.USub,
        ]

