from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="TheBloke/phi-2-GGUF",
	filename="phi-2.Q4_K_M.gguf",
)

output = llm(
	"Once upon a time,",
	max_tokens=20,
	echo=True
)
print(output["choices"][0]["text"])