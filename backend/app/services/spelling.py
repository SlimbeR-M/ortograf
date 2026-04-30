import language_tool_python

tool = language_tool_python.LanguageTool("es")

def correct_spelling(text: str) -> str:
    matches = tool.check(text)
    return language_tool_python.utils.correct(text, matches)


