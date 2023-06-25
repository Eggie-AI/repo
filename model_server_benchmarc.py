# benchmarc of the unix sockets model server protocol

import os
import socket
from model_server import connect, send_message, recv_message, predict_keys
from matplotlib import pyplot as plt
from typing import Callable, List, Dict
from argparse import ArgumentParser, Namespace
from time import time_ns, sleep
from multiprocessing import Process

POLL_TIMEOUT_SECONDS = 0.2

def main():
    parser = ArgumentParser(description='Benchmark model server')
    parser.add_argument('-s', '--socket_path', type=str, action='store', help='Path to socket lib', default='/tmp/model_server')
    parser.add_argument('-m', '--message_size', type=int, nargs='+', action='store', help='Size of message to send', default=[10, 100, 1000])
    parser.add_argument('-n', '--num_messages', type=int, action='store', help='Number of messages to send', default=10_000)
    parser.add_argument('-p', '--plot-dir', type=str, action='store', help='Directory to save plots', default='plots')
    parser.add_argument('-w', '--warmup-messages', type=int, action='store', help='Number of messages to send before benchmarking', default=10_000)
    args = parser.parse_args()

    MAX_MESSAGE_SIZE = 0xffffffff
    for size_bytes in args.message_size:
        if size_bytes > MAX_MESSAGE_SIZE:
            raise Exception(f"Message size {size_bytes} bytes is too large")

    print(f"Running benchmarks with {args.num_messages} messages")
    server_process = Process(target=server_fn, args=(args.socket_path, 1))
    server_process.start()

    os.makedirs(args.plot_dir, exist_ok=True)

    args.message_size.sort()

    response_times_ns = []
    for size_bytes in args.message_size:
        print(f"Running benchmark with message size {size_bytes} bytes")
        avg_response_time_ns = sum(run_benchmarc(args.socket_path, args.num_messages, args.warmup_messages, size_bytes)) / args.num_messages
        response_times_ns.append(avg_response_time_ns)

    plt.rcParams.update({
        'font.size': 18
    })

    # plt.title(f"Average latency and message size ({args.num_messages} samples)")
    plt.xlabel("Message size (bytes)")
    plt.ylabel("Latency (ms)")
    plt.xticks(args.message_size)
    plt.xscale('log', base=10)
    plt.plot(args.message_size, [t / 1e6 for t in response_times_ns], marker='o')
    plt.tight_layout()
    plt.savefig(os.path.join(args.plot_dir, f"protocol-benchmark-{args.num_messages}.svg"))
    plt.clf()

    server_process.terminate()
    server_process.join()



def server_fn(socket_path: str, response_size_bytes: int):
    response = 'a' * response_size_bytes
    s_server = connect(socket_path)

    try:
        while True:
            # allow client to connect
            c, _ = s_server.accept()

            try:
                # respond to all messages
                while True:
                    message = recv_message(c)
                    if not message:
                        break
                    send_message(c, response)
            finally:
                c.close()
    finally:
        s_server.close()
        os.unlink(socket_path)


def create_client(socket_path: str):
    # wait for the server to start
    while not os.path.exists(socket_path):
        sleep(POLL_TIMEOUT_SECONDS)

    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    for _ in range(5):
        try:
            c.connect(socket_path)
            break
        except ConnectionRefusedError:
            sleep(POLL_TIMEOUT_SECONDS)
            continue
    else:
        # could not connect
        raise Exception("Could not connect to server")

    return c


def run_benchmarc(socket_path: str, num_messages: int, num_warmup_messages: int, message_size_bytes: int) -> List[float]:
    c = create_client(socket_path)

    try:
        response_times_ns: List[float] = []
        message = 'a' * message_size_bytes

        for _ in range(num_warmup_messages):
            send_message(c, message)
            recv_message(c)

        for _ in range(num_messages):
            start_time = time_ns()

            # client sends message
            send_message(c, message)

            # server receives message
            # server sends response

            # client receives response
            recv_message(c)

            end_time = time_ns()
            response_times_ns.append(end_time - start_time)

        return response_times_ns
    finally:
        c.close()


if __name__ == "__main__":
    main()
