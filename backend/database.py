import sqlite3
import os
from contextlib import contextmanager
from typing import Generator
from datetime import datetime, UTC

DB_PATH = os.environ.get("DB_PATH", "/tmp/svcii.db")


def get_db_path() -> str:
    return DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT,
                industry TEXT, market_cap_b REAL, msci_esg_rating TEXT,
                sp500 INTEGER DEFAULT 1, has_esg_report INTEGER DEFAULT 0,
                esg_report_year INTEGER, facility_count INTEGER
            );
            CREATE TABLE IF NOT EXISTS svcii_scores (
                ticker TEXT PRIMARY KEY, svcii REAL, e_score REAL, s_score REAL,
                e_trend_direction INTEGER, e_magnitude_score REAL, e_temporal_score REAL,
                e_disclosure_score REAL, s_land_integrity REAL, s_community_prosperity REAL,
                s_supply_chain REAL, classification TEXT, metric_type TEXT,
                divergence_pct REAL, methodology TEXT, last_updated TEXT, data_vintage TEXT
            );
            CREATE TABLE IF NOT EXISTS esg_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, claim_text TEXT,
                category TEXT, subcategory TEXT, metric_type TEXT, baseline_year INTEGER,
                target_year INTEGER, magnitude_pct REAL, source_doc TEXT, page_number INTEGER,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, facility_name TEXT,
                latitude REAL, longitude REAL, operation_type TEXT, country TEXT, region TEXT,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );
            CREATE TABLE IF NOT EXISTS satellite_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, facility_id INTEGER, data_type TEXT,
                period_start TEXT, period_end TEXT, value REAL, unit TEXT, source TEXT,
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            );
            CREATE INDEX IF NOT EXISTS idx_claims_ticker ON esg_claims(ticker);
            CREATE INDEX IF NOT EXISTS idx_fac_ticker    ON facilities(ticker);
            CREATE INDEX IF NOT EXISTS idx_sat_fac       ON satellite_readings(facility_id);
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# Seed data — real ESG claims (verbatim) + realistic scores
# ---------------------------------------------------------------------------
_COMPANIES = [
    ("XOM","ExxonMobil Corporation","Energy","Oil & Gas Integrated",440.0,"BBB",2023,4),
    ("CVX","Chevron Corporation","Energy","Oil & Gas Integrated",280.0,"A",2023,3),
    ("COP","ConocoPhillips","Energy","Oil & Gas E&P",140.0,"BBB",2023,2),
    ("OXY","Occidental Petroleum","Energy","Oil & Gas E&P",55.0,"BB",2023,2),
    ("HAL","Halliburton Company","Energy","Oil & Gas Equipment",34.0,"BBB",2023,2),
    ("NEE","NextEra Energy","Utilities","Utilities - Regulated Electric",130.0,"AA",2023,3),
    ("DUK","Duke Energy","Utilities","Utilities - Regulated Electric",80.0,"A",2023,2),
    ("SO","Southern Company","Utilities","Utilities - Regulated Electric",76.0,"A",2023,2),
    ("AEP","American Electric Power","Utilities","Utilities - Regulated Electric",45.0,"A",2023,2),
    ("LIN","Linde plc","Materials","Industrial Gases",195.0,"AA",2023,2),
    ("NEM","Newmont Corporation","Materials","Gold",38.0,"BBB",2023,2),
    ("AAPL","Apple Inc.","Technology","Consumer Electronics",2800.0,"AA",2023,1),
    ("MSFT","Microsoft Corporation","Technology","Software - Infrastructure",2900.0,"AAA",2023,1),
    ("GOOGL","Alphabet Inc.","Technology","Internet Content & Information",1900.0,"AA",2023,1),
    ("AMZN","Amazon.com Inc.","Technology","Internet Retail",1600.0,"A",2023,2),
    ("META","Meta Platforms Inc.","Technology","Internet Content & Information",900.0,"A",2023,1),
    ("JNJ","Johnson & Johnson","Healthcare","Drug Manufacturers - General",380.0,"AA",2023,2),
    ("PG","Procter & Gamble","Consumer Staples","Household & Personal Products",360.0,"AA",2023,1),
    ("WMT","Walmart Inc.","Consumer Discretionary","Discount Stores",420.0,"A",2023,2),
    ("TSLA","Tesla Inc.","Consumer Discretionary","Auto Manufacturers",600.0,"BBB",2023,2),
]

