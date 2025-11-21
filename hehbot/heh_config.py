import json, os
from hehbot.env_service import env

class HehConfig:
    def __init__(self, config_file='{}/config.json'.format(env.data_path)):
        self.config_file = config_file
        self.config = {}

    def get(self, key):
        value = self.config.get(key, None)
        self.save_to_file()  # Зберігати конфігурацію після кожного доступу до неї
        return value

    def set(self, key, value):
        self.config[key] = value
        self.save_to_file()

    def remove(self, key):
        if key in self.config:
            del self.config[key]
            self.save_to_file()

    def save_to_file(self):
        with open(self.config_file, 'w') as file:
            json.dump(self.config, file, indent=4)

    def load_from_file(self):
        try:
            with open(self.config_file, 'r') as file:
                self.config = json.load(file)
        except FileNotFoundError:
            self.config = {}
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as file:
                json.dump(self.config, file)
        except json.JSONDecodeError:
            self.config = {'chackpot_chance': 100, 'tg_bet_active': False, 'ds_bet_active': False}
            
    def __str__(self):
        return str(self.config)
    
heh_config = HehConfig()
heh_config.load_from_file()
heh_config.save_to_file()
heh_config.set('tg_bet_active', False)
heh_config.set('ds_bet_active', False)