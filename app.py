from flask import Flask, request, jsonify
from flask_cors import CORS
import replicate
import base64
import json
import requests
import os
import time
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv


app = Flask(__name__)
CORS(app)
OUTPUT_DIRECTORY = "output"

load_dotenv()
print("FLASK_ENV:", os.environ.get('FLASK_ENV'))
OPENAI_KEY = os.environ.get('OPENAI_KEY')


def is_development_mode():
    """Check if the application is running in development mode."""
    return os.environ.get('FLASK_ENV') == 'development'


def download_image(image_url):
    """Downloads an image from a given URL and returns its content."""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        app.logger.error(f"Error downloading image from {image_url}: {e}")
        return None


def save_image_locally(image_content, seed):
    """Saves the image locally in development mode."""
    ensure_output_directory_exists()
    filename = f"{OUTPUT_DIRECTORY}/image-seed-{seed}-{time.strftime('%Y%m%d-%H%M%S')}.png"
    with open(filename, 'wb') as file:
        file.write(image_content)
    app.logger.info(f"Image saved locally: {filename}")


def ensure_output_directory_exists():
    """Ensures that the output directory exists."""
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)


def process_scene_prompt_dali(prompt):
    """Processes a scene prompt with dali."""
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        response = client.images.generate(
          model="dall-e-3",
          prompt=prompt,
          size="1024x1024",
          quality="standard",
          n=1)

        if isinstance(response.data, list) and len(response.data) > 0:
            image_url = response.data[0].model_dump()["url"]
            image_content = download_image(image_url)
            if image_content:
                if is_development_mode():
                    save_image_locally(image_content, seed)
                encoded_image = base64.b64encode(image_content).decode('utf-8')
                return encoded_image
            else:
                return None
        else:
            app.logger.error("Unexpected output format: {}".format(output))
            return None
    except Exception as e:
        app.logger.error(f"Error in processing scene prompt: {e}")
        return None


@app.route('/generate-image', methods=['POST'])
def generate_image():
    """Endpoint to generate images based on prompts."""
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    seed_values = [12345, 67890]  # Example seeds
    images = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_scene_prompt, prompt, seed)
                   for seed in seed_values]
        for future in as_completed(futures):
            result = future.result()
            if result:
                images.append(result)
            else:
                return jsonify({"error": "Error generating image"}), 500

    return jsonify({"data": {"images": images}})

@app.route('/generate-text', methods=['POST'])
def generate_text():
  """Endpoint to generate text based on prompts."""
  data = request.json
  prompt = data.get('prompt')
  if not prompt:
    return jsonify({"error": "No prompt provided"}), 400

  client = OpenAI(api_key=OPENAI_KEY)

  response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "You are a dungeons and dragons dungeon master."},
      {"role": "user", "content": "Make a quest where the ultimate prize is a treasure chest.  The quest is presented in a choose your own adventure style adventure.  For each step, present a scenario and end with a question and 4 choices.  Only generate one question at a time and I will let you know how they answered."},
    ]
  )

  text = []
  print(response)
  text.append(response.choices[0].message.content)

  return jsonify({"data": {"text": text}})

@app.route('/generate-text-and-image', methods=['POST'])
def generate_text_and_image():
  """Endpoint to generate images based on prompts."""
  form = request.json

  oldScenarios = form.get('oldScenarios', [])
  oldQuestions = form.get('oldQuestions', [])
  oldChoices = form.get('oldChoices', [])
#  print(oldScenarios)
#  print(oldQuestions)
#  print(oldChoices)

  choice = form.get('choice')
  if choice:
    oldChoices.append(choice)

  client = OpenAI(api_key=OPENAI_KEY)

  messages = []
  messages.append({"role": "system", "content": "You are a dungeons and dragons Dungeon Master that outputs JSON."})
  messages.append({"role": "user", "content": "Make a dungeons and dragons style quest where the ultimate prize is a treasure chest.  The quest is presented in a 'choose your own adventure' style. Each scenario will present a question to the user and have only 2 possible answers to choose from. These answers can be detailed but limited to one sentence. The scenario will also be illustrated using dali so make the scenario a two sentence descriptive image prompt. Only generate one scenario and question at a time. Have the story end within 3 turns where the ending is either getting the treasure or dying.  Only provide compliant JSON responses with the scenario stored in a name 'scenario', the question in a name 'question' and the choices in a list with the key 'choices' and the value of what the sentence-long choice is, do NOT make the key anyhting else other than 'choices'. The key of the choices list MUST BE 'choices' AND NOTHING ELSE. Those names must always be present even if the values are empty.  For the final scenario it is okay for the `question` and `choices` names to be empty lists."})

  for i in range(len(oldScenarios)):
    messages.append({"role": "assistant", "content": oldScenarios[i]})
    messages.append({"role": "assistant", "content": oldQuestions[i]})
    messages.append({"role": "user", "content": oldChoices[i]})

  for message in messages:
    print(message)

  response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object" },
        messages = messages
  )

  print(response)

#  print(response.choices[0].message.content)
  jsonResult = json.loads(response.choices[0].message.content)

  scenario = jsonResult['scenario']
#  print(scenario)
  oldScenarios.append(scenario)

  images = []

  with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(process_scene_prompt_dali, scenario)
               for i in range(1)]
    for future in as_completed(futures):
      result = future.result()
      if result:
        images.append(result)
      else:
        return jsonify({"error": "Error generating image"}), 500

  question = jsonResult['question']
#  print(question)
  oldQuestions.append(question)

  choices = jsonResult['choices']
#  print(choices)

  return jsonify(
   {"data":
     {
      "scenario": scenario,
      "images": images,
      "question": question,
      "choices": choices,
      "oldScenarios": oldScenarios,
      "oldQuestions": oldQuestions,
      "oldChoices": oldChoices
      }
    })

@app.route('/')
def home():
    return "If you are seeing this page, that means the shit is online. if you have further issues, don't ask spencer - he probably dont care"

if __name__ == "__main__":
    app.run(debug=True)
