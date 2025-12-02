# ai_models.py
import requests
from abc import ABC, abstractmethod
import logging
from django.conf import settings
import google.generativeai as genai
from groq import Groq
from webui.agent.utils import gemini_gen, groq_gen


logger = logging.getLogger(__name__)

class Analyzer(ABC):
    """
    Base class for all AI models, defining a consistent interface for news analysis.
    """
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    @abstractmethod
    def analyze_news_impact(self, news_title: str, news_content: str) -> str: # Return type changed to str
        """
        Analyzes news impact on stocks and provides advice, returning the full text response.
        Must be implemented by subclasses.

        Args:
            news_title (str): The title of the news article.
            news_content (str): The full content of the news article.

        Returns:
            str: The full text response from the AI model containing the analysis.
        """
        pass

    def generate_prompt(self, news_title: str, news_content: str) -> str:
        """
        Generates the detailed prompt for the Ollama model with the revised format.
        """
        prompt = f"""
        请你作为一名资深的财经新闻分析师，仔细阅读以下新闻文章，然后完成以下任务：
        1.  **新闻摘要：** 总结新闻文章的**核心内容**，生成一个简洁的摘要。
        2.  **相关股票影响与建议：** 分析该文章可能对新闻中直接提及或高度相关的**特定公司股票**产生的影响（正面、负面或中性），并说明理由。基于此影响，给出对这些股票的概括性操作建议（例如：关注、谨慎买入、观望、注意风险、短期波动等），并简要解释。
        3.  **行业股票影响与建议：**
            * **科技股影响与建议：** 分析该文章对整个科技（包括AI、半导体等）行业股票的可能影响及操作建议。
            * **金融股影响与建议：** 分析该文章对银行、保险、券商等金融行业股票的可能影响及操作建议。
            * **能源股影响与建议：** 分析该文章对石油、天然气、可再生能源等能源行业股票的可能影响及操作建议。
            * **出行旅游股影响与建议：** 分析该文章对航空公司、酒店、OTA平台等出行旅游行业股票的可能影响及操作建议。
            * **医疗健康股影响与建议：** 分析该文章对制药、生物科技、医疗设备、医疗服务等医疗健康行业股票的可能影响及操作建议。

        请严格按照以下格式输出你的分析和建议：

        **新闻摘要：**
        [新闻摘要内容]

        **相关股票影响与建议：**
        * **影响：** [影响分析]
        * **建议：** [操作建议]

        **行业股票影响与建议：**
        * **科技股影响与建议：**
            * **影响：** [影响分析]
            * **建议：** [操作建议]
        * **金融股影响与建议：**
            * **影响：** [影响分析]
            * **建议：** [操作建议]
        * **能源股影响与建议：**
            * **影响：** [影响分析]
            * **建议：** [操作建议]
        * **出行旅游股影响与建议：**
            * **影响：** [影响分析]
            * **建议：** [操作建议]
        * **医疗健康股影响与建议：**
            * **影响：** [影响分析]
            * **建议：** [操作建议]

        **风险提示：**
        [风险提示内容]

        新闻文章标题：{news_title}
        新闻文章内容：{news_content}
        """
        return prompt.strip()
    

class GeminiAnalyzer(Analyzer):
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_TRANS_MODEL)
    
    def analyze_news_impact(self, news_title: str, news_content: str) -> str:
        return gemini_gen(self.model, self.generate_prompt(news_title, news_content))
        

class GroqAnalyzer(Analyzer):
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_TRANS_MODEL
    
    def analyze_news_impact(self, news_title: str, news_content: str) -> str:
        return groq_gen(self.client, self.model, self.generate_prompt(news_title, news_content))
    
    
class OllamaAnalyzer(Analyzer):
    """
    Subclass for interacting with a locally running Ollama model.
    """
    def __init__(self):
        self.model_name = settings.OLLAMA_ANALYZER_MODEL
        self.api_base_url = settings.OLLAMA_URL
        super().__init__()


    def analyze_news_impact(self, news_title: str, news_content: str) -> str: # Return type changed to str
        """
        Analyzes news impact using the Ollama model, returning the full text response.
        """
        prompt = self.generate_prompt(news_title, news_content)
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3, # Adjust for less randomness, more factual
                "top_k": 40,
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(self.api_base_url, headers=self.headers, json=data, timeout=180)
            response.raise_for_status()
            result = response.json()
            full_response_text = result.get('response', '').strip()
            return full_response_text # Directly return the full text response
        except Exception as e:
            logger.error(f"An unexpected error occurred during news analysis: {e}")
            return ""
        

def get_analyzer(analyzer_name: str):
    if analyzer_name == "ollama":
        return OllamaAnalyzer()
    if analyzer_name == "gemini":
        return GeminiAnalyzer()
    if analyzer_name == "groq":
        return GroqAnalyzer()
    raise Exception(f"Unsupported analyzer: {analyzer_name}")