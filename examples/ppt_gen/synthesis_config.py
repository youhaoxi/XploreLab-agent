import argparse

TEMPLATE = """
# @package _global_
defaults:
  - _self_
  - /tools/search@toolkits.search

agent:
  name: PPTGeneratorAgent
  instructions: |-
    You are an expert in PowerPoint generation.
    Given a url or a document, you are required to:

    1. Analyze the content and structure of the report or document.
    2. Arrange the content in a logical and coherent manner. Divide the content into slides formatted by the json schema
    3. Generate a PowerPoint presentation based on the given json schema and content page by page.

    Don't dive too deep into the content, just extract the key points and arrange them in a logical and coherent manner.

    If there are any images in the document, you are encouraged to use them in the presentation (with url and caption).

    Remember you can insert table into the content page.

    ## JSON Schema

    ```json
    {schema_content}
    ```

    ## Example Arragenment

    1. (title) title: Attention is All You Need
    2. (content) introduction of the paper (...)
    3. (section_title) section title: Related Work
    4. (items_page_4) items: [...]
    5. (content) conclusion of the paper (...)
    6. (acknowledgement) acknowledgement: [...]

max_turns: 100
"""


def prepend_indent(text, indent=2):
    return "\n".join(["  " * indent + line for line in text.split("\n")])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=str, required=True)
    args = parser.parse_args()
    output_file = args.output

    with open("schema/template.schema.json") as f:
        schema_content = f.read()

    schema_content = prepend_indent(schema_content, indent=2)

    config_content = TEMPLATE.format(schema_content=schema_content)

    with open(output_file, "w") as f:
        f.write(config_content)

    print("Template schema:")
    print(schema_content)
    print("Config file generated successfully.")
