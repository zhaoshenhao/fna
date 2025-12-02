from typing import Iterator
import logging

logger = logging.getLogger(__name__)


def gemini_gen(model, prompt: str, stream: bool=True) -> str:
    response = model.generate_content(prompt, stream=stream)
    return get_gemini_stream_response(response)


def get_gemini_stream_response(stream: Iterator,):
    full_text = []
    
    for chunk in stream:
        if chunk.candidates:
            if chunk.candidates[0].content.parts:
                try:
                    text_part = chunk.text
                    full_text.append(text_part)
                except ValueError:
                    full_text.append("[内容被屏蔽]")
            else:
                pass
        else:
            if hasattr(chunk, 'prompt_feedback'):
                 logger.info(f"提示词反馈: {chunk.prompt_feedback}")
    ret_str = "".join(full_text)
    logger.debug(f"Gemini response: {ret_str}")
    return ret_str


def groq_gen(client, model, prompt: str, stream: bool=True) -> str:
    logger.debug(f"prompt: {prompt}")
    logger.debug(f"model: {model}")
    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
        stream=stream,
    )
    return get_groq_stream_response(stream)


def get_groq_stream_response(stream: Iterator):
    full_text = []
    
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
        else:
            ""
        if content:
            full_text.append(content) 
    ret_str = "".join(full_text)
    logger.debug(f"Groq response: {ret_str}")
    return ret_str

