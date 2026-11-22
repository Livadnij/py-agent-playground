import inspect
import typing

TOOLS = {}


TYPE_DESCRIPTIONS = {
    'str': "string",
    'int': "integer",
    'float': "number",
    'bool': "boolean",
    'list': "array",
    'dict': "object",
    'NoneType': "null"
}


def tool(description):
    def decorator(func):
        props = {}
        required = []

        sig = inspect.signature(func)

        for name, param in sig.parameters.items():
            if typing.get_origin(param.annotation) is typing.Annotated:
                raw_info = typing.get_args(param.annotation)
                
                raw_type_hint = raw_info[0].__name__
                type_hint = TYPE_DESCRIPTIONS.get(raw_type_hint)
                annotated_desc = raw_info[1]
            else:
                type_hint = TYPE_DESCRIPTIONS.get(param.annotation.__name__)
                annotated_desc = "unknown"

            default_value = param.default
    
            if default_value is inspect.Parameter.empty:
                required.append(name)
                
            props[name] = {
                'type' : type_hint if type_hint else "unknown",
                'description': annotated_desc
            }

        schema = {
            'type': 'function',
            'function': {
                'name': func.__name__,
                'description':description,
                'parameters': {
                    'type': 'object',
                    'properties': props,
                    'required': required
                },
                
            }
        }
        TOOLS[func.__name__] = {"schema": schema, "function": func}
        return func
    
    return decorator