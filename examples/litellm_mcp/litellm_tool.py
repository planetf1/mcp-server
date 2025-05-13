import asyncio
import os
import json
import litellm
from litellm import experimental_mcp_client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import tempfile
from colorama import Fore, Style, init

init()  # Initialize colorama

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={
        "GITHUB_PERSONAL_ACCESS_TOKEN": os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "GITHUB_OWNER": os.environ["GITHUB_OWNER"],
        "GITHUB_REPO": os.environ["GITHUB_REPO"],
        "PATH": os.getenv("PATH", default=""),
    },
)


async def run_litellm_tool():
    print(Fore.BLUE + "Setting up MCP tools..." + Style.RESET_ALL)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print(Fore.BLUE + ".. initializing session" + Style.RESET_ALL)
            await session.initialize()
            tools = await experimental_mcp_client.load_mcp_tools(session=session, format="openai")
            print(Fore.GREEN + "MCP TOOLS: " + Style.RESET_ALL, tools)

            messages = [
                {
                    "role": "user",
                    "content": "list the open issues for owner:i-am-bee and repo:beeai-framework",
                }
            ]
            print(Fore.BLUE + "Sending prompt to LLM..." + Style.RESET_ALL)
            llm_response = await litellm.acompletion(
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
                messages=messages,
                tools=tools,
            )
            print(
                Fore.GREEN + "LLM RESPONSE: " + Style.RESET_ALL,
                json.dumps(llm_response, indent=4, default=str),
            )

            tool_calls = llm_response["choices"][0]["message"].get("tool_calls")

            if tool_calls:
                openai_tool = tool_calls[0]
                print(Fore.BLUE + "Calling MCP tool..." + Style.RESET_ALL)
                call_result = await experimental_mcp_client.call_openai_tool(
                    session=session,
                    openai_tool=openai_tool,
                )
                issue_data = json.loads(call_result.content[0].text)

                # Print raw JSON with a separator
                print(Fore.YELLOW + "\n--- Raw JSON Response ---\n" + Style.RESET_ALL)
                print(json.dumps(issue_data, indent=4))
                print(Fore.YELLOW + "--- End Raw JSON ---\n" + Style.RESET_ALL)

                # Extract and print specific fields in a formatted table
                print(Fore.GREEN + "\n--- Formatted Issue Summary ---\n" + Style.RESET_ALL)
                print(
                    Style.BRIGHT + "Issue #".ljust(12) + "Title".ljust(40) + "URL" + Style.RESET_ALL
                )  # Header
                print("-" * 70)  # Separator
                for issue in issue_data:
                    print(
                        f"{str(issue['number']).ljust(12)}{issue['title'].ljust(40)}{issue['html_url']}"
                    )
                print(Fore.GREEN + "--- End Formatted Summary ---\n" + Style.RESET_ALL)

            else:
                print(Fore.YELLOW + "LLM did not use any tools." + Style.RESET_ALL)


if __name__ == "__main__":
    asyncio.run(run_litellm_tool())