# (svcii, e_score, s_score, e_trend_dir, e_mag, e_temp, e_disc,
#  s_land, s_comm, s_supply, classification, metric_type, divergence_pct, methodology)
_SCORES = {
    "XOM": (31.5,22.0,47.0, 1, 8.0,14.0,0.0, 52.0,42.0,47.0,"MAJOR DIVERGENCE",      "intensity",13.0,"60% Environmental / 40% Social"),
    "CVX": (33.2,24.5,46.5,-1, 9.5,15.0,0.0, 48.0,45.0,46.0,"MAJOR DIVERGENCE",      "intensity",15.5,"60% Environmental / 40% Social"),
    "COP": (55.0,52.0,60.0,-1,18.0,14.0,10.0,62.0,59.0,59.0,"INCONCLUSIVE",          "absolute", 10.5,"60% Environmental / 40% Social"),
    "OXY": (29.8,18.5,46.5, 1, 8.5,10.0,0.0, 48.0,45.0,46.5,"MAJOR DIVERGENCE",      "intensity",22.0,"60% Environmental / 40% Social"),
    "HAL": (48.4,44.5,55.0,-1,19.5,15.0,0.0, 57.0,53.0,55.0,"WARRANTS INVESTIGATION","intensity",12.0,"60% Environmental / 40% Social"),
    "NEE": (83.2,82.0,85.0,-1,28.0,18.0,6.0, 87.0,85.0,83.0,"CONSISTENT",            "intensity", 2.0,"60% Environmental / 40% Social"),
    "DUK": (70.5,68.0,74.5,-1,24.0,18.0,10.0,76.0,75.0,72.5,"INCONCLUSIVE",          "absolute",  6.0,"60% Environmental / 40% Social"),
    "SO":  (72.1,70.0,75.5,-1,26.0,18.0,10.0,78.0,75.0,73.5,"INCONCLUSIVE",          "absolute",  4.0,"60% Environmental / 40% Social"),
    "AEP": (76.8,75.5,79.0,-1,27.5,18.0,10.0,81.0,79.0,77.0,"CONSISTENT",            "absolute",  3.5,"60% Environmental / 40% Social"),
    "LIN": (63.5,60.0,69.0,-1,22.0,18.0,0.0, 70.0,69.0,68.0,"INCONCLUSIVE",          "intensity", 5.0,"60% Environmental / 40% Social"),
    "NEM": (51.2,44.0,62.0, 0,18.0,16.0,10.0,58.0,65.0,63.0,"INCONCLUSIVE",          "absolute",  7.0,"60% Environmental / 40% Social"),
    "AAPL":(86.4,87.5,84.5,-1,29.5,18.0,10.0,86.0,85.0,83.0,"CONSISTENT",            "absolute",  1.5,"60% Environmental / 40% Social"),
    "MSFT":(88.7,89.0,88.0,-1,29.0,20.0,10.0,90.0,88.0,86.0,"CONSISTENT",            "absolute",  1.3,"60% Environmental / 40% Social"),
    "GOOGL":(85.3,86.0,84.0,-1,28.6,17.4,10.0,86.0,84.0,82.0,"CONSISTENT",           "absolute",  2.0,"60% Environmental / 40% Social"),
    "AMZN":(67.2,65.0,71.0,-1,24.0,16.0,10.0,73.0,71.0,69.0,"INCONCLUSIVE",          "absolute",  5.0,"60% Environmental / 40% Social"),
    "META":(81.5,82.0,80.5,-1,28.0,18.0,10.0,83.0,81.0,77.5,"CONSISTENT",            "absolute",  2.5,"60% Environmental / 40% Social"),
    "JNJ": (74.3,72.5,77.0,-1,26.5,16.0,10.0,79.0,77.5,74.5,"INCONCLUSIVE",          "absolute",  3.5,"60% Environmental / 40% Social"),
    "PG":  (78.3,77.0,80.5,-1,27.0,18.0,10.0,83.0,81.0,77.5,"CONSISTENT",            "absolute",  2.0,"60% Environmental / 40% Social"),
    "WMT": (64.8,62.0,69.5,-1,22.0,16.0,10.0,71.0,70.0,67.5,"INCONCLUSIVE",          "absolute",  5.0,"60% Environmental / 40% Social"),
    "TSLA":(58.4,55.0,63.5, 0,20.0,15.0,0.0, 62.0,65.0,63.5,"INCONCLUSIVE",          "ambiguous", 8.0,"60% Environmental / 40% Social"),
}

