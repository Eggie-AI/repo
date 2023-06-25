#!/usr/bin/env python3
import json
import socket
import os
import sys
import struct
from argparse import ArgumentParser
from typing import Optional
from joblib import load
from create_models import predict_keys
import time


def connect(socket_path: str) -> socket:
    try:
        os.unlink(socket_path)
    except OSError:
        if os.path.exists(socket_path):
            raise

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        s.bind(socket_path)
    except socket.error as msg:
        print('Bind failed. Error:', str(sys.exc_info()), 'Message:', msg)
        sys.exit()

    s.listen(1)
    return s


def send_message(c: socket, msg: str) -> None:
    msg_size = len(msg)
    c.sendall(struct.pack('I', msg_size))
    c.sendall(msg.encode('utf-8'))


def recv_message(c: socket) -> Optional[str]:
    data = c.recv(4)
    if not data:
        return None
    msg_size = struct.unpack('I', data)[0]
    return c.recv(msg_size, socket.MSG_WAITALL).decode('utf-8')


def parse_args():
    parser = ArgumentParser(description='Predict ML Values for states')
    parser.add_argument('socket_path', type=str, action='store', help='Path to socket lib')
    parser.add_argument('model_path', type=str, action='store', help='Path to the joblib model')
    parser.add_argument('--debug', action='store_true', help='Print debug messages')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if not os.path.exists(args.model_path):
        raise Exception("Invalid model path")

    print(f"Starting server on {args.socket_path}")
    s = connect(args.socket_path)
    model = load(args.model_path)
    print("Model loaded")

    try:
        while True:
            print('Waiting for first message...')
            c, addr = s.accept()
            try:
                while True:
                    if args.debug:
                        print('Waiting...')
                    x = recv_message(c)
                    if not x:
                        print("No more data")
                        break

                    start = time.time_ns()
                    if args.debug:
                        print(f"Received: '{x}'")
                    state_data = json.loads(x)
                    x = []
                    for key in predict_keys:
                        if key not in state_data:
                            raise Exception(f"key '{key}' not in state data")
                        x.append(state_data[key])

                    y = str(int(model.predict([x])[0]))

                    end = time.time_ns()
                    if args.debug:
                        print(f"prediction took: {end - start}*10^-9s")

                    send_message(c, y)
                    if args.debug:
                        print(f"Sent: '{y}'")
            except Exception as e:
                print(f"Exception: {e}")
            finally:
                c.close()
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        s.close()
        os.unlink(args.socket_path)
