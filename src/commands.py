# commands.py
async def cmd_help(client, args):
    for name, (handler, description) in COMMANDS.items():
        print(f'/{name} - {description}')


async def cmd_summary(client, args):
    print(client.summary or 'No summary yet')


async def cmd_compact(client, args):
    await client.compact()


async def cmd_exit(client, args):
    return True  # tells the loop to stop

async def cmd_history(client, args):
    history_lines_list = [f'{item['role']} : {item['content']}' for item in client.history]
    history_transcript = '\n'.join(history_lines_list)
    print(history_transcript)

COMMANDS = {
    'help': (cmd_help, 'show this list'),
    'summary': (cmd_summary, 'print the current summary'),
    'compact': (cmd_compact, 'force compaction now'),
    'history': (cmd_history, 'print the current history'),
    'exit': (cmd_exit, 'quit'),
}