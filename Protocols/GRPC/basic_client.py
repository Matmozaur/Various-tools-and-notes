import basic_pb2_grpc
import basic_pb2
import time
import grpc


def get_client_stream_requests():
    while True:
        name = input("Please enter a name (or nothing to stop chatting): ")

        if name == "":
            break

        hello_request = basic_pb2.HelloRequest(greeting="Hello", name=name)
        yield hello_request
        time.sleep(1)


def get_client_stream_table_requests():
    while True:
        table = input("Please enter a list of numbers : ")

        if table == "END":
            break

        r = basic_pb2.AverageRequest(table=list(map(float, table.split(','))))
        print(r)
        yield r
        time.sleep(1)


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = basic_pb2_grpc.GreeterStub(channel)
        print("1. SayHello - Unary")
        print("2. ParrotSaysHello - Server Side Streaming")
        print("3. ChattyClientSaysHello - Client Side Streaming")
        print("4. InteractingHello - Both Streaming")
        print("5. Average counter")
        rpc_call = input("Which rpc would you like to make: ")

        if rpc_call == "1":
            hello_request = basic_pb2.HelloRequest(greeting="Bonjour", name="YouTube")
            hello_reply = stub.SayHello(hello_request)
            print("SayHello Response Received:")
            print(hello_reply)
        elif rpc_call == "2":
            hello_request = basic_pb2.HelloRequest(greeting="Bonjour", name="YouTube")
            hello_replies = stub.ParrotSaysHello(hello_request)

            for hello_reply in hello_replies:
                print("ParrotSaysHello Response Received:")
                print(hello_reply)
        elif rpc_call == "3":
            delayed_reply = stub.ChattyClientSaysHello(get_client_stream_requests())

            print("ChattyClientSaysHello Response Received:")
            print(delayed_reply)
        elif rpc_call == "4":
            responses = stub.InteractingHello(get_client_stream_requests())

            for response in responses:
                print("InteractingHello Response Received: ")
                print(response)

        elif rpc_call == "5":
            responses = stub.AverageStream(get_client_stream_table_requests())

            for response in responses:
                print("Response Received: ")
                print(response)


if __name__ == "__main__":
    run()
