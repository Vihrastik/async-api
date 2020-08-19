from bot import TestRepository, input_language, Context
from api import Flow, Channel, Results
import telebot

TOKEN = "123"
bot = telebot.TeleBot(TOKEN)

repository = TestRepository()
user_states = {} # chat id to tuple of request and flow


def _get_read_state(chat_id):
    if chat_id not in user_states:
        return None
    request, _ = user_states.get(chat_id)
    return request if isinstance(request, Channel.ReadRequest) else None


def is_waiting_command(chat_id, command):
    request = _get_read_state(chat_id)
    return request and (command in request.commands)


def is_waiting_message(chat_id):
    request = _get_read_state(chat_id)
    return request and request.allow_text


@bot.message_handler(commands=["start"])
def reset(message):
    chat_id = message.chat.id
    context = Context(repository)
    flow = Flow(input_language, context).run()
    _continue_flow(flow, None)


@bot.callback_query_handler(func=lambda query: is_waiting_command(query.message.chat.id, query.data))
def handle_command(query):
    chat_id = query.message.chat.id
    _, flow = user_states.pop(chat_id)
    _continue_flow(chat_id, flow, Results.make_command(query.data))


@bot.message_handler(func=lambda msg: is_waiting_message(msg.chat.id))
def handle_message(message):
    chat_id = message.chat.id
    _, flow = user_states.pop(chat_id)
    _continue_flow(chat_id, flow, Results.make_text(message.text))


def _continue_flow(chat_id, flow, response):
    try:
        data = response
        while True:
            request = flow.send(data) if data else next(flow)
            if isinstance(request, Channel.WriteRequest):
                _reply(chat_id, request)
                data = None
            elif isinstance(request, Channel.ReadRequest):
                user_states[chat_id] = (request, flow)
                _send_prompt(chat_id, request)
                return
            else:
                t = type(request)
                raise NotImplementedError(f"unknown request type: {t}")
    except StopIteration:
        print("fsm done")


def _reply(chat_id, write_request):
    pass


def _send_prompt(chat_id, read_request):
    pass


bot.polling()