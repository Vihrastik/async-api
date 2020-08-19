from http.server import BaseHTTPRequestHandler, HTTPServer
from bot import TestRepository, Context, input_language
from api import Flow, Channel, Results, continue_flow, run_flow, ExecutionSuspended

USER_ID = 1
user_states = {} 
repository = TestRepository()


class Handler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()

    def do_GET(self):
        self._set_response()
        parts = str(self.path)[1:].split('/')
        if len(parts) != 2:
            return
        _type, value = parts
        if _type == "cmd":
            self.process_command(value)
        elif _type =="msg":
            self.process_message(value)
        else:
            print("not supported command")

    def process_command(self, command):
        if command == "start":
            context = Context(repository)
            run_flow(Flow(input_language, context), self._handle, USER_ID)
        elif USER_ID in user_states and command in user_states[USER_ID][0].commands:
            _, flow = user_states.pop(USER_ID)
            continue_flow(flow, Results.make_command(command), self._handle, USER_ID)
        else:
            print("unknown command: " + command)

    def process_message(self, message):
        print("processing message: " + message)
        if USER_ID in user_states and user_states[USER_ID][0].allow_text:
            _, flow = user_states.pop(USER_ID)
            continue_flow(flow, Results.make_text(message), self._handle, USER_ID)
        else:
            print("message is not allowed in current state")

    def _handle(self, request, flow, user_id):
        if isinstance(request, Channel.ReadRequest):
            self._send_read(request, flow, user_id)
        elif isinstance(request, Channel.WriteRequest):
            self.wfile.write(request.content.encode("utf-8"))
        else:
            raise Exception("not supported operation")
    
    def _send_read(self, request, flow, user_id):
        text = request.prompt
        if request.commands:
            cmds = ", ".join(map(lambda x: f"<a href='http://localhost:8080/cmd/{x}'>{x}</a>", request.commands))
            text = text + f" ({cmds}): "
        self.wfile.write(text.encode("utf-8"))
        user_states[user_id] = (request, flow)
        raise ExecutionSuspended()

    
address = ('',8080)
httpd = HTTPServer(address, Handler)
try:
    print("running server")
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
print("done")


