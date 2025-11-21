# global variables
from hehbot.env_service import bot, dp, env

# commands
from hehbot.command import BotCommand 

# types
from hehbot.memory import repo_msg, ChatMessage
from hehbot.admin  import repo_staff, StaffPerson
from hehbot.client import repo_user, Person
from hehbot.score_history import repo_score_history, ScoreHistory
import hehbot.gpt

#handlers
from hehbot.slot_machine import handle_slot_machine