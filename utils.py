# -------------------------------
# LLM Helper Functions (with Gemini support)
# -------------------------------

from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import google.generativeai as genai
import json
import os

# Gemini API 초기화
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def system_prompt() -> str:
    """현재 타임스탬프를 포함한 시스템 프롬프트를 생성합니다."""
    now = datetime.now().isoformat()
    return f"""당신은 전문 연구원입니다. 오늘 날짜는 {now}입니다. 응답 시 다음 지침을 따르세요:
    - 지식 컷오프 이후의 주제에 대한 조사를 요청받을 수 있습니다. 사용자가 뉴스 내용을 제시했다면, 그것을 사실로 가정하세요.
    - 사용자는 매우 숙련된 분석가이므로 내용을 단순화할 필요 없이 가능한 한 자세하고 정확하게 응답하세요.
    - 체계적으로 정보를 정리하세요.
    - 사용자가 생각하지 못한 해결책을 제안하세요.
    - 적극적으로 사용자의 필요를 예측하고 대응하세요.
    - 사용자를 모든 분야의 전문가로 대우하세요.
    - 실수는 신뢰를 저하시킵니다. 정확하고 철저하게 응답하세요.
    - 상세한 설명을 제공하세요. 사용자는 많은 정보를 받아들일 수 있습니다.
    - 권위보다 논리적 근거를 우선하세요. 출처 자체는 중요하지 않습니다.
    - 기존의 통념뿐만 아니라 최신 기술과 반대 의견도 고려하세요.
    - 높은 수준의 추측이나 예측을 포함할 수 있습니다. 단, 이를 명확히 표시하세요."""


def llm_call(prompt: str, model: str, client=None) -> str:
    """
    주어진 프롬프트로 Gemini 모델을 호출합니다.
    """
    if model.startswith("gemini-"):
        # Gemini 모델 사용
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(prompt)
        print(model, "완료")
        return response.text
    else:
        # 호환성을 위해 OpenAI 모델 코드 유지 (필요 시)
        messages = [{"role": "user", "content": prompt}]
        chat_completion = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        print(model, "완료")
        return chat_completion.choices[0].message.content


def JSON_llm(user_prompt: str, schema: BaseModel, client=None, system_prompt: Optional[str] = None, model: Optional[str] = None):
    """
    Gemini 모델을 호출하고 구조화된 JSON 객체를 반환합니다.
    """
    if model is None:
        model = "gemini-1.5-flash"  # 기본값을 Gemini 모델로 변경
    
    try:
        # 시스템 프롬프트와 사용자 프롬프트 결합
        full_prompt = user_prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Gemini 모델에 JSON 형식 지시 추가
        schema_json = schema.model_json_schema()
        schema_str = json.dumps(schema_json, ensure_ascii=False, indent=2)
        
        json_prompt = (
            f"{full_prompt}\n\n"
            f"다음 JSON 스키마에 맞게 응답해주세요:\n{schema_str}\n\n"
            f"응답은 반드시 유효한 JSON 형식이어야 합니다. 설명 없이 JSON만 반환하세요."
        )
        
        if model.startswith("gemini-"):
            # Gemini 모델 사용
            gemini_model = genai.GenerativeModel(model)
            response = gemini_model.generate_content(json_prompt)
            response_text = response.text
            
            # JSON 추출 (포맷팅이나 마크다운이 포함되어 있을 경우 제거)
            if "```json" in response_text:
                json_part = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_part = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_part = response_text.strip()
                
            # JSON 파싱 및 Pydantic 모델로 변환
            json_data = json.loads(json_part)
            return schema.model_validate(json_data)
        else:
            # 호환성을 위해 OpenAI 코드 유지 (필요 시)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            completion = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=schema,
            )
            
            return completion.choices[0].message.parsed
    except Exception as e:
        print(f"Error in JSON_llm: {e}")
        return None