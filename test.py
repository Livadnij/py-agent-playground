import asyncio
import inspect
import typing

from src.startup import startup
from src.tools.filesystem import list_directory

TYPE_DESCRIPTIONS = {
    'str': "string",
    'int': "number",
    'float': "floating-point number",
    'bool': "boolean",
    'list': "array"
}


def sync_main():
    startup()

    # print(typing.get_args(typing.get_type_hints(list_directory, include_extras=True)['path'])[1])
    
    # print(typing.get_type_hints(temp, include_extras=True))

    sig = inspect.signature(list_directory)
    for name, param in sig.parameters.items():
        print(param)
        default_value = param.default
        raw_type_hint = typing.get_args(param.annotation)

        type_hint = raw_type_hint[0].__name__
        annotated_desc = raw_type_hint[1]

        print(name, default_value, TYPE_DESCRIPTIONS[type_hint], annotated_desc)


async def async_main():
    print("hello world")

if __name__ == "__main__":
    sync_main()
    # asyncio.run(async_main())