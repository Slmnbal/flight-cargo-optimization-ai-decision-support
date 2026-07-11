"""
AI Agent: kullanıcının doğal dil sorularını, tools.py'deki fonksiyonları
çağırarak (tool calling) cevaplar.

Guardrail kuralları (SYSTEM_INSTRUCTION içinde LLM'e açıkça söyleniyor):
- Agent veri uydurmaz, sadece tool çıktısına dayanır.
- Solver'ın verdiği kararı asla değiştirmez, sadece açıklar.
- search_knowledge_base'den gelen bilgiyi (dokümantasyon/tasarım kararı) canlı
  veritabanı sorgularından gelen bilgiden (get_accepted_requests vb.) ayırt eder.
- Emin olmadığı durumlarda bunu açıkça belirtir.

GEMINI_API_KEY tanımlı değilse, agent uçtan uca çalışmaya devam etsin diye
basit bir kural tabanlı moda düşer.

Hafıza: her çağrı artık bir session_id taşıyor. session_id verilmezse yeni bir
konuşma başlatılır; verilirse önceki turlar (services/agent_service.py ->
load_conversation_history) Gemini'ye history olarak veriliyor.
"""
from sqlalchemy.orm import Session

from app.agents.tools import (
    get_accepted_requests,
    get_rejected_requests,
    get_scenario_kpi_summary,
    list_recent_scenarios,
    get_route_statistics,
    get_top_routes_by_revenue,
    calculate_capacity_utilization,
    explain_request_decision,
    predict_acceptance_probability_for_request,
    get_aircraft_type_specs,
    list_restricted_routes,
    search_knowledge_base,
)
from app.config import settings
from app.services.agent_service import load_conversation_history, new_session_id, save_message

SYSTEM_INSTRUCTION = (
    "Sen bir havayolu kargo operasyonu karar destek asistanısın. "
    "Sadece sana verilen tool'ların döndürdüğü gerçek verilere dayanarak cevap ver. "
    "Hiçbir sayı, karar veya gerekçe uydurma. Elindeki tool'lar soruyu cevaplamaya "
    "yetmiyorsa bunu açıkça söyle. Solver'ın verdiği kabul/red kararını asla "
    "değiştirme veya sorgulama, sadece mevcut veriye dayanarak açıkla. "
    "search_knowledge_base HARİÇ tüm tool'lar CANLI veritabanı/model verisidir (belirli "
    "bir talep/uçuş/rota/senaryo hakkında somut, güncel sayılar -- ML tahmini dahil, "
    "o da geçmiş veriden öğrenilmiş gerçek bir model çıktısıdır, uydurma değil). "
    "search_knowledge_base tool'u ise projenin kendi tasarım dokümantasyonundan (iş "
    "kuralları, kısıt gerekçeleri) getirilen genel AÇIKLAYICI bilgidir -- 'neden embargo "
    "var', 'priority_class nasıl işliyor' gibi kavramsal sorularda bunu kullan. Cevap "
    "verirken hangi tür bilgiye dayandığını (canlı veri/model mi, dokümantasyon mu) "
    "karıştırma; söylediğin şeyin hangi kaynaktan geldiğini kullanıcı sorarsa açıkça "
    "belirtebilmelisin. ML tahmini bir olasılıktır, solver'ın kesin kabul/red kararının "
    "yerini tutmaz -- bunu karıştırma. "
    "Cevaplarını kısa ve net tut, Türkçe cevap ver."
)

TOOLS = [
    get_accepted_requests,
    get_rejected_requests,
    get_scenario_kpi_summary,
    list_recent_scenarios,
    get_route_statistics,
    get_top_routes_by_revenue,
    calculate_capacity_utilization,
    explain_request_decision,
    predict_acceptance_probability_for_request,
    get_aircraft_type_specs,
    list_restricted_routes,
    search_knowledge_base,
]


def ask_agent(db: Session, question: str, session_id: str | None = None) -> tuple[str, str]:
    session_id = session_id or new_session_id()

    api_key = settings.gemini_api_key
    if not api_key:
        return (
            "GEMINI_API_KEY tanımlı değil, bu yüzden gerçek bir dil modeli çalışamıyor. "
            "app/backend/.env dosyasına GEMINI_API_KEY=... ekleyip sunucuyu yeniden başlat.",
            session_id,
        )

    import google.generativeai as genai

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        tools=TOOLS,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    history = load_conversation_history(db, session_id)
    chat = model.start_chat(history=history, enable_automatic_function_calling=True)
    response = chat.send_message(question)
    answer = response.text

    save_message(db, session_id, "user", question)
    save_message(db, session_id, "model", answer)

    return answer, session_id
