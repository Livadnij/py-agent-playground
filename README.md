# py-agent-playground

An experimental terminal chat client for locally hosted language models, built around LM Studio. The project explores what a minimal LLM client can do. Its central focus is context management, meaning how a long conversation can be kept inside the model's context window through automatic summarization.

## Features

- Multi-turn chat in the terminal with full conversation history
- Tool calling. The model can request tools, the client runs them and returns the results to the model, with a configurable limit on rounds per reply
- Tools defined with a `@tool` decorator that builds the function schema from type hints and registers the tool
- Agent roles. Each role has its own model, system prompt and list of tools, and the runner only executes tools the role was given
- Sandboxed filesystem tools that can list directories and read text files inside configured folders only
- Automatic context compaction. When the conversation fills a configurable share of the loaded context window, the older half of the history is summarized by the model and replaced with that summary
- Token usage printed after every reply, colored by how full the context is
- Slash commands for inspecting and controlling the session
- Typed settings loaded from a `.env` file with pydantic-settings
- Pydantic models for the parts of the LM Studio responses the code reads

## How it works

Every request to the chat completions endpoint carries the system prompt, the current summary if there is one, the recent history and the new message. After each reply the client works out how much of the loaded context is used. When that crosses the threshold, it calls the model again with a summarizer prompt. The new summary is merged with any previous one, stored separately from the history, and added to the system message on later requests. The context length is read from LM Studio's native models endpoint, so the model has to be loaded.

When tools are provided, their schemas are sent with every request. If a reply asks for tool calls, the client runs each one through a tool runner, appends the assistant message and the tool results, and sends the request again. This repeats until the model answers without asking for a tool or the round limit is reached. A turn is added to the history only after it ends with a final answer, and compaction always cuts the history at a user message, so a tool exchange is never split.

Tools are plain async functions marked with the `@tool` decorator. The decorator reads the parameter names, types and `Annotated` descriptions and builds the JSON schema, then stores the function in a registry. A role in `src/roles.py` names the tools it may use, and the client receives only those schemas plus a runner that refuses any other name. Filesystem tools resolve every path and reject anything outside `LLM_ALLOWED_DIRECTORIES`. Large files are cut to a configurable size by keeping the first and last half, with a marker that says how much was left out.

## Adding a tool

Write an async function in a module under `src/tools/`, mark it with `@tool` and describe each parameter with `Annotated`.

    @tool('Returns the content of a text file.')
    async def read_file(path: Annotated[str, 'Absolute path of the file to read']):
        ...

Import the module in `src/tools/__init__.py` so the decorator runs, then add the tool name to a role in `src/roles.py`. A name that is not registered is reported at startup.

## Requirements

- Python 3.12 or newer
- uv
- LM Studio with the local server running and a model loaded

## Setup

```
uv sync
```

Copy `.env.example` to `.env` in the project root and fill in the values. The values below are examples.

```
LLM_BASE_URL=http://127.0.0.1:1234
LLM_API_KEY=your-lm-studio-api-token
LLM_TIMEOUT=300
LLM_CONCURENT_REQ=1
LLM_ALLOWED_DIRECTORIES=["D:/code/python/py-agent-playground/playground"]
PRODUCTION=false
```

`LLM_ALLOWED_DIRECTORIES` is a JSON array of folders the filesystem tools may access. The model is chosen per role in `src/roles.py`.

`LLM_BASE_URL` is the server address without a path, because the client adds the `/v1/...` and `/api/v1/...` routes itself.

Optional settings and their defaults.

| Setting                       | Default | Meaning                                  |
| ----------------------------- | ------- | ---------------------------------------- |
| LLM_SUMMARY_THRESHOLD_PERCENT | 75      | Context usage at which compaction starts |
| LLM_SUMMARY_MAX_TOKENS        | 2000    | Token limit for the summarizing request  |
| LLM_SUMMARY_TEMPERATURE       | 0.2     | Temperature used for summaries           |
| LLM_COMPLETION_TEMPERATURE    | 0.7     | Temperature used for normal replies      |
| LLM_MAX_TOOL_ROUNDS           | 10      | Maximum tool rounds in a single reply    |
| LLM_MAX_FILE_SIZE             | 8192    | Bytes read from a file before it is cut  |

## Usage

```
uv run main.py
```

Type a message and press Enter. Any line that starts with `/` is a command.

| Command  | Description               |
| -------- | ------------------------- |
| /help    | Show the list of commands |
| /summary | Print the current summary |
| /compact | Force compaction now      |
| /history | Print the current history |
| /exit    | Quit                      |

After each reply the client prints the number of tokens used and the percentage of the context window. The line is green below 37 percent, yellow up to 70 percent and red above that.

## Project structure

```
main.py              entrypoint, opens the HTTP client and starts the chat loop
src/
  commands.py        slash command registry
  config.py          settings loaded from .env
  factory.py         builds an LLMClient for a role
  repl.py            input loop, command dispatch and usage output
  roles.py           model, system prompt and tools for each role
  startup.py         checks that every tool named in a role is registered
  utils.py           terminal colors and message formatting
  llm/
    client.py        LLMClient with history, compaction and usage tracking
    transport.py     thin async GET and POST helpers on httpx
    schema.py        pydantic models for LM Studio responses
    prompts.py       summarizer prompt and summary marker
  tools/
    registry.py      TOOLS registry and the @tool decorator
    builder.py       turns tool names into schemas
    runner.py        executes an allowed tool call by name
    basic.py         simple built-in tools
    filesystem.py    sandboxed list_directory and read_file
```
