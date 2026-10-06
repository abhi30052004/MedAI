import json
from typing import Dict, Any, List, Optional
import openai
import groq
from pydantic import BaseModel
from app.core.config import settings


class AnalysisResult(BaseModel):
    patient_summary: Optional[str] = None
    medical_history: Optional[List[str]] = []
    symptoms: Optional[List[str]] = []
    diagnoses: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    procedures: Optional[List[str]] = []
    clinical_findings: Optional[List[str]] = []
    important_observations: Optional[List[str]] = []
    missing_information: Optional[List[str]] = []
    potential_risks: Optional[List[str]] = []
    ai_analysis: Optional[str] = None
    evidence: Optional[List[Any]] = []
    confidence: Optional[str] = "low"


class OpenAIProvider:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def analyze(self, extracted_text: str) -> Dict[str, Any]:
        prompt = f"""
        You are a highly skilled clinical AI assistant. Analyze the following medical case extracted from documents.
        Return ONLY a JSON object exactly matching this structure (with empty strings or arrays if info is missing):
        {{
          "patient_summary": "",
          "medical_history": [],
          "symptoms": [],
          "diagnoses": [],
          "medications": [],
          "procedures": [],
          "clinical_findings": [],
          "important_observations": [],
          "missing_information": [],
          "potential_risks": [],
          "ai_analysis": "",
          "evidence": [],
          "confidence": "low"
        }}
        
        Do not invent or hallucinate information. If missing, say "Not available in the provided documents."
        Use tentative language for AI observations.
        
        EXTRACTED TEXT:
        {extracted_text}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        
        return json.loads(response.choices[0].message.content)

class GroqProvider:
    def __init__(self):
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def analyze(self, extracted_text: str) -> Dict[str, Any]:
        prompt = f"""
        You are a highly skilled clinical AI assistant. Analyze the following medical case extracted from documents.
        Return ONLY a JSON object exactly matching this structure (with empty strings or arrays if info is missing):
        {{
          "patient_summary": "",
          "medical_history": [],
          "symptoms": [],
          "diagnoses": [],
          "medications": [],
          "procedures": [],
          "clinical_findings": [],
          "important_observations": [],
          "missing_information": [],
          "potential_risks": [],
          "ai_analysis": "",
          "evidence": [],
          "confidence": "low"
        }}
        
        Do not invent or hallucinate information. If missing, say "Not available in the provided documents."
        
        EXTRACTED TEXT:
        {extracted_text}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        
        return json.loads(response.choices[0].message.content)

class AIService:
    def __init__(self):
        self.provider_name = settings.PRIMARY_LLM_PROVIDER.lower()
        if self.provider_name == "openai" and settings.OPENAI_API_KEY:
            self.provider = OpenAIProvider()
        elif self.provider_name == "groq" and settings.GROQ_API_KEY:
            self.provider = GroqProvider()
        else:
            # Fallback for local development when keys aren't set
            self.provider = None

    def generate_analysis(self, case_id: int, extracted_text: str) -> AnalysisResult:
        if not self.provider:
            # Mock response for testing if no provider configured
            return AnalysisResult(
                patient_summary="Mock summary: AI Provider not configured. Set OPENAI_API_KEY.",
                ai_analysis="This is a mock analysis.",
                confidence="low"
            )
            
        try:
            result = self.provider.analyze(extracted_text)
            return AnalysisResult(**result)
        except Exception as e:
            # Log error and return empty fallback
            print(f"AI Provider error: {e}")
            return AnalysisResult(
                patient_summary="Error generating analysis.",
                ai_analysis=str(e),
                confidence="low"
            )

ai_service = AIService()
