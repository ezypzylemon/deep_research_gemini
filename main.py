import os
from step1_feedback.feedback import generate_feedback
from step2_research.research import deep_research
from step3_reporting.reporting import write_final_report
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()  # .env 파일에서 환경 변수를 불러옵니다.

# Gemini API 초기화
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

def main():
    # 사용자로부터 초기 연구 질문을 입력받음
    query = input("어떤 주제에 대해 리서치하시겠습니까?: ")

    # Gemini 모델 설정
    feedback_model = "gemini-1.5-flash"
    research_model = "gemini-1.5-flash"
    reporting_model = "gemini-1.5-flash"
    
    # 클라이언트는 더 이상 필요하지 않음 (Gemini는 직접 API 호출)
    client = None

    # 추가적인 질문을 생성하여 연구 방향을 구체화
    print(f"------------------------------------------1단계: 추가 질문 생성----------------------------------------------------")
    feedback_questions = generate_feedback(query, client, feedback_model, max_feedbacks=3)
    answers = []
    if feedback_questions:
        print("\n다음 질문에 답변해 주세요:")
        for idx, question in enumerate(feedback_questions, start=1):
            answer = input(f"질문 {idx}: {question}\n답변: ")
            answers.append(answer)
    else:
        print("추가 질문이 생성되지 않았습니다.")

    # 초기 질문과 후속 질문 및 답변을 결합
    combined_query = f"초기 질문: {query}\n"
    for i in range(len(feedback_questions)):
        combined_query += f"\n{i+1}. 질문: {feedback_questions[i]}\n"
        combined_query += f"   답변: {answers[i]}\n"
        
    print("최종질문 : \n")
    print(combined_query)

    # 연구 범위 및 깊이를 사용자로부터 입력받음
    try:
        breadth = int(input("연구 범위를 입력하세요 (예: 2): ") or "2")
    except ValueError:
        breadth = 2
    try:
        depth = int(input("연구 깊이를 입력하세요 (예: 2): ") or "2")
    except ValueError:
        depth = 2

    # 심층 연구 수행 (동기적으로 실행)
    print(f"------------------------------------------2단계: 딥리서치----------------------------------------------------")
    research_results = deep_research(
        query=combined_query,
        breadth=breadth,
        depth=depth,
        client=client,
        model=research_model
    )

    # 연구 결과 출력
    print("\n연구 결과:")
    for learning in research_results["learnings"]:
        print(f" - {learning}")

    # 최종 보고서 생성
    print(f"------------------------------------------3단계: 보고서 작성----------------------------------------------------")

    report = write_final_report(
        prompt=combined_query,
        learnings=research_results["learnings"],
        visited_urls=research_results["visited_urls"],
        client=client,
        model=reporting_model
    )

    # 최종 보고서 출력 및 파일 저장
    print("\n최종 보고서:\n")
    print(report)
    with open("output/output.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n보고서가 output/output.md 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()