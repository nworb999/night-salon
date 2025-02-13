import asyncio
import json

from utils.logger import logger


async def accept_connection(server_socket):
    loop = asyncio.get_event_loop()
    future = loop.create_task(loop.sock_accept(server_socket))
    return await future


async def receive_data(client_socket, buffer_size=1024):
    loop = asyncio.get_event_loop()
    future = loop.create_task(loop.sock_recv(client_socket, buffer_size))
    return await future


def handle_client_factory(unity_client):
    async def handle_client(client_socket, addr):
        logger.info(f"Accepted connection from {addr}")
        try:
            while True:
                data = await receive_data(client_socket)
                if not data:
                    break  # Client disconnected

                decoded_data = data.decode()

                # Process each newline-separated event
                for raw_event in decoded_data.splitlines():
                    if not raw_event:
                        continue
                    try:
                        event = json.loads(raw_event)
                        event_type = event.get("type")
                        agent_id = event.get("agent_id")
                        event_data = event.get("data")

                        if event_type == "state_change" and agent_id:
                            try:
                                new_state = (
                                    json.loads(event_data)
                                    if isinstance(event_data, str)
                                    else event_data
                                )
                                asyncio.run_coroutine_threadsafe(
                                    unity_client._handle_event(
                                        "state_change", agent_id, new_state
                                    ),
                                    unity_client.loop,
                                )
                            except json.JSONDecodeError as je:
                                logger.error(
                                    f"Failed to parse state data: {je}, raw data: {event_data}"
                                )

                        elif event_type == "position_update":
                            try:
                                position_data = (
                                    json.loads(event_data)
                                    if isinstance(event_data, str)
                                    else event_data
                                )
                                asyncio.run_coroutine_threadsafe(
                                    unity_client._handle_event(
                                        "position_update", agent_id, position_data
                                    ),
                                    unity_client.loop,
                                )
                            except json.JSONDecodeError as je:
                                logger.error(
                                    f"Failed to parse position data: {je}, raw data: {event_data}"
                                )

                        elif event_type == "destination_change" and agent_id:
                            try:
                                destination_data = (
                                    json.loads(event_data)
                                    if isinstance(event_data, str)
                                    else event_data
                                )
                                asyncio.run_coroutine_threadsafe(
                                    unity_client._handle_event(
                                        "destination_change", agent_id, destination_data
                                    ),
                                    unity_client.loop,
                                )
                            except json.JSONDecodeError as je:
                                logger.error(
                                    f"Failed to parse destination data: {je}, raw data: {event_data}"
                                )

                        elif (
                            event_type
                            and event_type in unity_client.event_handlers
                        ):
                            if event_type not in [
                                "state_change",
                                "position_update",
                                "destination_change",
                            ]:
                                asyncio.run_coroutine_threadsafe(
                                    unity_client._handle_event(
                                        event_type, None, event_data
                                    ),
                                    unity_client.loop,
                                )

                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Failed to parse Unity event: {e}, raw data: {raw_event}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing Unity event: {e}", exc_info=True
                        )

        except ConnectionResetError:
            logger.info(f"Client {addr} disconnected")
        except Exception as e:
            logger.error(
                f"Error handling client connection: {e}", exc_info=True
            )
        finally:
            client_socket.close()
            logger.info(f"Connection to {addr} closed")

    return handle_client


async def run_tcp_event_loop(server_socket, unity_client):
    handle_client = handle_client_factory(unity_client)

    async def main():
        loop = asyncio.get_event_loop()
        while True:
            try:
                client_socket, addr = await accept_connection(server_socket)
                loop.create_task(handle_client(client_socket, addr))
            except OSError as e:
                if e.errno == 24:
                    logger.error(
                        "Too many open files. Consider increasing the limit."
                    )
                else:
                    logger.error(f"OSError during accept: {e}")
                break
            except Exception as e:
                logger.error(f"Error accepting connection: {e}", exc_info=True)
                break

    await main()
    server_socket.close()
    logger.info("Server socket closed")
