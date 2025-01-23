import requests

# Create your tests here.

class OllamaLLMModel:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model

    def get_llm_response(self, agent):
        url = f"{self.base_url}/completions"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "prompt": f"Generate a response for {agent}",
            "max_tokens": 150
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("text", "")
        else:
            return f"Error: {response.status_code}"

ollama_model = OllamaLLMModel(
    base_url="http://219.147.100.43:8088/api/v1",
    model="qwen2.5:72b"
)

response = ollama_model.get_llm_response("Klaus Mueller")

response = ollama_model.get_llm_response("Isabella Rodriguez")
if response.startswith("Error"):
    print("Failed to get response:", response)
else:
    print("Ollama response:", response)