import requests
import argparse
import json
from libretranslatepy import LibreTranslateAPI
from googletrans import Translator
import logging
import asyncio
import sys
import re
from django.conf import settings
from webui.agent.utils import gemini_gen, groq_gen
import google.generativeai as genai
from groq import Groq


logger = logging.getLogger(__name__)
headers = {"Content-Type": "application/json"}

class BaseTranslator:
    def translate_text(self, text: str) -> str:
        """子类需要实现的翻译方法"""
        raise NotImplementedError
    
    def translate_text(self, text: str) -> str:
        pass


class GenAITranslator(BaseTranslator):
    def get_prompt(self, text: str) -> str:
        pstr = f"你是一个金融、经济、股票中英文翻译专家。将以下英文准确的翻译成简体中文，不要添加额外内容：\n{text}"
        logger.debug(f"Prompt: {pstr}")
        return pstr


class GroqTranslator(GenAITranslator):
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_TRANS_MODEL
    
    def translate_text(self, text: str) -> str:
        return groq_gen(self.client, self.model, self.get_prompt(text))


class GeminiTranslator(GenAITranslator):
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_TRANS_MODEL)
    
    def translate_text(self, text: str) -> str:
        return gemini_gen(self.model, self.get_prompt(text))
    

class OllamaTranslator(GenAITranslator):
    def __init__(self):
        self.host = settings.OLLAMA_URL
        self.model = settings.OLLAMA_TRANS_MODEL
        self.pattern = r"<think>(.*?)</think>"

    def remove_think_tag(self, text: str) -> str:
        return re.sub(self.pattern, "", text, flags=re.DOTALL)
        
        
    def translate_text(self, text: str) -> str:
        payload = {
            "model": self.model,
            "prompt": self.get_prompt(text),
            "stream": True
        }
        response = requests.post(self.host, headers=headers, data=json.dumps(payload), stream=True, timeout=120)
        response.raise_for_status()
        translated_chunks = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                json_line = json.loads(decoded_line)
                if 'response' in json_line:
                    translated_chunks.append(json_line['response'])
                if json_line.get('done'):
                    break
        tc = "".join(translated_chunks).strip()
        return self.remove_think_tag(tc)


class LibreTranslator(BaseTranslator):
    def __init__(self):
        self.lt = LibreTranslateAPI("https://libretranslate.com/")
        
        
    def translate_text(self, text: str) -> str:
        return self.lt.translate(text, "en", "zh")
    

class GoogleTranslator(BaseTranslator):
    def __init__(self):
        self.translator = Translator()
        
    async def _google_translate(self, text: str):
        r = await self.translator.translate(text, dest='zh-cn')
        return r.text
    
    
    def translate_text(self, text: str) -> str:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return asyncio.run(self._google_translate(text))
    

def get_translator(translator_name: str):
    logger.debug(f'Translator: {translator_name}')
    if translator_name == "ollama":
        return OllamaTranslator()
    elif translator_name == "libre":
        return LibreTranslator()
    elif translator_name == "google":
        return GoogleTranslator()
    elif translator_name == "gemini":
        return GeminiTranslator()
    elif translator_name == "groq":
        return GroqTranslator()
    else:
        raise Exception(f"[!] Unsupported translator: {translator_name}")


def main():
    import sys
    from os.path import dirname
    sys.path.append("/home/allen/work/fna")
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    test_parser = subparsers.add_parser("test", help="测试翻译器")
    test_parser.add_argument("--translator", required=True, help="翻译器名称，如 ollama")
    test_parser.add_argument("--text", required=True, help="要翻译的英文文本")
    args = parser.parse_args()

    if args.command == "test":
        text = args.text.strip()
        translator = get_translator(args.translator.lower())
        translated = translator.translate_text(text)
        print(f"中文：{translated}")


if __name__ == "__main__":
    main()
