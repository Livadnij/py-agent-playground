import asyncio
import logging
import os
from pathlib import Path
from typing import Annotated

from src.tools.registry import tool
from src.config import settings


def create_divider (omitted: int) : return f'\n\n---file exceeds limit. limit was divided and split between first and last half. {omitted} bytes omitted---\n\n'

def resolve_allowed_path(raw_path: str) -> Path|None :
    path = Path(raw_path).resolve()

    for raw_directory in settings.LLM_ALLOWED_DIRECTORIES:
        directory = Path(raw_directory).resolve()

        is_allowed = path.is_relative_to(directory)

        if is_allowed : return path
    return None


@tool(f'Lists the files and folders inside a directory. Allowed directories are {settings.LLM_ALLOWED_DIRECTORIES}.')
async def list_directory(
    path: Annotated[str, "Absolute path of the directory to list"]
):

    resolved_path = resolve_allowed_path(path)
    if(not resolved_path) : 
        return f"Path is not allowed.\nAllowed path are:\n{",\n".join(settings.LLM_ALLOWED_DIRECTORIES)}"
    elif (not resolved_path.exists()) :
        return "Path is allowed, but destination folder does not exist."
    elif (not resolved_path.is_dir()) :
        return "Path is allowed, but it point to the file instead of directory."

    ls = []

    for item in resolved_path.iterdir():
        ls.append(item.as_posix())
 
    return ",\n".join(ls)

@tool("Returns content of the file based on path provided. Use to read files.")
async def read_file(
    path: Annotated[str, "Absolute path of the file to read"]
):
    resolved_path = resolve_allowed_path(path)
    if(not resolved_path) : 
        return f"Path is not allowed.\nAllowed path are:\n{",\n".join(settings.LLM_ALLOWED_DIRECTORIES)}"
    elif (not resolved_path.exists()) :
        return "Path is allowed, but destination file does not exist"
    elif (resolved_path.is_dir()) :
            return "Path is allowed, but it point to the directory instead of file."

    try:
        with resolved_path.open('rb') as f:
            chunk = f.read(8192)
            if b'\x00' in chunk : 
                return f"file '{resolved_path.as_posix()}' appears to be binary and cannot be read as text."
    except Exception as e:
            logging.exception(f'Unhandled error: {e}')
            return "Unhandled error happened."
    
    try:
        file_length = resolved_path.stat().st_size
        if file_length == 0:
            return f"File '{resolved_path.as_posix()}' is empty."
        if (file_length > settings.LLM_MAX_FILE_SIZE):
            half_limit = settings.LLM_MAX_FILE_SIZE // 2

            with resolved_path.open('rb') as f:
                raw_head = f.read(half_limit)
                f.seek(-half_limit, os.SEEK_END)
                raw_tail = f.read()

            omitted = file_length - 2 * half_limit

            head = raw_head.decode('utf-8', errors='replace')
            tail = raw_tail.decode('utf-8', errors='replace')
            content = head + create_divider(omitted) + tail
        else:
            with resolved_path.open('rb') as f:
                raw_content = f.read(-1)
            content = raw_content.decode('utf-8', errors='replace')
        return content
    except Exception as e:
        logging.exception(f'Unhandled error: {e}')
        return "Unhandled error happened."

    

# @tool('Returns a list of strings representing allowed directories. Use to acknowledge allowed directories before listing.')
# def list_allowed_directories():
#     return f"Allowed path are:\n{",\n".join(ALLOWED_DIRECTORIES)}"



async def main():
    print(await list_directory("D:/code/python/py-agent-playground/playground"))

if __name__ == "__main__":
    asyncio.run(main())