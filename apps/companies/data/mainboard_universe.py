"""Curated list of ~100 SGX Mainboard companies, anchored on STI 30 + iEdge
Singapore Next 50 plus targeted fills per spec
``SGX_Tool_Refinements_and_Cost_Analysis`` section 2.

Each entry is (sgx_code, name, short_name, sector). The ``name`` MUST match
SGX's ``issuer_name`` exactly because the per-company API call uses
``?value=<name>&exactsearch=true``. If a name is wrong, the per-company
scrape will return zero rows for it — flag and fix.

The sgx_code is best-effort; the live scrape will overwrite it with whatever
``issuers[0].stock_code`` SGX returns, so a wrong code self-corrects.

Edit this file freely to adjust the universe.
"""

# (sgx_code, name, short_name, sector)
MAINBOARD_COMPANIES: list[tuple[str, str, str, str]] = [

    # --- Banks & Financial Services (~8) ---
    ("D05", "DBS GROUP HOLDINGS LTD", "DBS", "Banks & Financial Services"),
    ("O39", "OVERSEA-CHINESE BANKING CORPORATION LIMITED", "OCBC", "Banks & Financial Services"),
    ("U11", "UNITED OVERSEAS BANK LIMITED", "UOB", "Banks & Financial Services"),
    ("S68", "SINGAPORE EXCHANGE LIMITED", "SGX", "Banks & Financial Services"),
    ("AIY", "IFAST CORPORATION LTD.", "iFAST", "Banks & Financial Services"),
    ("S41", "HONG LEONG FINANCE LIMITED", "Hong Leong Finance", "Banks & Financial Services"),
    ("U10", "UOB-KAY HIAN HOLDINGS LIMITED", "UOB-Kay Hian", "Banks & Financial Services"),
    ("G07", "GREAT EASTERN HOLDINGS LIMITED", "Great Eastern", "Banks & Financial Services"),

    # --- REITs & Property Trusts (~30) ---
    ("C38U", "CAPITALAND INTEGRATED COMMERCIAL TRUST", "CICT", "REITs & Property Trusts"),
    ("A17U", "CAPITALAND ASCENDAS REIT", "CapitaLand Ascendas REIT", "REITs & Property Trusts"),
    ("HMN", "CAPITALAND ASCOTT TRUST", "CapitaLand Ascott Trust", "REITs & Property Trusts"),
    ("AU8U", "CAPITALAND CHINA TRUST", "CapitaLand China Trust", "REITs & Property Trusts"),
    ("CY6U", "CAPITALAND INDIA TRUST", "CapitaLand India Trust", "REITs & Property Trusts"),
    ("M44U", "MAPLETREE LOGISTICS TRUST", "Mapletree Logistics Trust", "REITs & Property Trusts"),
    ("ME8U", "MAPLETREE INDUSTRIAL TRUST", "Mapletree Industrial Trust", "REITs & Property Trusts"),
    ("N2IU", "MAPLETREE PAN ASIA COMMERCIAL TRUST", "Mapletree Pan Asia Commercial Trust", "REITs & Property Trusts"),
    ("BUOU", "FRASERS LOGISTICS & COMMERCIAL TRUST", "Frasers Logistics & Commercial Trust", "REITs & Property Trusts"),
    ("J69U", "FRASERS CENTREPOINT TRUST", "Frasers Centrepoint Trust", "REITs & Property Trusts"),
    ("J91U", "ESR-REIT", "ESR-REIT", "REITs & Property Trusts"),
    ("AJBU", "KEPPEL DC REIT", "Keppel DC REIT", "REITs & Property Trusts"),
    ("K71U", "KEPPEL REIT", "Keppel REIT", "REITs & Property Trusts"),
    ("CRPU", "SASSEUR REAL ESTATE INVESTMENT TRUST", "Sasseur REIT", "REITs & Property Trusts"),
    ("C2PU", "PARKWAYLIFE REIT", "Parkway Life REIT", "REITs & Property Trusts"),
    ("BTOU", "MANULIFE US REAL ESTATE INVESTMENT TRUST", "Manulife US REIT", "REITs & Property Trusts"),
    ("O5RU", "AIMS APAC REIT", "AIMS APAC REIT", "REITs & Property Trusts"),
    ("M1GU", "ALPHA INTEGRATED REAL ESTATE INVESTMENT TRUST", "Alpha Integrated REIT", "REITs & Property Trusts"),
    ("P40U", "STARHILL GLOBAL REAL ESTATE INVESTMENT TRUST", "Starhill Global REIT", "REITs & Property Trusts"),
    ("T82U", "SUNTEC REAL ESTATE INVESTMENT TRUST", "Suntec REIT", "REITs & Property Trusts"),
    ("TS0U", "OUE REAL ESTATE INVESTMENT TRUST", "OUE REIT", "REITs & Property Trusts"),
    ("J85", "CDL HOSPITALITY TRUSTS", "CDL Hospitality Trusts", "REITs & Property Trusts"),
    ("Q5T", "FAR EAST HOSPITALITY TRUST", "Far East Hospitality Trust", "REITs & Property Trusts"),
    ("OXMU", "PRIME US REIT", "Prime US REIT", "REITs & Property Trusts"),
    ("CMOU", "KORE US REIT", "KORE US REIT", "REITs & Property Trusts"),
    ("DHLU", "DAIWA HOUSE LOGISTICS TRUST", "Daiwa House Logistics Trust", "REITs & Property Trusts"),
    ("A7RU", "KEPPEL INFRASTRUCTURE TRUST", "Keppel Infrastructure Trust", "REITs & Property Trusts"),
    # --- Next 50 additions (per Mar 2026 monthly statistics PDF) ---
    ("DCRU", "DIGITAL CORE REIT", "Digital Core REIT", "REITs & Property Trusts"),
    ("JYEU", "LENDLEASE GLOBAL COMMERCIAL REIT", "Lendlease Global REIT", "REITs & Property Trusts"),
    # CENT placeholder: Centurion Accommodation REIT IPO'd late 2024/early 2025;
    # verify the actual SGX stock_code after the first scrape and update.
    ("8C8U", "CENTURION ACCOMMODATION REIT", "Centurion Accommodation REIT", "REITs & Property Trusts"),
    # NDC placeholder — verify after first scrape.
    ("NTDU", "NTT DC REIT", "NTT DC REIT", "REITs & Property Trusts"),
    
    # --- Real Estate Developers (~6) ---
    ("9CI", "CAPITALAND INVESTMENT LIMITED", "CapitaLand Investment", "Real Estate Developers"),
    ("C09", "CITY DEVELOPMENTS LIMITED", "City Developments", "Real Estate Developers"),
    ("U14", "UOL GROUP LIMITED", "UOL", "Real Estate Developers"),
    ("F17", "GUOCOLAND LIMITED", "GuocoLand", "Real Estate Developers"),
    ("H78", "HONGKONG LAND HOLDINGS LIMITED", "Hongkong Land", "Real Estate Developers"),
    ("Z25", "YANLORD LAND GROUP LIMITED", "Yanlord", "Real Estate Developers"),
    ("TQ5", "FRASERS PROPERTY LIMITED", "Frasers Property", "Real Estate Developers"),

    # --- Industrials & Engineering (~10) ---
    ("BN4", "KEPPEL LTD.", "Keppel", "Industrials & Engineering"),
    ("U96", "SEMBCORP INDUSTRIES LTD", "Sembcorp Industries", "Industrials & Engineering"),
    ("S63", "ST ENGINEERING LTD", "ST Engineering", "Industrials & Engineering"),
    ("BS6", "YANGZIJIANG SHIPBUILDING (HOLDINGS) LTD.", "Yangzijiang Shipbuilding", "Industrials & Engineering"),
    ("H22", "HONG LEONG ASIA LTD.", "Hong Leong Asia", "Industrials & Engineering"),
    ("F9D", "BOUSTEAD SINGAPORE LIMITED", "Boustead", "Industrials & Engineering"),
    ("BEC", "BRC ASIA LIMITED", "BRC Asia", "Industrials & Engineering"),
    ("P52", "PAN-UNITED CORPORATION LTD", "Pan-United", "Industrials & Engineering"),
    ("E3B", "WEE HUR HOLDINGS LTD.", "Wee Hur", "Industrials & Engineering"),

    # --- Transport & Logistics (~5) ---
    ("C6L", "SINGAPORE AIRLINES LIMITED", "SIA", "Transport & Logistics"),
    ("S58", "SATS LTD.", "SATS", "Transport & Logistics"),
    ("C52", "COMFORTDELGRO CORPORATION LIMITED", "ComfortDelGro", "Transport & Logistics"),
    ("S59", "SIA ENGINEERING COMPANY LIMITED", "SIA Engineering", "Transport & Logistics"),
    ("S08", "SINGAPORE POST LIMITED", "SingPost", "Transport & Logistics"),

    # --- Telco, Media & Connectivity (~4) ---
    ("Z74", "SINGAPORE TELECOMMUNICATIONS LIMITED", "Singtel", "Telco, Media & Connectivity"),
    ("CC3", "STARHUB LTD", "StarHub", "Telco, Media & Connectivity"),
    ("CJLU", "NETLINK NBN TRUST", "NetLink NBN Trust", "Telco, Media & Connectivity"),

    # --- Technology & Semicon (~8) ---
    ("V03", "VENTURE CORPORATION LIMITED", "Venture Corp", "Technology & Semicon"),
    ("AWX", "AEM HOLDINGS LTD", "AEM", "Technology & Semicon"),
    ("558", "UMS INTEGRATION LIMITED", "UMS Integration", "Technology & Semicon"),
    ("E28", "FRENCKEN GROUP LIMITED", "Frencken", "Technology & Semicon"),
    ("544", "CSE GLOBAL LTD", "CSE Global", "Technology & Semicon"),
    ("JLB", "GRAND VENTURE TECHNOLOGY LIMITED", "Grand Venture", "Technology & Semicon"),
    # UGAI placeholder — UltraGreen.ai is a recent IPO; verify SGX stock_code after first scrape.
    ("UGAI", "ULTRAGREEN.AI LTD", "UltraGreen.ai", "Technology & Semicon"),

    # --- Healthcare & Medtech (~6) ---
    ("BSL", "RAFFLES MEDICAL GROUP LTD", "Raffles Medical", "Healthcare & Medtech"),
    ("A50", "THOMSON MEDICAL GROUP LIMITED", "Thomson Medical", "Healthcare & Medtech"),
    ("Q0F", "IHH HEALTHCARE BERHAD", "IHH Healthcare", "Healthcare & Medtech"),
    ("AP4", "RIVERSTONE HOLDINGS LIMITED", "Riverstone", "Healthcare & Medtech"),
    ("505", "ASIAMEDIC LIMITED", "AsiaMedic", "Healthcare & Medtech"),

    # --- Consumer Goods & F&B (~8) ---
    ("F34", "WILMAR INTERNATIONAL LIMITED", "Wilmar", "Consumer Goods & F&B"),
    ("Y92", "THAI BEVERAGE PUBLIC COMPANY LIMITED", "ThaiBev", "Consumer Goods & F&B"),
    ("OV8", "SHENG SIONG GROUP LTD", "Sheng Siong", "Consumer Goods & F&B"),
    ("F03", "FOOD EMPIRE HOLDINGS LIMITED", "Food Empire", "Consumer Goods & F&B"),
    ("D01", "DFI RETAIL GROUP HOLDINGS LIMITED", "DFI Retail", "Consumer Goods & F&B"),
    ("G13", "GENTING SINGAPORE LIMITED", "Genting Singapore", "Consumer Goods & F&B"),
    ("VC2", "OLAM GROUP LIMITED", "Olam", "Consumer Goods & F&B"),
    ("E5H", "GOLDEN AGRI-RESOURCES LTD", "Golden Agri", "Consumer Goods & F&B"),
    ("EB5", "FIRST RESOURCES LIMITED", "First Resources", "Consumer Goods & F&B"),
    ("CH8", "CHINA SUNSINE CHEMICAL HOLDINGS LTD.", "China Sunsine", "Consumer Goods & F&B"),

    # --- Energy & Resources (~5) ---
    ("5E2", "SEATRIUM LIMITED", "Seatrium", "Energy & Resources"),
    ("G92", "CHINA AVIATION OIL (SINGAPORE) CORPORATION LTD", "China Aviation Oil", "Energy & Resources"),
    ("RE4", "GEO ENERGY RESOURCES LIMITED", "Geo Energy", "Energy & Resources"),
    ("5LY", "MARCO POLO MARINE LTD.", "Marco Polo Marine", "Energy & Resources"),

    # --- Conglomerates & Diversified (~4) ---
    ("J36", "JARDINE MATHESON HOLDINGS LIMITED", "Jardine Matheson", "Conglomerates & Diversified"),
    ("YF8", "YANGZIJIANG FINANCIAL HOLDING LTD.", "Yangzijiang Financial", "Conglomerates & Diversified"),
    # YZMD placeholder — recent spin-off from Yangzijiang Shipbuilding; verify SGX stock_code after first scrape.
    ("8YZ", "YANGZIJIANG MARITIME DEVELOPMENT LTD", "Yangzijiang Maritime", "Conglomerates & Diversified"),
    ("H02", "HAW PAR CORPORATION LIMITED", "Haw Par", "Conglomerates & Diversified"),

    # --- Specialty (Hospitality, Education, Other) (~4) ---
    ("OU8", "CENTURION CORPORATION LIMITED", "Centurion Corp", "Specialty"),
    ("OYY", "PROPNEX LIMITED", "Propnex", "Specialty"),
    # T6I best-guess for Valuemax (T13 turned out to be RH PetroGas);
    # verify the actual SGX stock_code after the first scrape.
    ("T6I", "VALUEMAX GROUP LIMITED", "Valuemax", "Specialty"),
    ("F99", "FRASER AND NEAVE, LIMITED", "Fraser & Neave", "Specialty"),
]
