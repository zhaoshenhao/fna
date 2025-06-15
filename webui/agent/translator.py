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


logger = logging.getLogger(__name__)
headers = {"Content-Type": "application/json"}

class BaseTranslator:
    def translate_text(self, text: str) -> str:
        """子类需要实现的翻译方法"""
        raise NotImplementedError
    
    def translate_text(self, text: str) -> str:
        pass


class OllamaTranslator(BaseTranslator):
    def __init__(self, host="http://localhost:11434", model="qwen3:8b"):
        self.host = host
        self.model = model
        self.pattern = r"<think>(.*?)</think>"

    def remove_think_tag(self, text: str) -> str:
        return re.sub(self.pattern, "", text, flags=re.DOTALL)
        
        
    def translate_text(self, text: str) -> str:
        prompt = f"请将以下英文翻译成简体中文：\n{text}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        response = requests.post(f"{self.host}/api/generate", headers=headers, data=json.dumps(payload), stream=True, timeout=120)
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
    if translator_name == "ollama":
        return OllamaTranslator("http://172.30.237.34:11434", model=settings.OLLAMA_MODEL)
    elif translator_name == "libre":
        return LibreTranslator()
    elif translator_name == "google":
        return GoogleTranslator()
    else:
        raise Exception(f"[!] Unsupported translator: {translator_name}")


def main():
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
