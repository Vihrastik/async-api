from api import Flow, Channel, Results, run_flow, continue_flow


def handle(request, flow):
    if isinstance(request, Channel.ReadRequest):
        return _read(request)
    if isinstance(request, Channel.WriteRequest):
        return _write(request)
    raise Exception("Unsupported request type: "+type(request))


def _read(request):
    text = request.prompt
    if request.commands:
        cmds = ", ".join(map(lambda x: f"/{x}",request.commands))
        text = text + f" ({cmds}): "
    result = input(text)
    return _parse_result(result, request)


def _write(request):
    print(request.content)


def _parse_result(result, request):
    if result.startswith("/") and result[1:] in request.commands:
        return Results.make_command(result[1:])
    if request.allow_text:
        return Results.make_text(result)
    raise Exception("invalid input: " + result)