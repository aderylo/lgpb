# roundtable_data

## Prerequisites

Install dependencies:
```
pip install -r requirements.txt
```

<details>

<summary>Side notes</summary>
A few side notes for reproducablity:

-  please use `virtalenv` or some other tool for environment management
- python@3.12 was used in development

</details>


### Using LLMs
Some scripts, notably `annotation_pipeline.py` necessitate access to running LLM which communicates via OpenAI style api. To run your local LLM do following:
- get a .gguf file of your favorite llm supported by llama_cpp from huggingface. 
- add its path to a `config.json` file
- run following command:
    ```
    python3 -m llama_cpp.server --config_file config.json
    ```

Now, LLM specified in the `config.json` will run in the background and respond to calls made by the aforementioned script.