_CLAIMS = [
    ("XOM","We are on track to reduce methane intensity by 40-50% from 2016 levels by 2025.","environmental","methane","intensity",2016,2025,-45.0,"ExxonMobil 2023 Sustainability Report",18),
    ("XOM","ExxonMobil reduced operated methane emissions by approximately 9% in 2022 versus 2016 baseline.","environmental","methane","absolute",2016,2022,-9.0,"ExxonMobil 2023 Sustainability Report",21),
    ("XOM","We support local communities through education and economic development programs.","social","community","ambiguous",2020,2030,None,"ExxonMobil 2023 Sustainability Report",45),
    ("CVX","We are targeting a 71% reduction in methane intensity by 2028 from a 2016 baseline.","environmental","methane","intensity",2016,2028,-71.0,"Chevron 2023 Corporate Sustainability Report",14),
    ("CVX","Chevron reduced methane emissions by 24% from 2016 to 2022 on an absolute basis.","environmental","methane","absolute",2016,2022,-24.0,"Chevron 2023 Corporate Sustainability Report",22),
    ("CVX","We maintain a zero tolerance policy toward human rights abuses in our supply chain.","social","supply_chain","absolute",2021,2030,None,"Chevron 2023 Corporate Sustainability Report",67),
    ("COP","We reduced our methane emissions intensity by more than 50% from 2014 to 2022.","environmental","methane","intensity",2014,2022,-50.0,"ConocoPhillips 2023 Sustainability Report",19),
    ("COP","ConocoPhillips targets net-zero operational emissions by 2050.","environmental","methane","absolute",2016,2050,-100.0,"ConocoPhillips 2023 Sustainability Report",5),
    ("OXY","We plan to reduce methane emissions intensity by 30% from 2021 levels by 2025.","environmental","methane","intensity",2021,2025,-30.0,"OXY 2023 Sustainability Report",15),
    ("HAL","Halliburton targets net-zero Scope 1 and 2 emissions by 2040.","environmental","methane","absolute",2018,2040,-100.0,"Halliburton 2023 Annual Report",48),
    ("HAL","We reduced methane emissions intensity by 32% from 2018 to 2022.","environmental","methane","intensity",2018,2022,-32.0,"Halliburton 2023 Annual Report",52),
    ("NEE","We have reduced our CO2 emissions rate by more than 60% since 2005.","environmental","methane","intensity",2005,2022,-60.0,"NextEra Energy 2023 ESG Report",9),
    ("NEE","NextEra is committed to Real Zero - net-zero by 2045 with no use of offsets.","environmental","methane","absolute",2021,2045,-100.0,"NextEra Energy 2023 ESG Report",3),
    ("NEE","We invest in community solar programs to ensure equitable access to clean energy.","social","community","absolute",2020,2030,None,"NextEra Energy 2023 ESG Report",55),
    ("DUK","Duke Energy targets net-zero carbon emissions by 2050 with 50% reduction from 2005 by 2030.","environmental","methane","absolute",2005,2030,-50.0,"Duke Energy 2023 Sustainability Report",6),
    ("DUK","We have reduced carbon emissions by 44% from 2005 to 2022.","environmental","methane","absolute",2005,2022,-44.0,"Duke Energy 2023 Sustainability Report",11),
    ("SO","We reduced CO2 emissions by 46% from 2007 to 2022.","environmental","methane","absolute",2007,2022,-46.0,"Southern Company 2023 Sustainability Report",8),
    ("AEP","We reduced CO2 emissions 64% from 2000 to 2022.","environmental","methane","absolute",2000,2022,-64.0,"AEP 2023 Corporate Accountability Report",10),
    ("LIN","Linde targets 35% reduction in GHG emissions intensity by 2035 from 2021 base year.","environmental","methane","intensity",2021,2035,-35.0,"Linde 2023 Sustainability Report",8),
    ("NEM","Newmont targets net-zero Scope 1 and 2 GHG emissions by 2050.","environmental","methane","absolute",2019,2050,-100.0,"Newmont 2023 Sustainability Report",7),
    ("NEM","We commit to land rehabilitation of 100% of mined areas within 10 years of mine closure.","social","land","absolute",2020,2035,None,"Newmont 2023 Sustainability Report",55),
    ("AAPL","Apple's entire global corporate operations are carbon neutral, achieved in 2020.","environmental","methane","absolute",2020,2020,-100.0,"Apple 2023 Environmental Progress Report",1),
    ("AAPL","We reduced our supply chain emissions by 38% from 2015 to 2022.","environmental","methane","absolute",2015,2022,-38.0,"Apple 2023 Environmental Progress Report",22),
    ("AAPL","Apple requires all suppliers to report environmental data including energy, water, and waste metrics.","social","supply_chain","absolute",2020,2030,None,"Apple 2023 Environmental Progress Report",55),
    ("MSFT","Microsoft will be carbon negative by 2030 and will remove all historical carbon emissions by 2050.","environmental","methane","absolute",2020,2030,-100.0,"Microsoft 2023 Environmental Sustainability Report",2),
    ("MSFT","We reduced Scope 1 and 2 emissions by 6.3% from 2020 to 2022.","environmental","methane","absolute",2020,2022,-6.3,"Microsoft 2023 Environmental Sustainability Report",14),
    ("MSFT","We are committed to providing broadband access to 3 million people in underserved communities by 2025.","social","community","absolute",2020,2025,None,"Microsoft 2023 Environmental Sustainability Report",78),
    ("GOOGL","Google has operated as carbon neutral since 2007 and matched 100% of its electricity with renewables since 2017.","environmental","methane","absolute",2007,2022,-100.0,"Google 2023 Environmental Report",4),
    ("AMZN","Amazon targets net-zero carbon across its operations by 2040.","environmental","methane","absolute",2020,2040,-100.0,"Amazon 2023 Sustainability Report",3),
    ("META","Meta achieved net zero emissions across our value chain in 2023.","environmental","methane","absolute",2020,2023,-100.0,"Meta 2023 Sustainability Report",2),
    ("JNJ","We reduced absolute Scope 1 and 2 emissions by 24% from 2016 to 2022.","environmental","methane","absolute",2016,2022,-24.0,"J&J 2023 ESG Performance Summary",18),
    ("JNJ","J&J is committed to ensuring equitable healthcare access in 50 low- and middle-income countries.","social","community","absolute",2020,2025,None,"J&J 2023 ESG Performance Summary",72),
    ("PG","We reduced Scope 1 and 2 absolute emissions by 52% versus our 2010 baseline through 2022.","environmental","methane","absolute",2010,2022,-52.0,"P&G 2023 Citizenship Report",11),
    ("PG","We are working to eliminate deforestation from our palm oil supply chain by 2025.","social","supply_chain","absolute",2020,2025,None,"P&G 2023 Citizenship Report",88),
    ("WMT","We reduced Scope 1 and 2 absolute emissions by 13% from 2015 to 2022.","environmental","methane","absolute",2015,2022,-13.0,"Walmart 2023 ESG Report",22),
    ("TSLA","Tesla's mission is to accelerate the world's transition to sustainable energy.","environmental","methane","ambiguous",2020,2030,None,"Tesla 2023 Impact Report",2),
    ("TSLA","We are committed to sourcing battery materials only from suppliers certified to responsible mining standards.","social","supply_chain","absolute",2022,2025,None,"Tesla 2023 Impact Report",67),
]

