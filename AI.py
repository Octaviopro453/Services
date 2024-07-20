from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, Conversation, GPT2LMHeadModel, GPT2Tokenizer
import torch

app = FastAPI()

# Configura los pipelines de diálogo
VALID_MODELS = {
    'microsoft/DialoGPT-medium': pipeline('conversational', model='microsoft/DialoGPT-medium'),
    'microsoft/DialoGPT-small': pipeline('conversational', model='microsoft/DialoGPT-small'),
    'microsoft/DialoGPT-large': pipeline('conversational', model='microsoft/DialoGPT-large'),
}

# Configura los modelos GPT-2
GPT2_MODELS = {
    'gpt2': {
        'model': GPT2LMHeadModel.from_pretrained('gpt2'),
        'tokenizer': GPT2Tokenizer.from_pretrained('gpt2')
    },
    'gpt2-medium': {
        'model': GPT2LMHeadModel.from_pretrained('gpt2-medium'),
        'tokenizer': GPT2Tokenizer.from_pretrained('gpt2-medium')
    },
    'gpt2-large': {
        'model': GPT2LMHeadModel.from_pretrained('gpt2-large'),
        'tokenizer': GPT2Tokenizer.from_pretrained('gpt2-large')
    },
    'gpt2-xl': {
        'model': GPT2LMHeadModel.from_pretrained('gpt2-xl'),
        'tokenizer': GPT2Tokenizer.from_pretrained('gpt2-xl')
    },
}

class ChatRequest(BaseModel):
    model: str
    msg: str
    context: str

@app.get("/")
def on_router():
    return "200 OK"

@app.post("/api/ai/")
async def chat(request: ChatRequest):
    model_name = request.model
    
    if model_name in VALID_MODELS:
        # Configura el contexto de la conversación para modelos de diálogo
        conversation = Conversation(request.context)
        conversation.add_user_input(request.msg)
        chatbot = VALID_MODELS[model_name]
        response = chatbot(conversation)
        response_text = response.generated_responses[-1]
        return {"response": response_text}
    
    elif model_name in GPT2_MODELS:
        # Configura el contexto para modelos GPT-2
        tokenizer = GPT2_MODELS[model_name]['tokenizer']
        model = GPT2_MODELS[model_name]['model']
        inputs = tokenizer.encode(request.context + " " + request.msg, return_tensors='pt')
        outputs = model.generate(inputs, max_length=150, num_return_sequences=1, no_repeat_ngram_size=2, early_stopping=True)
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return {"response": response_text}
    
    else:
        # Si el modelo no es válido, devuelve una lista de modelos válidos
        return {"error": "Modelo no válido", "valid_models": list(VALID_MODELS.keys()) + list(GPT2_MODELS.keys())}
