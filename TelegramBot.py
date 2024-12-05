import telebot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup
import config_teleg # En este script tengo la configuración acerca del token necesario de Telegram
import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model


############################ Parte de inteligencia IA para respuestas Text ###############################

lemmatizer = WordNetLemmatizer()

#Importamos los archivos generados en el código anterior
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_model.h5')

#Pasamos las palabras de oración a su forma raíz
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

#Convertimos la información a unos y ceros según si están presentes en los patrones
def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i]=1
                if True:
                    print ("found in bag: %s" % w)
    print(bag)
    return np.array(bag)

#Predecimos la categoría a la que pertenece la oración
def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    max_index = np.where(res ==np.max(res))[0][0]
    category = classes[max_index]
    return category

#Obtenemos una respuesta aleatoria
#Revisar porque es diferente al visto en la web
def get_response(tag, intents_json):
    list_of_intents = intents_json['intents']
    result = ""
    for i in list_of_intents:
        if i["tag"]==tag:
            result = random.choice(i['responses'])
            break
    return result

def respuesta(message):
    ints = predict_class(message)
    res = get_response(ints, intents)
    return res


##############################################################################################################

# Se inicializa el bot con el token de Telegram proporcionado (guardado en otro script externo)
bot = telebot.TeleBot(config_teleg.TELEGRAM_TOKEN)

# Se define un gestor de mensajes para los comandos /start y /help.
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        """
    Hola, soy tu primer bot, estos son los comandos disponibles:
    \n /count - contar palabras o caracteres de un texto
    \n /start - mensaje de bienvenida
    """,
    )

# Definir un manejador de mensajes para el comando /count
@bot.message_handler(commands=["count"])
def count(message):
    # Crear un teclado personalizado con opciones para contar palabras o caracteres
    board = ReplyKeyboardMarkup(
        row_width=2, resize_keyboard=True, one_time_keyboard=True #resize_keyboard es para que los teclados se adapten a diferentes dispositivos
    )                                                             #one_time_keyboard es para que una vez se conteste el teclado se esconda
    board.add(KeyboardButton("Contar palabras"), KeyboardButton("Contar caracteres"))
    # Envíar un mensaje para elegir qué contar y registrar el manejador del siguiente paso
    bot.send_message(message.chat.id, "Elige qué quieres contar: ¿contar texto o contar palabras?", reply_markup=board)
    bot.register_next_step_handler(message, handle_count_choice)

def handle_count_choice(message):
    # Comprobar la elección del usuario y proceder con la función correspondiente
    if message.text.lower() == "contar palabras":
        bot.send_message(
            message.chat.id, "Envía el texto del que deseas contar palabras"
        )
        bot.register_next_step_handler(message, count_words)
    elif message.text.lower() == "contar caracteres":
        bot.send_message(
            message.chat.id, "Envía el texto del que deseas contar caracteres"
        )
        bot.register_next_step_handler(message, count_characters)

# Función de contar palabras
def count_words(message):
    words = message.text.split()
    word_count = len(words)
    bot.reply_to(message, f"El texto tiene {word_count} palabras")

# Función de contar caracteres
def count_characters(message):
    char_count = len(message.text)
    bot.reply_to(message, f"El texto tiene {char_count} caracteres")


# Definir un gestor de mensajes para textos generales, donde responderá utilizando IA
@bot.message_handler(content_types=["text"])
def hola(message):
    bot.send_message(
        message.chat.id,
        respuesta(message.text.lower()),
    )



# Empezar a recibir mensajes
bot.polling()