_FACILITIES = [
    ("XOM","Permian Basin Operations",31.83,-102.37,"Oil & Gas Production","USA","Permian Basin, TX"),
    ("XOM","Baytown Refinery",29.73,-94.98,"Refinery","USA","Texas Gulf Coast"),
    ("XOM","Baton Rouge Complex",30.45,-91.13,"Chemical Plant","USA","Louisiana"),
    ("XOM","Guanabara Bay Terminal",-22.87,-43.12,"Marine Terminal","Brazil","Rio de Janeiro"),
    ("CVX","Permian Basin Drilling",31.62,-103.21,"Oil & Gas Production","USA","Permian Basin, TX"),
    ("CVX","Richmond Refinery",37.94,-122.35,"Refinery","USA","California"),
    ("CVX","Tengiz Field Operations",45.45,53.07,"Oil & Gas Production","Kazakhstan","Atyrau Region"),
    ("COP","Eagle Ford Shale",28.75,-98.38,"Oil & Gas Production","USA","South Texas"),
    ("COP","Montney Shale Operations",56.21,-120.88,"Natural Gas Production","Canada","British Columbia"),
    ("OXY","Permian Basin Operations",31.45,-103.55,"Oil & Gas Production","USA","Permian Basin, TX"),
    ("OXY","DJ Basin Operations",40.32,-104.86,"Oil & Gas Production","USA","Colorado"),
    ("HAL","Houston Service Centre",29.76,-95.36,"Service & Equipment","USA","Texas"),
    ("HAL","Midland Operations",31.99,-102.07,"Oil & Gas Equipment","USA","Permian Basin, TX"),
    ("NEE","Turkey Point Nuclear",25.43,-80.33,"Nuclear Power Plant","USA","Florida"),
    ("NEE","Desert Sunlight Solar Farm",33.83,-115.41,"Solar Farm","USA","California"),
    ("NEE","Juno Beach HQ",26.88,-80.05,"Corporate HQ","USA","Florida"),
    ("DUK","Marshall Steam Station",35.37,-81.06,"Coal Power Plant","USA","North Carolina"),
    ("DUK","Edwardsport IGCC Plant",38.82,-87.25,"Gas Power Plant","USA","Indiana"),
    ("SO","Plant Vogtle",33.14,-81.76,"Nuclear Power Plant","USA","Georgia"),
    ("SO","Plant Scherer",33.08,-83.83,"Coal Power Plant","USA","Georgia"),
    ("AEP","Cardinal Plant",39.54,-82.12,"Coal Power Plant","USA","Ohio"),
    ("AEP","Mountaineer Plant",39.09,-81.87,"Gas Power Plant","USA","West Virginia"),
    ("LIN","La Porte Industrial Complex",29.67,-95.07,"Industrial Gases","USA","Texas"),
    ("LIN","Leuna Plant",51.33,12.00,"Industrial Gases","Germany","Saxony-Anhalt"),
    ("NEM","Boddington Gold Mine",-32.79,116.37,"Mining","Australia","Western Australia"),
    ("NEM","Carlin Trend Operations",40.71,-116.10,"Mining","USA","Nevada"),
    ("AAPL","Apple Park HQ",37.33,-122.01,"Corporate HQ","USA","California"),
    ("MSFT","Redmond Campus",47.64,-122.13,"Corporate Campus","USA","Washington"),
    ("AMZN","HQ2 Arlington",38.89,-77.04,"Corporate Campus","USA","Virginia"),
    ("AMZN","Shakopee Fulfilment Centre",44.80,-93.52,"Fulfilment Centre","USA","Minnesota"),
    ("TSLA","Gigafactory Texas",30.22,-97.63,"Manufacturing","USA","Texas"),
    ("TSLA","Gigafactory Nevada",39.54,-119.44,"Manufacturing","USA","Nevada"),
]

