import asyncio

from utu.env import DockerManager, MCPClient

docker_manager = DockerManager()


async def test_mcp():
    try:
        container_info = await docker_manager.start_container("test_11")
        print(f"container_info: {container_info}")
        await asyncio.sleep(5)
        # client = MCPClient(container_info["mcp_url"])
        # # try:
        # #     async with client:
        # #         res = await client.list_tools()
        # #         print(res)
        # # except BaseException as e:
        # #     print(f"async with error: {e}")
        # await client.start()
        # res = await client.list_tools()
        # print(res)
        # await client.cleanup()
        async with MCPClient.get_mcp_client(container_info["mcp_url"]) as client:
            res = await client.list_tools()
            print(res)
            res = await client.call_tool("go_to_url", {"url": "https://github.com/modelcontextprotocol/python-sdk/issues/79"})
            print(res)
    except Exception as e:
        print(f"except: {e}")
    except BaseExceptionGroup as e:
        print(f"BaseExceptionGroup: {e}")
    # finally:
    #     print("finally")
    #     try:
    #         docker_manager.cleanup()
    #     except BaseException as e:
    #         print(f"finally error: {e}")
    #     except BaseExceptionGroup as e:
    #         print(f"BaseExceptionGroup: {e}")

async def test_concurrency():
    try:
        n = 20
        tasks = [docker_manager.start_container(f"test_{i}") for i in range(n)]
        res = await asyncio.gather(*tasks)
        print(res)

        stat = docker_manager.get_all_status()
        print(stat)
    except Exception as e:
        print(e)
    finally:
        docker_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_mcp())
