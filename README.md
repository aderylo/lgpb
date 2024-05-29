# roundtable_data



## Using LLMs
All scripts from llm directory necessitate access to running LLM which communicates via OpenAI style api.
We will be using llm hosted locally:

```
python3 -m llama_cpp.server --config_file config.json
```

Now, LLM specified in the `config.json` will run in the background and respond to calls made by functions
from `./llm` directory.
