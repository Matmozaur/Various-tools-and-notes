from concurrent import futures
import time

import grpc
import basic_pb2
import basic_pb2_grpc


class GreeterServicer(basic_pb2_grpc.GreeterServicer):

    def __init__(self):
        self.avg = 0
        self.counter = 0

    def SayHello(self, request, context):
        print("SayHello Request Made:")
        print(request)
        hello_reply = basic_pb2.HelloReply()
        hello_reply.message = f"{request.greeting} {request.name}"

        return hello_reply

    def ParrotSaysHello(self, request, context):
        print("ParrotSaysHello Request Made:")
        print(request)

        for i in range(3):
            hello_reply = basic_pb2.HelloReply()
            hello_reply.message = f"{request.greeting} {request.name} {i + 1}"
            yield hello_reply
            time.sleep(3)

    def ChattyClientSaysHello(self, request_iterator, context):
        delayed_reply = basic_pb2.DelayedReply()
        for request in request_iterator:
            print("ChattyClientSaysHello Request Made:")
            print(request)
            delayed_reply.request.append(request)

        delayed_reply.message = f"You have sent {len(delayed_reply.request)} messages. Please expect a delayed response."
        return delayed_reply

    def InteractingHello(self, request_iterator, context):
        for request in request_iterator:
            print("InteractingHello Request Made:")
            print(request)

            hello_reply = basic_pb2.HelloReply()
            hello_reply.message = f"{request.greeting} {request.name}"

            yield hello_reply

    def AverageStream(self, request_iterator, context):
        print(request_iterator)
        for request in request_iterator:
            print(request)
            l = len(request.table)
            r_avg = sum(request.table) / l
            new_counter = self.counter + l
            self.avg = self.avg * (self.counter/new_counter) + r_avg * (l/ new_counter)
            self.counter = new_counter

            reply = basic_pb2.AverageReply()
            reply.avg = self.avg

            yield reply


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    basic_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port("localhost:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
