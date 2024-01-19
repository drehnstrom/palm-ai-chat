from flask import Flask, render_template, request, session
import os
import yaml
import vertexai
from vertexai.preview.language_models import ChatModel, InputOutputTextPair, ChatMessage

app = Flask(__name__)
app.secret_key = "session_key1"

def get_config_value(config, section, key, default=None):
    """
    Retrieve a configuration value from a section with an optional default value.
    """
    try:
        return config[section][key]
    except:
        return default
        
with open('config.yaml') as f:
    config = yaml.safe_load(f)

TITLE = get_config_value(config, 'app', 'title', 'Ask Google')
SUBTITLE = get_config_value(config, 'app', 'subtitle', 'Your friendly Bot')
CONTEXT = get_config_value(config, 'palm', 'context', 'You are a bot who can answer all sorts of questions')
BOTNAME = get_config_value(config, 'palm', 'botname', 'Google')
TEMPERATURE = get_config_value(config, 'palm', 'temperature', 0.8)
MAX_OUTPUT_TOKENS = get_config_value(config, 'palm', 'max_output_tokens', 256)
TOP_P = get_config_value(config, 'palm', 'top_p', 0.8)
TOP_K = get_config_value(config, 'palm', 'top_k', 40)

EXAMPLES=get_config_value(config, 'palm', 'examples', [])
examples = [InputOutputTextPair(input_text=k, output_text=v) for k,v in EXAMPLES.items()]
     
@app.route("/", methods = ['POST', 'GET'])
def main():
    if request.method == 'POST':
        input = request.form['input']
        if input > " ":
            response = get_response(input)
        else:
            response = "Ask me something"
        input = ""
    else: 
        input = ""
        session.pop('chat_history', None)        
        response = get_response("Who are you and what can you do?")


    model = {"title": TITLE, "subtitle": SUBTITLE, "botname": BOTNAME, "message": response, "input": input, "history": session["chat_history"]}
    return render_template('index.html', model=model)


def get_response(input):
    vertexai.init(location="us-central1")
    chat_model = ChatModel.from_pretrained("chat-bison@001")
    parameters = {
        "temperature": TEMPERATURE,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "top_p": TOP_P,
        "top_k": TOP_K
     }

    if 'chat_history' in session:
        chat_history = [ChatMessage(content=items["content"], author=items["author"]) for items in session["chat_history"]]
        parameters["message_history"] = chat_history

    chat = chat_model.start_chat(context=CONTEXT, examples=examples,  **parameters)
    response = chat.send_message(input)
    session["chat_history"] = chat.message_history
    return response.text
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
