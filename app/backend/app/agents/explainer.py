"""
AI Agent: kullanıcının doğal dil sorularını, tools.py'deki fonksiyonları
çağırarak (tool calling) cevaplar.

Guardrail kuralları (SYSTEM_INSTRUCTION içinde LLM'e açıkça söyleniyor):
- Agent veri uydurmaz, sadece tool çıktısına dayanır.
- Solver'ın verdiği kararı asla değiştirmez, sadece açıklar.
- Emin olmadığı durumlarda bunu açıkça belirtir.

GEMINI_API_KEY tanımlı değilse, agent uçtan uca çalışmaya devam etsin diye
basit bir kural tabanlı moda düşer.
"""
from app.agents.tools import (
    get_accepted_requests,
    get_rejected_requests,
    calculate_capacity_utilization,
    explain_request_decision,
)
from app.config import settings

SYSTEM_INSTRUCTION = (
    "Sen bir havayolu kargo operasyonu karar destek asistanısın. "
    "Sadece sana verilen tool'ların döndürdüğü gerçek verilere dayanarak cevap ver. "
    "Hiçbir sayı, karar veya gerekçe uydurma. Elindeki tool'lar soruyu cevaplamaya "
    "yetmiyorsa bunu açıkça söyle. Solver'ın verdiği kabul/red kararını asla "
    "değiştirme veya sorgulama, sadece mevcut veriye dayanarak açıkla. "
    "Cevaplarını kısa ve net tut, Türkçe cevap ver."
)

TOOLS = [
    get_accepted_requests,
    get_rejected_requests,
    calculate_capacity_utilization,
    explain_request_decision,
]


def ask_agent(question: str) -> str:
    api_key = settings.gemini_api_key
    if not api_key:
        return (
            "GEMINI_API_KEY tanımlı değil, bu yüzden gerçek bir dil modeli çalışamıyor. "
            "app/backend/.env dosyasına GEMINI_API_KEY=... ekleyip sunucuyu yeniden başlat."
        )

    import google.generativeai as genai

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        tools=TOOLS,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(question)
    return response.text
