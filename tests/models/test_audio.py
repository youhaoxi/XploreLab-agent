import base64
import requests
from utu.utils import SimplifiedAsyncOpenAI
from utu.config import ConfigLoader


config = ConfigLoader.load_model_config("v00")
client = SimplifiedAsyncOpenAI(**config.model_dump())


# https://platform.openai.com/docs/guides/audio?example=audio-in#add-audio-to-your-existing-application
async def test_audio_input():
    # Fetch the audio file and convert it to a base64 encoded string
    url = "https://cdn.openai.com/API/docs/audio/alloy.wav"
    response = requests.get(url)
    response.raise_for_status()
    wav_data = response.content
    encoded_string = base64.b64encode(wav_data).decode('utf-8')

    completion = await client.chat_completion(
        model="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "wav"},
        messages=[
            {
                "role": "user",
                "content": [
                    { 
                        "type": "text",
                        "text": "What is in this recording?"
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_string,
                            "format": "wav"
                        }
                    }
                ]
            },
        ]
    )

    print(completion.choices[0].message)