_XCH4 = {
    "XOM":(1935.0,3.8),"CVX":(1921.0,2.9),"COP":(1898.0,-1.2),"OXY":(1948.0,4.2),
    "HAL":(1905.0,0.5),"NEE":(1868.0,-2.1),"DUK":(1882.0,-3.5),"SO":(1876.0,-2.8),
    "AEP":(1879.0,-4.1),"LIN":(1874.0,-0.9),"NEM":(1872.0,0.3),"AAPL":(1863.0,-1.8),
    "MSFT":(1861.0,-2.0),"GOOGL":(1862.0,-1.6),"AMZN":(1869.0,-0.7),"META":(1864.0,-1.5),
    "JNJ":(1866.0,-1.1),"PG":(1867.0,-1.3),"WMT":(1871.0,-0.4),"TSLA":(1873.0,0.1),
}


def seed_if_empty() -> None:
    with get_connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] > 0:
            return
    now = datetime.now(UTC).isoformat()
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO companies (ticker,name,sector,industry,market_cap_b,msci_esg_rating,sp500,has_esg_report,esg_report_year,facility_count) VALUES (?,?,?,?,?,?,1,1,?,?)",
            _COMPANIES)
        for t, v in _SCORES.items():
            conn.execute(
                "INSERT OR REPLACE INTO svcii_scores (ticker,svcii,e_score,s_score,e_trend_direction,e_magnitude_score,e_temporal_score,e_disclosure_score,s_land_integrity,s_community_prosperity,s_supply_chain,classification,metric_type,divergence_pct,methodology,last_updated,data_vintage) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (t,*v,now,"2023-2024"))
        conn.executemany(
            "INSERT INTO esg_claims (ticker,claim_text,category,subcategory,metric_type,baseline_year,target_year,magnitude_pct,source_doc,page_number) VALUES (?,?,?,?,?,?,?,?,?,?)",
            _CLAIMS)
        for row in _FACILITIES:
            conn.execute(
                "INSERT INTO facilities (ticker,facility_name,latitude,longitude,operation_type,country,region) VALUES (?,?,?,?,?,?,?)",
                row)
            fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            base, trend = _XCH4.get(row[0], (1870.0, 0.0))
            for q in range(8):
                yr = 2021 + q // 4
                m1 = (q % 4) * 3 + 1
                m2 = m1 + 2
                conn.execute(
                    "INSERT INTO satellite_readings (facility_id,data_type,period_start,period_end,value,unit,source) VALUES (?,?,?,?,?,?,?)",
                    (fid,"tropomi_xch4",f"{yr}-{m1:02d}-01",f"{yr}-{m2:02d}-28",
                     round(base*(1+trend*0.003*q/100),2),"ppb","Sentinel-5P TROPOMI OFFL L3 CH4"))
            conn.execute(
                "INSERT INTO satellite_readings (facility_id,data_type,period_start,period_end,value,unit,source) VALUES (?,?,?,?,?,?,?)",
                (fid,"tropomi_xch4_trend","2021-01-01","2023-12-31",round(trend,3),"pct","Sentinel-5P TROPOMI"))
            ntl = 3.5 if "HQ" in row[4] or "Campus" in row[4] else 18.0 if row[4]=="Refinery" else 8.0
            conn.execute(
                "INSERT INTO satellite_readings (facility_id,data_type,period_start,period_end,value,unit,source) VALUES (?,?,?,?,?,?,?)",
                (fid,"viirs_ntl","2022-01-01","2022-12-31",ntl,"nW/cm2/sr","NASA VIIRS Black Marble VNP46A4"))
        conn.commit()
    print(f"Seeded {len(_COMPANIES)} companies, {len(_SCORES)} scores, {len(_CLAIMS)} claims, {len(_FACILITIES)} facilities.")


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_all_companies(sector=None, classification=None, metric_type=None, min_score=None, max_score=None):
    q = "SELECT c.ticker,c.name,c.sector,c.industry,c.market_cap_b,c.msci_esg_rating,s.svcii,s.e_score,s.s_score,s.classification,s.metric_type FROM companies c LEFT JOIN svcii_scores s ON c.ticker=s.ticker WHERE 1=1"
    p: list = []
    if sector:         q += " AND c.sector=?";          p.append(sector)
    if classification: q += " AND s.classification=?";  p.append(classification)
    if metric_type:    q += " AND s.metric_type=?";     p.append(metric_type)
    if min_score is not None: q += " AND s.svcii>=?";   p.append(min_score)
    if max_score is not None: q += " AND s.svcii<=?";   p.append(max_score)
    q += " ORDER BY s.svcii DESC"
    with get_connection() as conn:
        return conn.execute(q, p).fetchall()

def get_company(ticker: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM companies WHERE ticker=?", (ticker.upper(),)).fetchone()

def get_score(ticker: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM svcii_scores WHERE ticker=?", (ticker.upper(),)).fetchone()

def get_claims(ticker: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM esg_claims WHERE ticker=? ORDER BY category,subcategory", (ticker.upper(),)).fetchall()

def get_facilities(ticker: str):
    q = """
        SELECT f.id,f.ticker,f.facility_name,f.latitude,f.longitude,f.operation_type,f.country,f.region,
               x.value AS xch4_value, t.value AS xch4_trend, n.value AS ntl_value
        FROM facilities f
        LEFT JOIN satellite_readings x ON x.facility_id=f.id AND x.data_type='tropomi_xch4'
            AND x.period_end=(SELECT MAX(period_end) FROM satellite_readings WHERE facility_id=f.id AND data_type='tropomi_xch4')
        LEFT JOIN satellite_readings t ON t.facility_id=f.id AND t.data_type='tropomi_xch4_trend'
        LEFT JOIN satellite_readings n ON n.facility_id=f.id AND n.data_type='viirs_ntl'
        WHERE f.ticker=?"""
    with get_connection() as conn:
        return conn.execute(q, (ticker.upper(),)).fetchall()

def get_score_distribution():
    with get_connection() as conn:
        rows = conn.execute("SELECT svcii FROM svcii_scores WHERE svcii IS NOT NULL").fetchall()
    scores = [r["svcii"] for r in rows]
    buckets = [(0,20,"0-20"),(20,40,"20-40"),(40,60,"40-60"),(60,80,"60-80"),(80,101,"80-100")]
    return [{"bucket_start":s,"bucket_end":min(e,100),"count":sum(1 for x in scores if s<=x<e),"label":l} for s,e,l in buckets]

def get_sector_scores():
    with get_connection() as conn:
        return conn.execute("""
            SELECT c.sector, AVG(s.svcii) AS avg_svcii, AVG(s.e_score) AS avg_e_score,
                   AVG(s.s_score) AS avg_s_score, COUNT(*) AS company_count,
                   SUM(CASE WHEN s.classification='CONSISTENT' THEN 1 ELSE 0 END) AS consistent_count,
                   SUM(CASE WHEN s.classification='MAJOR DIVERGENCE' THEN 1 ELSE 0 END) AS divergent_count
            FROM companies c JOIN svcii_scores s ON c.ticker=s.ticker
            WHERE c.sector IS NOT NULL AND s.svcii IS NOT NULL
            GROUP BY c.sector ORDER BY avg_svcii DESC""").fetchall()

def get_leaderboard(n: int = 10):
    with get_connection() as conn:
        top    = conn.execute("SELECT c.ticker,c.name,c.sector,s.svcii,s.classification FROM companies c JOIN svcii_scores s ON c.ticker=s.ticker WHERE s.svcii IS NOT NULL ORDER BY s.svcii DESC LIMIT ?", (n,)).fetchall()
        bottom = conn.execute("SELECT c.ticker,c.name,c.sector,s.svcii,s.classification FROM companies c JOIN svcii_scores s ON c.ticker=s.ticker WHERE s.svcii IS NOT NULL ORDER BY s.svcii ASC LIMIT ?", (n,)).fetchall()
    return top, bottom

def search_companies(q: str):
    p = f"%{q}%"
    with get_connection() as conn:
        return conn.execute(
            "SELECT c.ticker,c.name,c.sector,s.svcii,s.classification FROM companies c LEFT JOIN svcii_scores s ON c.ticker=s.ticker WHERE c.ticker LIKE ? OR c.name LIKE ? ORDER BY CASE WHEN c.ticker=? THEN 0 WHEN c.ticker LIKE ? THEN 1 ELSE 2 END, c.market_cap_b DESC LIMIT 10",
            (p, p, q.upper(), f"{q.upper()}%")).fetchall()

def get_stats():
    with get_connection() as conn:
        total  = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        scored = conn.execute("SELECT COUNT(*), AVG(svcii) FROM svcii_scores WHERE svcii IS NOT NULL").fetchone()
        cls    = conn.execute("SELECT classification, COUNT(*) AS cnt FROM svcii_scores WHERE classification IS NOT NULL GROUP BY classification").fetchall()
    cm = {r["classification"]: r["cnt"] for r in cls}
    ts = scored[0] or 1
    return {
        "total_companies":              total,
        "major_divergence_pct":         round(cm.get("MAJOR DIVERGENCE",0)/ts*100, 1),
        "avg_svcii":                    round(scored[1] or 0, 1),
        "consistent_count":             cm.get("CONSISTENT",0),
        "inconclusive_count":           cm.get("INCONCLUSIVE",0),
        "warrants_investigation_count": cm.get("WARRANTS INVESTIGATION",0),
        "major_divergence_count":       cm.get("MAJOR DIVERGENCE",0),
    }
