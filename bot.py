import random
from api import Channel, Results


class Languages:
    Eng = "en"
    Fra = "fr"
    Ger = "gr"


# Input messages
class TestRepository:
    def get_topics(self, lang: str):
        return ["Home", "War", "Common"]

    def get_words(self, lang, topic):
        return [("word", "слово"), ("мама", "mother")]


class Context:
    def __init__(self, repository):
        self.channel = Channel()
        self.vocabulary = Vocabulary()
        self.repository = repository
    

def input_language(context):
    _, lang = yield context.channel.read("Какой язык выбрать?", [Languages.Eng, Languages.Fra, Languages.Ger])
    print(f"language: {lang}")
    context.vocabulary.set_lang(lang)
    
    _, direction = yield context.channel.read("Выберите направление перевода:", ["to_rus", "from_rus"])
    print(f"direction: {direction}")
    context.vocabulary.set_direction(direction)
    return input_topic


def input_topic(context):
    vocabulary = context.vocabulary
    topics = context.repository.get_topics(vocabulary.lang)
    _, topic = yield context.channel.read("Доступны следуюшие темы, какую выбрать?", topics)
    print(f"topic: {topic}")
    words = context.repository.get_words(vocabulary.lang, topic)
    vocabulary.set_topic_words(topic, words)
    return QuestionState()

def exit(context):
    yield context.channel.write("Настройки сброшены. Для тренировки введите /start")


class QuestionState:
    commands = ["skip", "hint", "end"]

    def process(self, context):
        vocabulary = context.vocabulary
        task =  vocabulary.get_task()
        if not task:
            yield context.channel.write("В выбранной теме не осталось слов, которых вы не знаете")
            return input_topic

        ans_type, answer = yield context.channel.read(f"Введите перевод слова \"{task.word}\":", QuestionState.commands, True)
        if Results.is_command(ans_type): # we got command here
            if answer == "end":
                return exit
            if answer == "hint":
                yield context.channel.write(self._make_hint(task))
            vocabulary.skip_task()
        else: #we got a text answer here
            if vocabulary.is_valid_answer(answer):
                yield context.channel.write("Верно!") #todo send sticker
                vocabulary.complete_task()
            else:
                yield context.channel.write("Неправильно, попробуйте ещё раз")
        
        return self


    def _make_hint(self, task):
        return f'"{task.word}" переводится "{task.translation}"\n" \
            "[Google переводчик "{task.word}](https://translate.google.com/?hl=ru#" \
            "view=home&op=translate&sl=auto&tl=ru&text={task.foreign})"'

           
class Vocabulary:
    class Task:
        def __init__(self, word, translation, foreign, index):
            self.word = word
            self.translation = translation
            self.foreign = foreign
            self.index = index


    def __init__(self):
        self.lang = None
        self.topic = None
        self.words = None
        self.translation_index = None  # index of word used as translation for word
        self.task = None

    def set_lang(self, lang):
        self.lang = lang

    def set_topic_words(self, topic, words):
        self.topic = topic
        self.words = words

    def set_direction(self, direction):
        self.translation_index = 0 if direction == "a" else 1

    def get_task(self):
        if not self.task:
            self.task = self._create_next_task()
        return self.task

    def skip_task(self):
        self.task = None

    def complete_task(self):
        self.words.pop(self.task.index)
        self.task = None

    def is_valid_answer(self, text: str):
        return self.task.translation.lower() == text.lower()

    def _create_next_task(self):
        if not self.words:
            return None
        i = random.randrange(0, len(self.words))
        pair = self.words[i]
        return Vocabulary.Task(pair[1-self.translation_index],pair[self.translation_index], pair[0], i)
    
