"""Catalogo multisectorial de oportunidades para ORION."""

SECTORS = {
    "ia": {"name": "Inteligencia artificial", "queries": [
        "AI automation underserved small business problems",
        "AI SaaS startup business models pricing market",
        "open source AI tools commercial opportunities"]},
    "tecnologia": {"name": "Tecnologia", "queries": [
        "emerging technology products unmet customer needs",
        "developer tools startup opportunities market demand",
        "technology trends adoption barriers business opportunities"]},
    "negocios_digitales": {"name": "Negocios digitales", "queries": [
        "profitable digital services underserved niches evidence",
        "digital products recurring revenue business models competition",
        "small online business customer acquisition costs case studies"]},
    "videojuegos": {"name": "Videojuegos", "queries": [
        "indie game market trends underserved player niches",
        "video game development tools monetization market research",
        "gaming industry business opportunities small studios 2026"]},
    "cripto": {"name": "Criptoactivos", "queries": [
        "crypto market infrastructure adoption risks evidence",
        "blockchain products real user demand business models",
        "crypto asset market data volatility liquidity risks"]},
}

def list_sectors():
    """Devuelve el catalogo de sectores sin modificar datos existentes."""
    return [{"id": sid, "name": s["name"], "queries": list(s["queries"])} for sid, s in SECTORS.items()]

def build_sector_queries(sector_id=None):
    """Prepara consultas por sector; no las ejecuta ni genera señales."""
    selected = SECTORS if sector_id is None else {sector_id: SECTORS[sector_id]}
    return [{"sector_id": sid, "sector": s["name"], "query": q} for sid, s in selected.items() for q in s["queries"]]

if __name__ == "__main__":
    for sector in list_sectors():
        print(f"\n{sector['name']} ({sector['id']})")
        for query in sector["queries"]:
            print(f"  - {query}")
    print(f"\nTotal: {len(build_sector_queries())} consultas preparadas")
