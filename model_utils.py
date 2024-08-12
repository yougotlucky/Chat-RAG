import dotenv
from chat import create_chat_engine

dotenv.load_dotenv()


class ModelManager:
    def __init__(self):
        self.selected_model = "codestral:latest"
        self.model_temp = .75
        self.chat_engine = create_chat_engine(self.selected_model, self.model_temp)

    def process_input(self, message):
        try:
            response = self.chat_engine.chat(message)
            return str(response)
        except Exception as e:
            return f"Error: {str(e)}"

    def update_model(self, model):
        self.selected_model = model
        self.reset_chat_engine()

    def update_temperature(self, temperature):
        self.model_temp = temperature
        self.reset_chat_engine()

    def reset_chat_engine(self):
        self.chat_engine = create_chat_engine(self.selected_model, self.model_temp)
