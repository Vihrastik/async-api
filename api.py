import random
import types


class Results:
    Command = "cmd"
    Text = "txt"

    @staticmethod
    def is_command(_type):
        return _type == Results.Command

    @staticmethod
    def make_command(data):
        return (Results.Command, data)

    @staticmethod
    def make_text(data):
        return (Results.Text, data)


class Flow:
    def __init__(self, start_state, context):
        self.state = start_state
        self.context = context

    def process(self):
        state = self.state
        while state:
            run = None
            process = getattr(state, "process", None)
            if process and callable(process):
                run = state.process(self.context)
            elif callable(state):
                run = state(self.context)
            elif isinstance(run, types.GeneratorType):
                run = state
            else:
                t = type(state)
                raise Exception(f"cannot run {t} in flow")

            if isinstance(run, types.GeneratorType):
                try:
                    data = None
                    while True:
                        req = run.send(data) if data else next(run)
                        data = yield req
                except StopIteration as si:
                    state = si.value
            elif callable(run):
                state = run()
            else:
                raise Exception("result is not either generator or function")


def run_flow(flow, handler, *args):
    continue_flow(flow.process(), None, handler, *args)


def continue_flow(flow, response, handler, *args):
    try:
        data = response
        while True:
            request = flow.send(data) if data else next(flow)
            data = handler(request, flow, *args)
    except ExecutionSuspended:
        pass
    except StopIteration:
        print("done")


class ExecutionSuspended(BaseException):
    pass


class Channel:
    class ReadRequest:
        def __init__(self, prompt, commands, allow_text):
            self.prompt = prompt
            self.commands = commands
            self.allow_text = allow_text

    class WriteRequest:
        def __init__(self, content):
            self.content = content

    def read(self, prompt: str, commands, allow_text = False):
        return Channel.ReadRequest(prompt, commands, allow_text)

    def write(self, message: str):
        return Channel.WriteRequest(message)


class Repository:
    def get_topics(self, lang):
        raise NotImplementedError()

    def get_words(self, lang, topic):
        raise NotImplementedError()