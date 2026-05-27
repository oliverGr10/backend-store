"""
Módulo de IA — BodegaApp.
Consulta los datos reales del bodeguero y genera análisis con el proveedor IA configurado.
Para cambiar de IA: solo cambia AI_PROVIDER en .env (gemini | anthropic).
"""

import uuid
import logging
from datetime import date, timedelta
from supabase import Client

from app.modules.ai.providers.base import AIProvider
from app.modules.ai.schemas import AIRequest, AIResponse

logger = logging.getLogger("bodega.ai")


class AIService:
    def __init__(self, db: Client, ai_provider: AIProvider):
        self.db = db
        self.ai = ai_provider
        logger.info(f"✅ AIService listo — proveedor: {ai_provider.provider_name}")

    # ── Recolección de datos reales ────────────────────────────────────────

    def _get_data(self, user_id: uuid.UUID, days: int) -> dict:
        """Consulta Supabase y consolida todos los datos del período."""
        since = (date.today() - timedelta(days=days)).isoformat()

        # Ventas del período
        sales_result = (
            self.db.table("sales")
            .select("*, sale_items(*)")
            .eq("user_id", str(user_id))
            .gte("created_at", since)
            .execute()
        )
        sales = sales_result.data or []

        # Inventario actual
        products_result = (
            self.db.table("products")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("is_active", True)
            .execute()
        )
        products = products_result.data or []

        # Fiados pendientes
        debts_result = (
            self.db.table("debts")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("paid", False)
            .execute()
        )
        pending_debts = debts_result.data or []

        # Calcular métricas
        total_revenue = sum(float(s["total"]) for s in sales)
        total_profit = sum(float(s["profit"]) for s in sales)
        cash_sales = [s for s in sales if s.get("payment_type", "cash") == "cash"]
        credit_sales = [s for s in sales if s.get("payment_type") == "credit"]

        # Productos más vendidos (por cantidad)
        product_sales: dict[str, dict] = {}
        for sale in sales:
            for item in sale.get("sale_items", []):
                name = item["product_name"]
                if name not in product_sales:
                    product_sales[name] = {"quantity": 0, "revenue": 0.0}
                product_sales[name]["quantity"] += item["quantity"]
                product_sales[name]["revenue"] += float(item["price"]) * item["quantity"]

        top_products = sorted(
            product_sales.items(),
            key=lambda x: x[1]["quantity"],
            reverse=True
        )[:5]

        # Productos con stock bajo
        low_stock = [p for p in products if p["stock"] <= p["min_stock"]]

        # Clientes con más fiados pendientes
        debtor_totals: dict[str, float] = {}
        for d in pending_debts:
            name = d["customer_name"]
            debtor_totals[name] = debtor_totals.get(name, 0) + float(d["amount"])

        top_debtors = sorted(debtor_totals.items(), key=lambda x: x[1], reverse=True)[:5]

        data = {
            "period_days": days,
            "total_sales": len(sales),
            "cash_sales": len(cash_sales),
            "credit_sales": len(credit_sales),
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin": round((total_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
            "total_products": len(products),
            "low_stock_products": [
                {"name": p["name"], "stock": p["stock"], "min_stock": p["min_stock"]}
                for p in low_stock
            ],
            "top_products": [
                {"name": n, "quantity": d["quantity"], "revenue": round(d["revenue"], 2)}
                for n, d in top_products
            ],
            "pending_debts_count": len(pending_debts),
            "pending_debts_total": round(sum(float(d["amount"]) for d in pending_debts), 2),
            "top_debtors": [
                {"name": n, "amount": round(a, 2)}
                for n, a in top_debtors
            ],
        }

        logger.info(
            f"📊 Datos: {data['total_sales']} ventas | "
            f"S/{data['total_revenue']} ingresos | "
            f"{data['total_products']} productos | "
            f"{data['pending_debts_count']} fiados"
        )
        return data

    # ── Construcción del prompt ────────────────────────────────────────────

    def _build_prompt(self, request: AIRequest, data: dict) -> str:
        """Construye el prompt con los datos reales del negocio."""

        base_context = f"""Eres el asistente de inteligencia artificial de BodegaApp,
una app para bodegueros de barrio en Perú. Tu misión es ayudar al bodeguero a
entender su negocio y tomar mejores decisiones. Habla en español peruano simple,
directo y amigable. Usa emojis cuando sea útil. Da consejos prácticos.

DATOS REALES DEL NEGOCIO (últimos {data['period_days']} días):

📊 VENTAS:
- Total de ventas: {data['total_sales']}
- Ventas al contado: {data['cash_sales']}
- Ventas fiadas: {data['credit_sales']}
- Ingresos totales: S/ {data['total_revenue']}
- Ganancia neta: S/ {data['total_profit']}
- Margen de ganancia: {data['profit_margin']}%

🏆 PRODUCTOS MÁS VENDIDOS:
{chr(10).join(f"  {i+1}. {p['name']}: {p['quantity']} unidades (S/ {p['revenue']})" for i, p in enumerate(data['top_products'])) or "  Sin ventas en el período"}

📦 INVENTARIO:
- Total productos activos: {data['total_products']}
- Productos con stock bajo: {len(data['low_stock_products'])}
{chr(10).join(f"  ⚠️ {p['name']}: {p['stock']} unidades (mínimo: {p['min_stock']})" for p in data['low_stock_products']) or "  ✅ Todo el inventario está bien"}

💰 FIADOS PENDIENTES:
- Cantidad de fiados: {data['pending_debts_count']}
- Total pendiente de cobro: S/ {data['pending_debts_total']}
- Clientes que más deben:
{chr(10).join(f"  • {d['name']}: S/ {d['amount']}" for d in data['top_debtors']) or "  Sin fiados pendientes 🎉"}
"""

        # Si hay pregunta libre → respuesta enfocada y conversacional, sin análisis general
        if request.question:
            return base_context + f"""

PREGUNTA DEL BODEGUERO: {request.question}

Responde SOLO esa pregunta de forma directa, breve y amigable (máximo 4 oraciones).
Usa los datos del negocio para dar una respuesta personalizada si aplica.
No hagas un análisis completo, no repitas los datos, no pongas títulos ni secciones.
Habla como si fueras un amigo que entiende de negocios."""

        prompts = {
            "general": base_context + "\n\nHaz un análisis completo del negocio. Destaca lo más importante, identifica problemas y da 3 recomendaciones concretas y accionables para mejorar las ganancias.",
            "top_products": base_context + "\n\nAnaliza los productos más vendidos. ¿Cuáles generan más ganancia? ¿Cuáles debería tener siempre en stock? ¿Hay oportunidad de vender productos complementarios?",
            "restock": base_context + "\n\nAnaliza el inventario y recomienda qué productos reabastecer urgentemente. Considera el ritmo de ventas. Prioriza por importancia para el negocio.",
            "profit": base_context + "\n\nAnaliza las ganancias del negocio. ¿El margen es saludable para una bodega peruana? ¿Qué productos tienen mejor margen? ¿Cómo puede mejorar la rentabilidad?",
            "debts": base_context + "\n\nAnaliza la situación de fiados. ¿Hay riesgo de no cobrar? ¿Qué estrategia recomiendas para cobrar los fiados pendientes? ¿Cómo manejar mejor el crédito a clientes?",
            "slow_products": base_context + "\n\nIdentifica productos que probablemente no se están vendiendo bien (no aparecen en el top). ¿Qué hacer con ellos? ¿Liquidar, cambiar precio, o promocionar?",
        }

        prompt = prompts.get(request.type, prompts["general"])
        logger.info(f"📝 Prompt construido: {len(prompt)} chars, tipo={request.type}")
        return prompt

    # ── Método principal ───────────────────────────────────────────────────

    def analyze(self, request: AIRequest, user_id: uuid.UUID) -> AIResponse:
        """
        Flujo completo:
        1. Consulta datos reales de Supabase
        2. Construye prompt con esos datos
        3. Delega al proveedor IA configurado (Gemini / Claude / etc.)
        4. Retorna análisis en español
        """
        logger.info(f"🤖 Análisis tipo='{request.type}' días={request.days} proveedor={self.ai.provider_name}")

        data = self._get_data(user_id, request.days)
        prompt = self._build_prompt(request, data)

        try:
            analysis = self.ai.generate(prompt, max_tokens=1024, temperature=0.7)
        except Exception as e:
            logger.error(f"❌ Error proveedor IA ({self.ai.provider_name}): {e}")
            raise Exception(f"Error al consultar la IA: {str(e)}")

        return AIResponse(
            analysis=analysis,
            type=request.type,
            days_analyzed=request.days,
            data_summary={
                "ventas": data["total_sales"],
                "ingresos": data["total_revenue"],
                "ganancia": data["total_profit"],
                "margen_pct": data["profit_margin"],
                "fiados_pendientes": data["pending_debts_total"],
            },
        )
