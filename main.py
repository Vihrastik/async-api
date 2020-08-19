from api import Channel, Results, Flow, Repository, run_flow
from bot import Context, TestRepository, input_language
from console_runner import handle

context = Context(TestRepository())
flow = Flow(input_language, context)
run_flow(flow, handle)